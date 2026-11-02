import curl_cffi.requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://chatgpt.com/backend-api/f/conversation"

headers = {
    "accept": "*/*",
    "accept-language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
    "authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IlNsdFlQZ2haN1I1UkFHZzM0em00eF9fc0FrVzAyd2VXT0t6SFlCc2tZNkUiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSJdLCJjbGllbnRfaWQiOiJhcHBfWDh6WTZ2VzJwUTl0UjNkRTduSzFqTDVnSCIsImh0dHBzOi8vYXBpLm9wZW5haS5jb20vYXV0aCI6eyJhbXIiOlsidXJuOm9wZW5haTphbXI6Z29vZ2xlIl0sImNoYXRncHRfbG9naW5fZmluYWxpemVyX2F1dGhfc2Vzc2lvbl9pZCI6ImF1dGhzZXNzX01TT1A3SFFYQ0IwbUlpa2xwQ1dQNVNhYyIsImNoYXRncHRfbG9naW5fZmluYWxpemVyX2ludml0ZV9pbnRlbnRfYm91bmQiOnRydWUsInVzZXJfaWQiOiJ1c2VyLWJhMXFlTDVMVEZZU0xGazRKb2tkTWRveCIsImNoYXRncHRfYWNjb3VudF91c2VyX2lkIjoidXNlci1iYTFxZUw1TFRGWVNMRms0Sm9rZE1kb3hfXzgzZjIwOWQwLTFiN2UtNGY1NC04ZDFlLTI0YWZiZjdiNmU5NCIsImNoYXRncHRfYWNjb3VudF9pZCI6IjgzZjIwOWQwLTFiN2UtNGY1NC04ZDFlLTI0YWZiZjdiNmU5NCIsImNoYXRncHRfdXNlcl9pZCI6InVzZXItYmExcWVMNUxURllTTEZrNEpva2RNZG94IiwiY2hhdGdwdF9wbGFuX3R5cGUiOiJmcmVlIiwiY2hhdGdwdF9kYXRhX3Jlc2lkZW5jeSI6Im5vX2NvbnN0cmFpbnQiLCJjaGF0Z3B0X2NvbXB1dGVfcmVzaWRlbmN5Ijoibm9fY29uc3RyYWludCJ9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJtZC5ob3NzYW4wNTdAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZhbWlseV9uYW1lIjoiTWQuaG9zc2FuIiwiZ2l2ZW5fbmFtZSI6Ik1kLmhvc3NhbiIsIm5hbWUiOiJNZC5ob3NzYW4gTWQuaG9zc2FuIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0pEQnN6YkJ5NHkyYzA0TVUwYi1ZMEhjQ2ZRZGt3ODhWUkdnUTlxbkhRSEZiLUJHcFU9czk2LWMifSwiaXNzIjoiaHR0cHM6Ly9hdXRoLm9wZW5haS5jb20iLCJwd2RfYXV0aF90aW1lIjoxNzkzNTIzMjE3NTkyLCJzY3AiOlsib3BlbmlkIiwiZW1haWwiLCJwcm9maWxlIiwib2ZmbGluZV9hY2Nlc3MiLCJtb2RlbC5yZXF1ZXN0IiwibW9kZWwucmVhZCIsIm9yZ2FuaXphdGlvbi5yZWFkIiwib3JnYW5pemF0aW9uLndyaXRlIl0sInNlc3Npb25faWQiOiJhdXRoc2Vzc19NU09QN0hRWENCMG1JaWtscENXUDVTYWMiLCJzbCI6dHJ1ZSwic3ViIjoiZ29vZ2xlLW9hdXRoMnwxMDIwNDU2NTk0ODIzMzE1NDYzMTEiLCJpYXQiOjE3OTM1MjMyMTksImV4cCI6MTc5NDM4NzIxOCwianRpIjoiMzI1OWM2M2E3ODEyNGI0YmFlNTRhOTkwYjkwMWJmMGMiLCJuYmYiOjE3OTM1MjMyMTl9.tZa4Kgm_dxEvKBpaE1fowbFaPqdi7Sw5TzW5KsS8IlMRFxlJh8SX5bKKnWD_Yez99I9flXe84aHu_SPHc_EhJvJ0b-OHnDwRgh0jq5oGdHAndHbCOaESPOK29Tmyw7V7B3CQgXFXem-MGEoGEE0tx-USsNyQHKfxbpAqhE3eOeuVkWDTRANxYoOyNeoTSfbH-lZoGgh2D4wVsRGHgPPr8aUTaO1qljTccNM5sNLPoFghkZ2lY-T0qmet71YaWLhmr3fTSIv_HpTLp-RMBD1HOngZPrchRq06cqfZtODgPyEWVHyqu5tIKM9RxUcclvO3Q41pgfCWKpTRZAQJI_0YeQ",
    "chatgpt-account-id": "83f209d0-1b7e-4f54-8d1e-24afbf7b6e94",
    "content-type": "application/json",
    "origin": "https://chatgpt.com",
    "originator": "Codex Browser",
    "priority": "u=1, i",
    "referer": "https://chatgpt.com/",
    "sec-ch-ua": '"Not:A-Brand";v="8", "Chromium";v="156", "Google Chrome";v="156"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36",
    "oai-device-id": "a9b1ac4c-6cab-4ddb-982d-f3f74d1759c3",
    "oai-did": "a9b1ac4c-6cab-4ddb-982d-f3f74d1759c3",
    "oai-echo-logs": "0,75665",
    "oai-genui-client-actions": "open_entity_detail,run_plugin_tool,launch_ecosystem_widget,trigger_agentic_handoff",
    "oai-language": "vi-VN",
    "openai-sentinel-chat-requirements-token": """gAAAAABq5wSKsZgXbCjPTuQ7fgs_DbfDxatRHH4fV6dqUQ7XX_89sVNzJ28Y2VNwSc2M9tD244VkigATE_zQSeQ6TdF3JK8yfl-nBdY-o09eL4aMTdgoJR3e_31tV8apGzJa-IvBFBjb3g-PttUR0vweeIygUUel6ng0wYqnxfceHKhyIbTH6kXTXPlqMlUOTxGqwy06qSAunRwQATPGSxX8v1C2xJVK1zVqX1R52rmrySkBGd9Q0p7Red8fBs47LF2KDZO7qagcr6-jsA_EIUBPZQQ1zpOCeU916dg03DSCi-bR6JGswy739OUXj56ZBa6U4AT7ksqbrgiErAg_pMvPxq6-HftQS_mZjdnkSyIN5Nlq5iEmAxpUHZf1MwOg8AITR-iEqWJFabMDJlzJ5Oa2hWfkBKqoSE8g71uGyObZZbOrPqTALCFRS__jsISyhmyN7HlFzsvE8HABvHiA1lwfOv7GadZzcwOOELveAKQ5fr73qO28HJD6ZDAXFaazbVUeB2hYbPji-_h7R32uWLFqGbBvmASyWoC22Uc_TV-0XyIurDzDOdKa1qrJ9zakWNcXptFXx68v9wJ3F2endQ7dYzy_959lIroBNQSCawGB09y8bzksEvHwWTL8qiiyxO04xxJaUWNbOICNKcHuuAsbLwjwE6Tl_gPNHuGl4G5wO7T9tu9AlraaBmw7jsL59DRzVxh7MszTFIWWEriZWhuD3Qrg42z0IZ4qdOIOBETQx_p0kRe1ao4Zkm07VlZOjvdu2pf6KKgr4oKpzVDhIhvwsl0Oezf2bThGLT5DpKFcP8n91nnEzGZjrVxgyfayPyItX33Mzp7JL9FBqcvzb-3kZJlQbG4AAhGy7lD35RC4N30e9HJ6qEeA2th5fWJx8t6gU4dJPedxwrS8MZE1Xq3glqmvddrQCujmv-4A3eCI_z2bN_VzlxWW0ZCQm0xKN3Ugt7-yY6EHLos_lyWN442c6MytU62ALIuOMzLZtHCj-tGX0H3WMYcSMlJrI8QVZUSY8IYz1nEhNuNXhb0stbVcsrSa6vJcM9BWA6-7cOuWEoI43NQY65ZBumNQ3ine_7dOU73rKBwk_bvOsWPEQZOjqjHgzv0CmiGQcqrU7LDyl-45HzL7cvCfRynpHjwzlnWI9NXiqvlQa9yCM8FhF3ZayUpTyF5kQ7g27jixU9G7LbSV2Mn-mZXk9HDwBgJ3LinXgH3UvARODoPUsZPFrFG3nw1vBfr3bqV6Bv8jtVPFIBZcwwybLTPA-iP2HNbl1ka4JmUc6kuEUiqa6TtBvJJ4P0IG6fuv5beVFdMXzD-7ecYG1zaeqng_Px0yWEPfZGoMUlIIgkjTppSy1wNMYP2zhbzN1LXOSw-U3QK01ec3hJCZr3Hzdskd3Ho9rRC0TucMpzr0OIGtDIdZlnja4lci8qs15QUQd7PTkPY5jng9WjQm_olax1wCk_RjR-RX-Ke_xUnLSGSjWF1g9IqLZC5yr2tqihxXL5Xk8XqfQPcQcEmrBiegVS5A50kCWBMf9ekyLjH-th5EXG2iaKO3LaVtSRSo84O9TF7RCr-w-HZivyjPMzFCZujOVnuiJogXr002TEppcr9XrgP1RVrKa9xsnPWPnm75TfniKEbQOW1NigShqqQoc2xQ_wGID7GCFuMbb8sfafgWtlF7xytKqlQkmySM9n4cvBG9kKcrVHf1ex2ztzWhF_WnSZuQbbjA7QT8EXIABxpU27Ut8alc99QvRD2_q3T7gc2Gm_w0u9wyIIAwdjBqrgPJJDVHU_TahAgRFbvJV8aZAWQh4c5fmGI7CLWuD8ZuS5gIQvR4FnZQNnKHZLC9NIr821L_E8mLsLRIJ9jwQscC-HTVbJPgYmzSwYiC_0JLSf-4AtZ6NPJmGEaHFRgPBsNY46MK_2kkqP5EvMk6QLk-HZxeVhC0AAhew3_mR9ARmRYtJmjw0RPr-dNXntfwuYky6tv20TQgAIOV9uNeyIWkzkOt1S6bx1O0cOytFoFfyN_cxCLT8yKfceNHFSwojznhjLWsbZFFQi9WxwCWicUfiOTanXZluy2lFhsG7htaxxqbIhr5E3Yn_W_A1rGaT_TI7hdkrHZ8KbYh1F4JulSJokL4hU1l7EKIgpJBJm85KlwrnfCU4EfmXeRLpgEVorFDGdIKkcdEvZPQGdvSHR5EzzCbB7mOn9PdD-miCa7rNsFyUwHKEE6EDsfVEtCb4tyyBwgwtcyOEX49v0SUpTEO3fJr_pqT-4kmHEpWYH_DMJltOsj0I0GxsGUg9CC2UD52owYP7PTyyBzcX0MyEAIExhg7FK537NXvpfZy4qScwxt0ZlT67Hk571HhtxfreUk7AtI6VPEj7keCXS6tcEjkzlPsXjqWdAkG372oGvp7arH-ZNWRsMUg4-pON56LZujQzzLt85oczPYeOPqoCwRGOZpQyF4yVSFnJESq9elq11OinTcBzbv2MXMtSJgm0Y1OrI93tyA_-0f0mtHhrwPovRgCdi1E549zdcg_Jhc5HLrwrTNvb0U_H0dAmVcIyvATmHc5BxGaNUMq1uUaXoQJbyT7rHGlc5h0q3sqA36iePcJHf-cGIvw6yfx4Km2dgrBnfRDf3zox0PiLmmJT1nfD6oFvfDWjdmfxRMYGKqpF4ZRMeUS7X-Ql23_gSkZvMRCtZY8AZT0OB69TRz-m8aSqaUks4BQv1qDn6VkY_sv01CRVPj2LB1SxCR_0kmKMUMK_PqGXFqjrEH-JPFAe7urZ1zwvMcP-d7PP2HFc__py4ffNCU5RPpUH4_vqe39UVsF6eZRkxlVaEbCISWap9C4WKdgT-_NTMeUWM9meaGyO-752LaBhJ6LsKkGhTdCayJZLHuT0UPjPX_aCah0tIRyQVcspwx5n0uszkOAZ-8RgqKQXkcjHTTGRj4_Q07OBfP27ZWtM_mggw9QfrqZNznV""".strip(),
    "openai-sentinel-proof-token": """gAAAAABWzMwMDAsIlN1biBOb3YgMDEgMjAyNiAxNjoyMToxMyBHTVQrMDcwMCAoR2nhu50gxJDDtG5nIETGsMahbmcpIiw0Mzk1NjMwNTkyLDM3LCJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXaW42NDsgeDY0KSBBcHBsZVdlYktpdC81MzcuMzYgKEtIVE1MLCBsaWtlIEdlY2tvKSBDaHJvbWUvMTU2LjAuMC4wIFNhZmFyaS81MzcuMzYiLCJodHRwczovL2NoYXRncHQuY29tL2Nkbi1jZ2kvY2hhbGxlbmdlLXBsYXRmb3JtL3NjcmlwdHMvanNkL2FwaS5qcz9vbmxvYWQ9anNkT25sb2FkIiwiZDk5MTA5YzVmMDMwYWUzN2NmZWUyZjZiZGNjN2JiMTI5ZmQwM2JiYiIsInZpLVZOIiwidmktVk4sdmksZnItRlIsZnIsZW4tVVMsZW4iLDMsInBsdWdpbnPiiJJbb2JqZWN0IFBsdWdpbkFycmF5XSIsIl9fcmVhY3RDb250YWluZXIkMDBqZXg5amtzeHQ5diIsIm9uYmVmb3JlaW5zdGFsbHByb21wdCIsOTg0OC44MDAwMDAwMDA3NDUsIjc0ZGEzMjAyLTAxMzMtNGUwOC04MTM1LWRiMThmZjkxZmZhMSIsIiIsMzYsMTc5MzUyNDg2MzE2MCwwLDAsMCwwLDAsMCwwXQ==~S""".strip(),
    "openai-sentinel-turnstile-token": """QhUaHg0MFRQSe3tcdxIUGwIAAAEbDR8ADw0HFwAJDQEcHBoLBAABABsNHQQACgUcAhQbBR8eDQEVFBJ7XmITEhQbDwAHDxsNWkJNXBsMAw4XABcSAk1FW1UUGwAZHgwLFRQSXlVfbGYJa1RoAlxcYFZTYHtZG0VbcXlAU2p8CgwcGggHAAUMGw0MVXBVR0h4CGN/HHJVWm8fG1pBQHdUCn9ZSnh+DXEcXG5fW3R2bG9id1ZVdwVrcVNzdkYEaVtxb2h6XnVvc2laUm9xVA9zVkdifn8fVWB/YUxkaWtGb2FTY2Z4AU59YHd4fFJ1Ympfc09vcmljVFYBCHpmSVUaFRUcBBYBBQwKGnZze0V2TgoTEhQbDh0eCgAVFBJpbHFsYW1/dX9lfntme3UBGxsMAxYAAQwKGmhfeGd9Xn5kd09BfWlXdX5wf1d2f2V4am9vT2BoT058bVdfY39JdXZ9QHtScHtHfGVTXW97dQhvcW95aH9leFFgCVBMdGoBf29xT1tza3pqYVsXUX1efmJyX3h2bWFPe39vZW1+BnhyanxPeWdfTnxtYX1+f2xHWW9hZHlqe1hqcgl0CgwcGgwHAAgLGw0Mdwp3b392CQFleEhealBjaFpvcXlmCVFWa3VIWmFFX2lqclppYFVhZWRuDHt/SFBuYn8Ffm9bH2Nrf1t5aH50eGl1SFphRUBib1saaHtveXtlfnN2fHhIbmBoQHxtclpnYFFUfGR+VXx4Zg1oYHtEbW1hSmRrCG18ZglzfHxmYl1iRVhib1tWZG8IAk1ofn9/dlwJXWZFcm1hYRdVaX9hTXdPBAoMHBoMAQAEGgMVb2EFBBUCEgwBGRsBGgMVb3F5eHZvcXl4dm9xeXh2b3F5eHZvcXl4FQISAQoZGgIaAwcACQAKAhkAAAwCHwAPDgMXBhQbARseAQsVFBJhUWFeaAldUnkAS2hUeFRteHVnZX8LdWZoX0p7aGFxfXRGZX5+QHRcGhUVHh4MDBUUEm1seU9hfUpzaXF+bWJoWHxqYmx9fghlbGhqXVZpclBrb38EcHF2RX9+eANPc2leYmpICW9gVmF3cVBCVH54fX5lTw1+bHUBbW9JBGhqQBMNGhUVGQkWDw8MChpoX3hgalVbf2cLVW12dQlfc29fcnpmFlVwe0d3YW0AbXh4fmplH1RpbWV7ZXlodmFyaXBkeWUBbmUfSAhhcWhRfV5+Z3RQTnZockxuYGh2am9gYHJpe1hqck9wZHkBYltme3oAYXJKUW97WGpyalZUaVx+amUfVGltZXtleWhyYnJPcGR6AXptYEJXWXhAd1V7eFB4dm4MbX92QFtWQmZxbWEWfXteWGBjXwQKDBwaAAEABBoDFQwcGgEPAAcPGw0Mc198CgwcGgwZHAkaAxV9W3ZpZWtEaWx2bFNvbEdqU24Ib3ZmDXBgeAFcWHFeam5vQHRjCGNteGVyaWVodm9uYR5TbghfS3Fuf359ZWl7b2h2XWEGXnhgb3V/YlNoYXpccnR/H0RvblsbVmsIT2hRU3NtdgB1e28eCWBsW1lVbF5ETGhta216ZWpxYVZqc2gHF2Nuf09BYgloYGpHAFt1b0dye3VJdX58R2pkCGt7e3Z5eGYfAXNrckpWblRtS2NQDXhvYXFYdW9Xc3hlQVNuCF9LcQl3Ynt2cnhlbGZhaFteaX5vcUtobWtvfQAMem8fXGl+chdxa3xYd2F+AAJ6dXZ+bXtEW2tgYGZrCUd5Y25vAHhbcnhlbGJya2JaZG1sR31TbkFveVxiWGB4VGBYckplYG9TamIIa3VoZmp7YWgBen5iVnNuCQJrYwhwYHl1XFxtaHJbblxadH5SD2lxX3dTalx1X3Z/cXl4XEZkYG8GeWRpaGJ5XFByYXtxYGtyWnVsf3V0Y210YX1cVGlma0RqbnFBVWsIT2toblVveABpeGVJWwUbSg==""".strip(),
}

