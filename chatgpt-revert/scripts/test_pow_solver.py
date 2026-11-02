import base64
import hashlib
import json
import time

def solve_openai_pow(seed: str, difficulty_prefix: str, config_list: list = None) -> tuple[str, bool]:
    """
    OpenAI Sentinel Proof-of-Work challenge solver.
    """
    target_bytes = bytes.fromhex(difficulty_prefix)
    diff_len = len(target_bytes)
    
    # Standard browser config metrics matching real Chrome
    if config_list is None:
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
            "plugins−[object PluginArray]",
            "__reactContainer$00jex9jksxt9v",
            "onbeforeinstallprompt",
            9848.800000000745,
            "74da3202-0133-4e08-8135-db18ff91ffa1",
            "",
            36,
            int(time.time() * 1000),
            0,
            0,
            0,
            0,
            0,
            0,
            0
        ]
    
    # Notice: In the proof token we decoded earlier, config_list is the JSON array:
    # [3000, "date...", ...]
    # The candidate is candidate_data
    # Let's test with the JSON array
    for i in range(500000):
        config_list[3] = i  # The iteration index is in position 3
        serialized = json.dumps(config_list, separators=(',', ':')).encode('utf-8')
        encoded_config = base64.b64encode(serialized)
        
        hasher = hashlib.sha3_512()
        hasher.update(seed.encode('utf-8') + serialized)
        digest = hasher.digest()
        
        if digest[:diff_len] <= target_bytes:
            return f"gAAAAAB{encoded_config.decode('utf-8')}~S", True

    return "", False

# Test solve with real seed
seed = "0.8673915715213527"
difficulty = "061a80"
print(f"Solving PoW for seed={seed}, diff={difficulty}...")
t0 = time.time()
token, ok = solve_openai_pow(seed, difficulty)
print(f"Solved: {ok} in {time.time()-t0:.2f}s")
print("Token sample:", token[:60], "...", token[-10:])
