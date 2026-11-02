import json
import re


def extract_gemini_text(chunk: str) -> str:
    if not chunk:
        return ""

    text_parts = []
    try:
        for match in re.finditer(r'\["wrb\.fr",\s*null,\s*"(\[.+?\])"', chunk, re.DOTALL):
            inner_json_raw = match.group(1).encode().decode('unicode_escape')
            try:
                inner_data = json.loads(inner_json_raw)
                if isinstance(inner_data, list):
                    for item in inner_data:
                        if isinstance(item, list):
                            for sub in item:
                                if isinstance(sub, str) and len(sub) > 0 and not sub.startswith("rc_"):
                                    text_parts.append(sub)
            except Exception:
                pass
    except Exception:
        pass

    if text_parts:
        return "".join(text_parts)

    if not chunk.startswith(")]}'") and not chunk.startswith("[["):
        return chunk

    return ""
