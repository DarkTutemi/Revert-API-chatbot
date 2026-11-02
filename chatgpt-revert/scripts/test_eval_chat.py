import asyncio
import sys
import json
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

raw_cookie = """oai-did=a9b1ac4c-6cab-4ddb-982d-f3f74d1759c3; oai-did-first-seen=v1.a9b1ac4c-6cab-4ddb-982d-f3f74d1759c3.1793523204; oai-mweb-route=1; oai-mweb-origin=1; _cfuvid=Kik5NBYX5.Mv1YTjoW7xG9rXJp1Q_PTOpOqIRR_B9Rc-1793523205.308107-1.0.1.1-pIWmN7GsrFJGZK9amdXiAnOqKFGqPreRufkz75MId7A; __cflb=0H28vzvP5FJafnkHxihKZRMPTs8EfEnoYHmuT7Tebas; __Host-next-auth.csrf-token=7cdfaf9ee64aaedeae1af543444b1067cca25a81b606a770fba0a9e98dfb22e6%7Ca63997073d18fb9c8f5a6b39d0e6867a5728e7364f4ef1a3694326a3011b5971; __Secure-next-auth.callback-url=https%3A%2F%2Fchatgpt.com%2F; _account=personal; _account_is_fedramp=false; oai-client-session-epoch=83337868-36ff-49b9-9259-4723c8b9e176; oai-hlib=true; oai_pl_permission_state=not_set; codex_sidebar_width=340; oai-gn=hossan; cf_clearance=CtMdXMU_V-8GZnH8CqPk2h4gjRELO3sNyJVaKgSdLf6sBnINiWF4DRk4YvvvjStXW3x_SgP-4e1auVq-9tZJaCd24tC29hkoyTPJFf3OoS4Nbl-0GWD520h-RlY8n56eAn2wLVS5Bx5eSsH_AsQ-YyLQMC4btRRwdCDp7ogeRA8Xc7Jv_IlacTuJfXU-VdDD2APmtO3Y9GT4WdmCeGqvWcP8x_3YySgM3-h2okkBnYeHATr5NvGoT3sYQk561E2IQvSrOxgzb1awJeaNbNZ0YdtrKqpDO8trd77GOL_6vZ5lAtoZQRI7; __cf_bm=bHVJbNZkmVRehgtnHbG7E4zs746mn1LFh_elWbcJ_Qg-1793524869.0948377-1.0.1.1-a7ixL_bg9yPQwr_pCh81.jf.tCG3bFc66YvuZvadhMefEao4YMvHkYoXm4MM98pdKVMqzWh7.xu9u6xw_FoG0LsVzP5yyWBYyf1CgL.MIrqwQdNx4OcyXKIQQXT8I6i7; __Secure-next-auth.session-token.0=eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..Heyckf3ZLIXR8tPD.XCEb5NnxoMty5vfoYe-7Ypu79-cKjh4liuR039K6NOMxiwopX61FyfcApemoHAIfW6fSvSglb-gFUoN89dQmPoc1kRznaZUBbfR6jRTzTUETAB0zRDfqFd3glDsWyEZTA7CaGVnLZboT1knc2UmmvkWvpSL-MO7-4Vb7Yjn1Ovbuk-ByDuadWUDMFnBT1ZOei8Q8jSvRuzhnEeMQbgNzJDND61I_jLcRV1xuP37s-cvtB0pNr7Zzutgo5LG1JoSWECJZa1c2W9MrL0kg-rVA22HgJHbrZDTMtad90UWDebYmnsLcqIRTqtfFq7ispcbJdaDqyTZjIQWGVKit_K0pyOteaybSJKBGS4UKcoXIMb-mo4DysMRrTM6hHLG4w_taShpKLIsfYvlrlEVhyXZpBdqOWZPmU--ieziKA08tsg6mn7RBnGjJ4V_Y1aRiECYhuIonNX15v_p6HOLivAwB-XDntbMDXvn5_U7PYIEPmmqudeN6kTiSPtdN9weTqKCm-pnRV-_V3n60KXrVA99SF-7SGhms-45Hqu5xuevzCCqqD4OwF-1k-aqACiEntxVfGvyFJZwAph7DyiVjmdeti3qU1DsDIY05z9Rfh9d_H2Ml5ggPFSHQmyhritjNIrM6R2jVppn6JGM8pYLO9N-9Sv0O18EiSMD6ascEcu5FM4klkhYINAXMZ43MIKUTqhHXNopKdaFWvknjd7r4DqRxgwEOjuizANb3X6pB2ZUSSsHpd-KGKUsz6l2TuH4CoTSawxzPQ8OV9RVwjkV08MheXkPBRFTkDw-6UFdkWHaLf-rNLwpKgLQMMoo_PPmdhB0onBYOxG_1palghkkFm1bP8_8cK28T_zn5ECs5mQGwXieh0yAMkOQjpdfA78EqwF7oaKGhIaGhNcm2WHLfBojo433UtOWerFGIOzUAkr8tC2YWRyrEh_yMpdiM_FTpwUxmn8txrmZnp8H9YIGzvQDoYThDgqz_fbA9B6VZiA0nWq2hRuzZOGNWGLdcPznod1maUbXtLZ_39canPWE6G1pnoX6QpSnynCihrIA4jUm3KsqY8OF7R8FGK1LexB02GQMNtSgu_h5bsvxmhvzsGY32GoEGQr0OWjm9xEy8FEkb8WZoZOE_DGWd9UmAyh51xnvnj310_cD7Qzao_od8aftu0wW2xkXZIAGiqPBbwT4Y7FJZTguq03VgGDuVsU-k2cLU0DrS6Aj2HJ9i238Atp6IFSZJirTKkbDSy7L4FCNTN8--gQ8Ui0pvaU0GIqsU93QUfTKsFK5REZpQoPpW7U7KWEXc2RKUTdicbcTrK2lsj7qVQ8-lhkRBwkSDZdmEingXb6uXUGm-k9tDb9onqw1koy8-ZX1ZOM_VOlmujlRaPDjC0DP0XcjvMhYOpjc3DjPWTKeJzG5WhW3RPnkC6fEDlLwS8NfEDaEmd4Cy4M7A2npuMj1sJF7N5xvgCSEdigoDvm-VO279Nfbmmitr6nRxJ9YSRKf6cdBM0jbj3wObWTuO7IBab77w_sBqSzLmyOs39hBh4mthsdSMqIoJ20njqERuHLPoHbBIxR9PWBYvpFAIYsXGk4qXm6wF4Uvv4n68PwyR1rWJ9LNBOFQP_2sk1_B_MAJWxP2iwqbliTxewap0VgTfwxFgYkBwm_J94NNxZP2JObtUkh-UO579iorQ4TeJy45CDDi7-OdFJrrDDkQh9RGgRuKBLtj0Luly3JhbRzAQzbDqUw0xPN7mGWi-Rm9lQcANAAS0a1FEhhFCm5V7HsaWOVdaB5gQGZXOTi9NFFF7-tKJdA3c_U0y7usdYAfFx0E2Bg_75p0IeXaS2M1bcTW_F2UqE1GbYbkO4PJeEozHo9uQEjztAr-QW3U8771sRefPX5XfN5p817Eq6CAbuk2kvuOxR0gG111CSK6jPeEhpwR0XCtDAZ5fnQPbg_IPPy-rcAbyHlX0wRYrobLDxgwhMOewcV2M5SmAwxM9YUyCs6H_4C_hkJuTvGT6a_aDyWbhYYZW2xV06kKRpHvfUK5q85ZOtny9Pe1zEtYK_r6qbYxD1Zd6hBEzmzp0tc84W_t3bnzuzUe3AJBMqKEw-EwxdH5RwvaQkMHzs4pAN7j_APy6UoaCSKCApuTTH3ICYDWrlF9xs7PzCS3rWGR6w3r8UKHgd-GT-DPbTI8QO9CD9L5N2rhxTQ1LneC6MQYp-Uzm6AAdWC6WjYKUZOn4hm6_lvzgJtFdNGeBP5tgEr2kwHG2sXbsL3FxflA1vzq-SJrw2OPz4ystAD1VI1OoDTn2WEjoPSDRYa7rlo2lPvaiqJ2f4tktsmHIfOHASN_McDL7ZG1kAEhVr3-1fsAdGLjOcvFCX7XT0p27yH9lbxk6L7fiTRcO8UV7yewaGFEOpkLdpddvLJQ8cpenGJsv7rrgkZP5xYq1LT-G0iBRfaoVJuK04D8ygu9rD_-tzImE9XxWJeqJuacFcHmEqg1t578m-OUBzLeWTHKAfxTGS37SzqlWYSTy3cfXb4S8c1X-_4AqwQqqzjQaTw-k9z4s5yJ8sNoBZv488kdV9-0HZBlWnDkUkXdtI3fCiDf-2wpfZSqQ3tkeVu3vdEYSSrSckyZAnCtopI8lmWhxHagnMaDR7KcKwpRtjpG3uEhLixgAw0gF-JDFTYQfm9byVd2v8gL0-L7v6QwdhOiE4ZXayVyIGfF4PiztcbSkAGjiN52anW_B_af0DAbJwkkXwGZ5uHocKXMappiJuXQM7k1P1kwElyieIabtP4sg4ZaDnqHbOMqIgWZzeEx613Px1TaKdqezy1ZGvoKuYnSIOerP8KF0UKUNTHvVeuAhkq0upugSsAvIRSam__IF9btUTnSSseIGqBIEBr61jA1-zHQ-OWqr0vV-fWgDY7UVBYMSCG4Y1JiwxTT0My7nRyIMIg9n9Q6xoyuTUpYVlY4LOpmTRk5v-zfCqFHYdELEciuW7Xfzh5KV9hvaxTXEmGQk6V3xKf0R8bH0h2z9y6xRM8xg73KEld-6VmEkiLoMg36LsLGir2HHeQFrca9zZi42VagpNE656ReVRwe7UfLUTvuzHp862OHz7OwYHlBj6AXFhraBQNBrnKt9lPX19PTvbG0T1A4titl_4-QB-bzodnfZ1fc1VnGdvHQoG5lPwpyk56BtBWbqaJcOy0TxOm9Vli-Tv24BGEhWJ5Km2m5y1LyDhcIuDpEaOEu41iXKzoS5xBLzA5Tq5VoI7hLG_UGrv3UenYFyLDO_I73MgvhgmYKcPrNfmhqUfkSwCJ9u_BLQwGU0fbVuIfMnscg5d802tviU8c5Cd-M0sju3zK6FtKcze1nobtZD094bltoIdGNU3TZ9ii6V6DCryj8HZDSO0uIldRGxtFRndKWYys7rqI9X6_2V5GtBH7KafUZyHef99qFM0dcz3pzp5PTOZAlJlWwND6wzgdvPwwiEWJHVYfmbJ81ixeMWLOoO5jrPpgSVdQMqtEBkHreXvJnVRgg7wzhFVv1VMeTME7tw0b6zknB5eGOvzON-3jE9hW_Tr3m1jiVBb8BnQX2vvPLyr4tq5Y0iXqa9q1aNrPJhRE7M5dMXIbijJg-Fjf2cEf96KfuZL9eZdMaS54aHz2KtSu1tEGS4FiHJXWbICRRXSNjID4e2pQEE8P86xJhWarryKIV4RJffi2JfIZKz8dZtIFB5UZ75WelLPrJQ50v_e3vcoVRb4YQfbKw9t4KCJIKeAp2J_fcPKTBhCcnMPW0D-ecK0afsoVWUbFDS4n3QLmIMbD4U_zg-kSb07cR8sv-vhdiSCeh21mARW5rHGmGAKA94Rb_N7e00p9qkXXmUQBH9zOnOQ7BrjYSb70jBBuWBPQbFbeAJxTcJCgnjf8L; __Secure-next-auth.session-token.1=Yg8GjDhXBg1Dx3I8IO1GbGbA6-h0Rcjh_Bb31gH0Vm-L0cgZQ5ZGFNm1I6Z6zF3t2iy3r_9qmj2WljXztyoA5Xa_L4W6PlRxG_TdWa5nD8uJwCydExYVxHz-WFSCDf_mGl7oI6TkWmmBpom-haAO4ZQBC3yn0I0UMLYxRDoGln2AKOOOztZbaMBSKyCBR90lZbEPSRo7fXf_3gCM_bLdORgM1f2U1b_nU-EFrugyvLsTo2d5C_0ZQ8z77DJo8YEw2qDEBXb1uHXyHqce4o9UMZJBT2CRfj7ajRnLaG-K19-gucgedziI4W_oizfk6COMR8qUgUf8lrV1u2UTbhFK2zTOt-RPn9qFDTc0R9hkpRgDEzsI_V3iJ9HOhMbbailcmGt4omzRJKUdRfuOxnvLv26jdcyRlOQxaa4wPzhQdsqTVYciRVwSU4OgJBNVSyBod1VZrfT-45UdiO1so7IT6cZodLJa9OpaR1VZa_Regoij1q8ettERf2za8fFVo5dghL20hNF195QqipAjkzQLbztQqcuH082824zTVlYmEFbT8SL_UzDxwMHqDq-GpG2j6Hvf47A8G-l-N79V3qFgYfjg4alNWmVUcKCYPtJOjOLwQ_qCc5dPUHLdSyUO-LE1II3ACjpUCR5XU826i1ClizJ-48p9Z0l3w44m7sZ_DPYyUSm8DwqqIKNFdE6IU2I6nQ3ogkpo_uBtel1L7us7pF_m_Y-59pu0798V-BOInVjrYQi1PQOGqcW_wB4LxuHMJqlGEf20ROskxUjB9FBRCIpkLRBsIf_xT6wclRMBDWPWYnxlM1OPecTWxkf113-jP7VkEKMkzB9alITCiLuvzEQrk6CNh165P6w.jArjEJ-wbj8tjJjJLHyRSA"""