cookie_str = """oai-did=a9b1ac4c-6cab-4ddb-982d-f3f74d1759c3; oai-did-first-seen=v1.a9b1ac4c-6cab-4ddb-982d-f3f74d1759c3.1793523204; oai-mweb-route=1; oai-mweb-origin=1; _cfuvid=Kik5NBYX5.Mv1YTjoW7xG9rXJp1Q_PTOpOqIRR_B9Rc-1793523205.308107-1.0.1.1-pIWmN7GsrFJGZK9amdXiAnOqKFGqPreRufkz75MId7A; __cflb=0H28vzvP5FJafnkHxihKZRMPTs8EfEnoYHmuT7Tebas; __Host-next-auth.csrf-token=7cdfaf9ee64aaedeae1af543444b1067cca25a81b606a770fba0a9e98dfb22e6%7Ca63997073d18fb9c8f5a6b39d0e6867a5728e7364f4ef1a3694326a3011b5971; __Secure-next-auth.callback-url=https%3A%2F%2Fchatgpt.com%2F; _account=personal; _account_is_fedramp=false; oai-client-session-epoch=83337868-36ff-49b9-9259-4723c8b9e176; oai-hlib=true; oai_pl_permission_state=not_set; codex_sidebar_width=340; __stripe_mid=66a92155-bbbe-4096-9f1a-9d30411f46dc3c2903; __stripe_sid=96536dd4-0ea9-42cf-a10b-5ddfb3d22ccc393333; oai-gn=hossan; cf_clearance=CtMdXMU_V-8GZnH8CqPk2h4gjRELO3sNyJVaKgSdLf6sBnINiWF4DRk4YvvvjStXW3x_SgP-4e1auVq-9tZJaCd24tC29hkoyTPJFf3OoS4Nbl-0GWD520h-RlY8n56eAn2wLVS5Bx5eSsH_AsQ-YyLQMC4btRRwdCDp7ogeRA8Xc7Jv_IlacTuJfXU-VdDD2APmtO3Y9GT4WdmCeGqvWcP8x_3YySgM3-h2okkBnYeHATr5NvGoT3sYQk561E2IQvSrOxgzb1awJeaNbNZ0YdtrKqpDO8trd77GOL_6vZ5lAtoZQRI7; __cf_bm=bHVJbNZkmVRehgtnHbG7E4zs746mn1LFh_elWbcJ_Qg-1793524869.0948377-1.0.1.1-a7ixL_bg9yPQwr_pCh81.jf.tCG3bFc66YvuZvadhMefEao4YMvHkYoXm4MM98pdKVMqzWh7.xu9u6xw_FoG0LsVzP5yyWBYyf1CgL.MIrqwQdNx4OcyXKIQQXT8I6i7"""
headers["cookie"] = cookie_str

