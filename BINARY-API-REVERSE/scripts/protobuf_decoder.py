#!/usr/bin/env python3
"""
protobuf_decoder.py

Pure Python recursive Protocol Buffers wire-format decoder and schema reconstructor.
Operates WITHOUT requiring .proto files or the google.protobuf library.

Features:
  - Wire Types supported:
      0: Varint (int32, int64, uint32, uint64, sint32, sint64, bool, enum)
      1: 64-bit (fixed64, sfixed64, double)
      2: Length-delimited (string, submessage, packed repeated, bytes)
      5: 32-bit (fixed32, sfixed32, float)
  - Recursive submessage heuristic detection
  - Heuristic detection for UTF-8 strings vs embedded messages vs raw bytes
  - Automatic synthetic .proto file generation (syntax = "proto3")
  - Inputs accepted: raw binary file, hex string, or base64 string
  - Outputs: clean structured JSON and reconstructed .proto definitions

Conforms to PROJECT.md Interface Contracts.
"""

import sys
import os
import struct
import base64
import json
import argparse
from typing import Dict, List, Any, Tuple, Optional, Union


# Wire type constants
WIRE_VARINT = 0
WIRE_64BIT = 1
WIRE_LENGTH_DELIMITED = 2
WIRE_START_GROUP = 3  # Deprecated
WIRE_END_GROUP = 4    # Deprecated
WIRE_32BIT = 5


class ProtobufDecodeError(Exception):
    """Raised when wire parsing fails."""
    pass


def decode_varint(buffer: bytes, offset: int) -> Tuple[int, int]:
    """
    Decodes a varint from buffer starting at offset.
    Returns (value, new_offset).
    """
    value = 0
    shift = 0
    buf_len = len(buffer)

    while offset < buf_len:
        b = buffer[offset]
        offset += 1
        value |= (b & 0x7F) << shift
        if not (b & 0x80):
            return value, offset
        shift += 7
        if shift > 70:
            raise ProtobufDecodeError("Varint exceeds 64-bit / 10 bytes")

    raise ProtobufDecodeError("Unexpected end of buffer while reading varint")


def zigzag_decode(n: int) -> int:
    """Decodes a zigzag-encoded integer (sint32/sint64)."""
    return (n >> 1) ^ (-(n & 1))


def is_printable_utf8(data: bytes) -> bool:
    """Returns True if bytes represent a valid, predominantly printable UTF-8 string."""
    try:
        text = data.decode("utf-8")
        if not text:
            return False
        # Check printable ratio
        printable_count = sum(1 for c in text if c.isprintable() or c in ('\n', '\r', '\t'))
        return (printable_count / len(text)) >= 0.95
    except UnicodeDecodeError:
        return False


def try_parse_submessage(data: bytes, depth: int = 0) -> Optional[List[Dict[str, Any]]]:
    """
    Attempts to parse data as an embedded submessage.
    Returns parsed fields list if successful, or None if invalid.
    """
    if len(data) == 0 or depth > 20:
        return None

    try:
        fields = parse_protobuf_stream(data, depth=depth + 1)
        # If we got at least 1 valid field and no parse errors occurred
        if fields:
            return fields
    except Exception:
        pass

    return None