access_token = """eyJhbGciOiJSUzI1NiIsImtpZCI6IlNsdFlQZ2haN1I1UkFHZzM0em00eF9fc0FrVzAyd2VXT0t6SFlCc2tZNkUiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSJdLCJjbGllbnRfaWQiOiJhcHBfWDh6WTZ2VzJwUTl0UjNkRTduSzFqTDVnSCIsImh0dHBzOi8vYXBpLm9wZW5haS5jb20vYXV0aCI6eyJhbXIiOlsidXJuOm9wZW5haTphbXI6Z29vZ2xlIl0sImNoYXRncHRfbG9naW5fZmluYWxpemVyX2F1dGhfc2Vzc2lvbl9pZCI6ImF1dGhzZXNzX01TT1A3SFFYQ0IwbUlpa2xwQ1dQNVNhYyIsImNoYXRncHRfbG9naW5fZmluYWxpemVyX2ludml0ZV9pbnRlbnRfYm91bmQiOnRydWUsInVzZXJfaWQiOiJ1c2VyLWJhMXFlTDVMVEZZU0xGazRKb2tkTWRveCIsImNoYXRncHRfYWNjb3VudF91c2VyX2lkIjoidXNlci1iYTFxZUw1TFRGWVNMRms0Sm9rZE1kb3hfXzgzZjIwOWQwLTFiN2UtNGY1NC04ZDFlLTI0YWZiZjdiNmU5NCIsImNoYXRncHRfYWNjb3VudF9pZCI6IjgzZjIwOWQwLTFiN2UtNGY1NC04ZDFlLTI0YWZiZjdiNmU5NCIsImNoYXRncHRfdXNlcl9pZCI6InVzZXItYmExcWVMNUxURllTTEZrNEpva2RNZG94IiwiY2hhdGdwdF9wbGFuX3R5cGUiOiJmcmVlIiwiY2hhdGdwdF9kYXRhX3Jlc2lkZW5jeSI6Im5vX2NvbnN0cmFpbnQiLCJjaGF0Z3B0X2NvbXB1dGVfcmVzaWRlbmN5Ijoibm9fY29uc3RyYWludCJ9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJtZC5ob3NzYW4wNTdAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZhbWlseV9uYW1lIjoiTWQuaG9zc2FuIiwiZ2l2ZW5fbmFtZSI6Ik1kLmhvc3NhbiIsIm5hbWUiOiJNZC5ob3NzYW4gTWQuaG9zc2FuIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0pEQnN6YkJ5NHkyYzA0TVUwYi1ZMEhjQ2ZRZGt3ODhWUkdnUTlxbkhRSEZiLUJHcFU9czk2LWMifSwiaXNzIjoiaHR0cHM6Ly9hdXRoLm9wZW5haS5jb20iLCJwd2RfYXV0aF90aW1lIjoxNzkzNTIzMjE3NTkyLCJzY3AiOlsib3BlbmlkIiwiZW1haWwiLCJwcm9maWxlIiwib2ZmbGluZV9hY2Nlc3MiLCJtb2RlbC5yZXF1ZXN0IiwibW9kZWwucmVhZCIsIm9yZ2FuaXphdGlvbi5yZWFkIiwib3JnYW5pemF0aW9uLndyaXRlIl0sInNlc3Npb25faWQiOiJhdXRoc2Vzc19NU09QN0hRWENCMG1JaWtscENXUDVTYWMiLCJzbCI6dHJ1ZSwic3ViIjoiZ29vZ2xlLW9hdXRoMnwxMDIwNDU2NTk0ODIzMzE1NDYzMTEiLCJpYXQiOjE3OTM1MjMyMTksImV4cCI6MTc5NDM4NzIxOCwianRpIjoiMzI1OWM2M2E3ODEyNGI0YmFlNTRhOTkwYjkwMWJmMGMiLCJuYmYiOjE3OTM1MjMyMTl9.tZa4Kgm_dxEvKBpaE1fowbFaPqdi7Sw5TzW5KsS8IlMRFxlJh8SX5bKKnWD_Yez99I9flXe84aHu_SPHc_EhJvJ0b-OHnDwRgh0jq5oGdHAndHbCOaESPOK29Tmyw7V7B3CQgXFXem-MGEoGEE0tx-USsNyQHKfxbpAqhE3eOeuVkWDTRANxYoOyNeoTSfbH-lZoGgh2D4wVsRGHgPPr8aUTaO1qljTccNM5sNLPoFghkZ2lY-T0qmet71YaWLhmr3fTSIv_HpTLp-RMBD1HOngZPrchRq06cqfZtODgPyEWVHyqu5tIKM9RxUcclvO3Q41pgfCWKpTRZAQJI_0YeQ""".strip()

