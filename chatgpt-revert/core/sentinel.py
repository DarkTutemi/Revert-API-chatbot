"""
OpenAI Sentinel security challenge solver (Proof-of-Work and Turnstile).
"""
import base64
import hashlib
import json
import logging
import time

log = logging.getLogger("core.sentinel")


def solve_openai_pow(seed: str, difficulty_prefix: str) -> str:
    """
    OpenAI Sentinel Proof-of-Work challenge solver (SHA3-512).
    Generates tokens formatted as gAAAAAB...~S
    """
    if not seed or not difficulty_prefix:
        return ""

    try:
        target_bytes = bytes.fromhex(difficulty_prefix)
        diff_len = len(target_bytes)
    except Exception as e:
        log.warning("Invalid difficulty hex '%s': %s", difficulty_prefix, e)
        return ""

    date_str = time.strftime("%a %b %d %Y %H:%M:%S GMT+0700 (Indochina Time)")
    config_list = [
        3000,
        date_str,
        4395630592,
        37,
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36",
        "https://chatgpt.com/cdn-cgi/challenge-platform/scripts/jsd/api.js?onload=jsdOnload",
        "d99109c5f030ae37cfee2f6bdcc7bb129fd03bbb",
        "vi-VN",
        "vi-VN,vi,fr-FR,fr,en-US,en",
        3,
        "plugins-[object PluginArray]",
        "__reactContainer$00jex9jksxt9v",
        "onbeforeinstallprompt",
        9848.800000000745,
        "74da3202-0133-4e08-8135-db18ff91ffa1",
        "",
        36,
        int(time.time() * 1000),
        0, 0, 0, 0, 0, 0, 0
    ]

    for i in range(500000):
        config_list[3] = i
        serialized = json.dumps(config_list, separators=(',', ':')).encode('utf-8')
        hasher = hashlib.sha3_512()
        hasher.update(seed.encode('utf-8') + serialized)
        if hasher.digest()[:diff_len] <= target_bytes:
            encoded_config = base64.b64encode(serialized).decode('utf-8')
            return f"gAAAAAB{encoded_config}~S"

    return ""