data_body = {
    "turn_attribution": {"turn_trigger": "composer"},
    "conversation_id": "6ae70296-9490-83ec-909e-5ac613acf78e",
    "action": "next",
    "model": "auto",
    "parent_message_id": "2ed6ec2a-4cd5-4f57-8c5d-98563fa8d5da",
    "timezone": "Asia/Saigon",
    "timezone_offset_min": -420,
    "is_do_not_remember": False,
    "client_contextual_info": {
        "app_name": "chatgpt.com",
        "app_surface": "codex_browser",
        "has_web_push_capabilities": True,
        "web_push_notification_permission": "default",
    },
    "local_function_names": ["local.continue_in_work"],
    "messages": [
        {
            "author": {"metadata": {}, "name": None, "role": "user"},
            "channel": None,
            "content": {"content_type": "text", "parts": ["hello"]},
            "create_time": 1793524942.205,
            "end_turn": None,
            "id": "a41e4672-7fdd-4651-b726-9e5806cf4b59",
            "metadata": {
                "automation_creation_attribution": {
                    "origin": "conversation",
                    "flow_id": "a41e4672-7fdd-4651-b726-9e5806cf4b59",
                }
            },
            "recipient": "all",
            "status": "finished_successfully",
            "update_time": None,
            "weight": 1,
        }
    ],
    "supported_encodings": ["v1"],
    "genui_state_snapshots": [],
    "client_prepare_state": "success",
}

s = curl_cffi.requests.Session(impersonate="chrome124")
resp = s.post(url, headers=headers, json=data_body, stream=True, timeout=30)
print("Response status:", resp.status_code)
for line in resp.iter_lines():
    if line:
        txt = line.decode("utf-8", errors="replace")
        print(txt[:120])
        if "data: [DONE]" in txt:
            break