def parse_protobuf_stream(buffer: bytes, depth: int = 0) -> List[Dict[str, Any]]:
    """
    Parses a contiguous binary protobuf stream into structured field objects.
    """
    fields: List[Dict[str, Any]] = []
    offset = 0
    buf_len = len(buffer)

    while offset < buf_len:
        # Read tag
        tag, offset = decode_varint(buffer, offset)
        wire_type = tag & 0x07
        field_num = tag >> 3

        if field_num == 0 or field_num > 536870911:
            raise ProtobufDecodeError(f"Invalid field number: {field_num}")

        field_info: Dict[str, Any] = {
            "field_number": field_num,
            "wire_type": wire_type,
            "wire_type_name": {
                WIRE_VARINT: "varint",
                WIRE_64BIT: "64bit",
                WIRE_LENGTH_DELIMITED: "length_delimited",
                WIRE_32BIT: "32bit"
            }.get(wire_type, f"unknown_{wire_type}")
        }

        if wire_type == WIRE_VARINT:
            val, offset = decode_varint(buffer, offset)
            field_info["value"] = val
            field_info["sint_value"] = zigzag_decode(val)
            if val in (0, 1):
                field_info["bool_value"] = bool(val)
            field_info["inferred_type"] = "int64"

        elif wire_type == WIRE_64BIT:
            if offset + 8 > buf_len:
                raise ProtobufDecodeError("Truncated 64-bit field")
            raw_bytes = buffer[offset:offset + 8]
            offset += 8
            u64 = struct.unpack("<Q", raw_bytes)[0]
            i64 = struct.unpack("<q", raw_bytes)[0]
            f64 = struct.unpack("<d", raw_bytes)[0]
            field_info["raw_hex"] = raw_bytes.hex()
            field_info["uint64_value"] = u64
            field_info["int64_value"] = i64
            # Keep double if valid float
            if not (f64 != f64):  # not NaN
                field_info["double_value"] = round(f64, 6)
            field_info["value"] = f64 if abs(f64) < 1e12 and f64 != 0 else u64
            field_info["inferred_type"] = "double" if field_info.get("double_value") is not None else "fixed64"

        elif wire_type == WIRE_32BIT:
            if offset + 4 > buf_len:
                raise ProtobufDecodeError("Truncated 32-bit field")
            raw_bytes = buffer[offset:offset + 4]
            offset += 4
            u32 = struct.unpack("<I", raw_bytes)[0]
            i32 = struct.unpack("<i", raw_bytes)[0]
            f32 = struct.unpack("<f", raw_bytes)[0]
            field_info["raw_hex"] = raw_bytes.hex()
            field_info["uint32_value"] = u32
            field_info["int32_value"] = i32
            if not (f32 != f32):  # not NaN
                field_info["float_value"] = round(f32, 6)
            field_info["value"] = f32 if abs(f32) < 1e8 and f32 != 0 else u32
            field_info["inferred_type"] = "float" if field_info.get("float_value") is not None else "fixed32"

        elif wire_type == WIRE_LENGTH_DELIMITED:
            length, offset = decode_varint(buffer, offset)
            if length < 0 or offset + length > buf_len:
                raise ProtobufDecodeError(f"Invalid length {length} for length-delimited field {field_num}")

            payload = buffer[offset:offset + length]
            offset += length
            field_info["length"] = length

            # Heuristic decision tree:
            # 1. Try recursive submessage parsing
            # 2. Check if clean UTF-8 string
            # 3. Fallback to bytes / hex
            sub_fields = None
            # Only try submessage if payload is non-trivial and doesn't look like short plain text
            is_utf8 = is_printable_utf8(payload)

            if len(payload) > 1 and not (is_utf8 and len(payload) < 8 and payload.isalpha()):
                sub_fields = try_parse_submessage(payload, depth)

            if sub_fields is not None:
                field_info["inferred_type"] = "message"
                field_info["value"] = sub_fields
            elif is_utf8:
                field_info["inferred_type"] = "string"
                field_info["value"] = payload.decode("utf-8")
            else:
                field_info["inferred_type"] = "bytes"
                field_info["value"] = payload.hex()
                field_info["raw_base64"] = base64.b64encode(payload).decode("ascii")

        else:
            raise ProtobufDecodeError(f"Unsupported or invalid wire type: {wire_type} at offset {offset}")

        fields.append(field_info)

    return fields


