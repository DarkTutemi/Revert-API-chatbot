import hashlib
import json
import base64
import time

def solve_pow(seed, difficulty):
    """Solve OpenAI Proof of Work"""
    diff_len = int(difficulty)
    start_time = time.time()
    for i in range(10000000):
        val = f"{seed}{i}"
        h = hashlib.sha3_512(val.encode('utf-8')).hexdigest()
        # check zero prefix or condition
    return i

print("PoW solver test")