async def send_chat_in_browser(prompt: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36"
        )
        
        cookie_list = []
        for pair in raw_cookie.split(";"):
            if "=" in pair:
                k, v = pair.strip().split("=", 1)
                cookie_list.append({"name": k, "value": v, "url": "https://chatgpt.com/"})
        await context.add_cookies(cookie_list)
        
        page = await context.new_page()
        await page.goto("https://chatgpt.com/", wait_until="networkidle")
        
        # Test sending message using in-page fetch with all browser APIs available!
        result = await page.evaluate("""async (args) => {
            const { token, prompt } = args;
            
            // 1. Get chat requirements
            const reqRes = await fetch("/backend-api/sentinel/chat-requirements", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + token,
                    "chatgpt-account-id": "83f209d0-1b7e-4f54-8d1e-24afbf7b6e94",
                    "OAI-Language": "vi-VN"
                },
                body: JSON.stringify({})
            });
            const reqData = await reqRes.json();
            
            // 2. Init
            await fetch("/backend-api/conversation/init", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + token,
                    "chatgpt-account-id": "83f209d0-1b7e-4f54-8d1e-24afbf7b6e94"
                },
                body: JSON.stringify({})
            });
            
            return {
                persona: reqData.persona,
                hasToken: !!reqData.token,
                powRequired: reqData.proofofwork?.required,
                turnstileRequired: reqData.turnstile?.required
            };
        }""", {"token": access_token, "prompt": prompt})
        
        print("Browser evaluation result:", json.dumps(result, indent=2))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(send_chat_in_browser("hello"))