def build_nested_dict(fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Transforms the linear list of parsed fields into a nested dict matching PROJECT.md:
    {"fields": {"field_number": {"wire_type": int, "value": any}}}
    """
    out_fields: Dict[str, Any] = {}

    for f in fields:
        f_num_str = str(f["field_number"])
        val = f["value"]

        if f["inferred_type"] == "message" and isinstance(val, list):
            val = build_nested_dict(val)

        # Handle repeated fields
        if f_num_str in out_fields:
            existing = out_fields[f_num_str]
            if not isinstance(existing["value"], list):
                existing["value"] = [existing["value"]]
            existing["value"].append(val)
        else:
            out_fields[f_num_str] = {
                "wire_type": f["wire_type"],
                "inferred_type": f["inferred_type"],
                "value": val
            }

    return {"fields": out_fields}


def generate_synthetic_proto(fields: List[Dict[str, Any]], message_name: str = "ReconstructedMessage") -> Tuple[str, List[str]]:
    """
    Analyzes parsed field hierarchy and generates synthetic .proto (proto3) schema definition.
    """
    lines = []
    lines.append(f"message {message_name} {{")

    sub_definitions = []
    seen_fields = set()

    for f in fields:
        f_num = f["field_number"]
        if f_num in seen_fields:
            continue
        seen_fields.add(f_num)

        inf_type = f.get("inferred_type", "bytes")
        val = f.get("value")

        if inf_type == "message" and isinstance(val, list):
            sub_msg_name = f"SubMessage_{f_num}"
            sub_proto_code, nested_subs = generate_synthetic_proto(val, sub_msg_name)
            sub_definitions.append(sub_proto_code)
            sub_definitions.extend(nested_subs)
            lines.append(f"    {sub_msg_name} field_{f_num} = {f_num};")
        elif inf_type == "string":
            lines.append(f"    string field_{f_num} = {f_num};")
        elif inf_type == "int64":
            lines.append(f"    int64 field_{f_num} = {f_num};")
        elif inf_type == "double":
            lines.append(f"    double field_{f_num} = {f_num};")
        elif inf_type == "float":
            lines.append(f"    float field_{f_num} = {f_num};")
        elif inf_type == "fixed64":
            lines.append(f"    uint64 field_{f_num} = {f_num};")
        elif inf_type == "fixed32":
            lines.append(f"    uint32 field_{f_num} = {f_num};")
        elif inf_type == "bool":
            lines.append(f"    bool field_{f_num} = {f_num};")
        else:
            lines.append(f"    bytes field_{f_num} = {f_num};")

    lines.append("}\n")
    return "\n".join(lines), sub_definitions


def format_proto_file(root_code: str, sub_codes: List[str]) -> str:
    """Combines root message and submessages into a complete .proto file."""
    header = [
        'syntax = "proto3";',
        '',
        'package reconstructed;',
        '',
        '// Automatically reconstructed by protobuf_decoder.py',
        '// Field types are inferred from wire format representation.',
        ''
    ]
    all_codes = [root_code] + sub_codes
    return "\n".join(header + all_codes)


def main():
    parser = argparse.ArgumentParser(
        description="protobuf_decoder - Pure Python Wire-Format Protobuf Decoder & Proto Schema Generator."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input binary file path, hex string, or base64 string."
    )
    parser.add_argument(
        "--hex",
        action="store_true",
        help="Treat input argument as a raw hexadecimal string."
    )
    parser.add_argument(
        "--base64", "-b",
        action="store_true",
        help="Treat input argument as a base64 encoded string."
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path (default: stdout)."
    )
    parser.add_argument(
        "--export-proto",
        help="File path to save the reconstructed synthetic .proto schema."
    )
    parser.add_argument(
        "--message-name",
        default="ReconstructedMessage",
        help="Name of the root message for synthetic .proto (default: ReconstructedMessage)."
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty-print JSON output."
    )

    args = parser.parse_args()

    # Load raw bytes
    raw_data: bytes
    if args.hex:
        raw_data = bytes.fromhex(args.input.strip().replace(" ", "").replace("\n", ""))
    elif args.base64:
        raw_data = base64.b64decode(args.input.strip())
    else:
        in_path = os.path.expanduser(args.input)
        if os.path.exists(in_path):
            with open(in_path, "rb") as f:
                raw_data = f.read()
        else:
            # Try auto-detecting hex or base64 from string argument
            cleaned = args.input.strip()
            try:
                raw_data = bytes.fromhex(cleaned)
            except ValueError:
                try:
                    raw_data = base64.b64decode(cleaned)
                except Exception:
                    print(f"[-] Error: Input file not found and string could not be decoded as hex or base64: {args.input}", file=sys.stderr)
                    sys.exit(1)

    if not raw_data:
        print("[-] Error: Input buffer is empty.", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Decoding Protobuf stream ({len(raw_data)} bytes)...")
    try:
        parsed_fields = parse_protobuf_stream(raw_data)
    except Exception as e:
        print(f"[-] Protobuf decode failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Build schema
    root_code, sub_codes = generate_synthetic_proto(parsed_fields, args.message_name)
    synthetic_proto = format_proto_file(root_code, sub_codes)

    # Build structured JSON
    structured_tree = build_nested_dict(parsed_fields)
    structured_tree["synthetic_proto"] = synthetic_proto

    if args.export_proto:
        with open(args.export_proto, "w", encoding="utf-8") as f:
            f.write(synthetic_proto)
        print(f"[+] Reconstructed .proto definition saved to: {args.export_proto}")

    indent = 2 if args.pretty else None
    json_str = json.dumps(structured_tree, indent=indent, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"[+] Decoded JSON output saved to: {args.output}")
    else:
        print(json_str)


if __name__ == "__main__":
    main()
