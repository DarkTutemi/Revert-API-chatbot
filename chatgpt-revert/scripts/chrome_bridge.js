// ========================================================
// ChatGPT Proxy Bridge v1.0
// Paste this code into Chrome DevTools Console on chatgpt.com
// ========================================================
(() => {
    console.log("%c[ChatGPT Proxy Bridge]%c Connected to local server!", "background: #10a37f; color: white; padding: 2px 6px; border-radius: 4px;", "");
    
    let isProcessing = false;

    async function poll() {
        while (true) {
            try {
                const res = await fetch("http://localhost:3000/bridge/poll");
                if (res.status === 200) {
                    const data = await res.json();
                    if (data && data.job_id) {
                        console.log("%c[Job Received]%c ID:", "color: #10a37f; font-weight: bold;", "", data.job_id);
                        await handleJob(data);
                    }
                }
            } catch (err) {
                // Server might be restarting, wait 3 seconds
                await new Promise(r => setTimeout(r, 3000));
            }
        }
    }

    async function handleJob(job) {
        const { job_id, payload } = job;
        isProcessing = true;

        try {
            // 1. Get sentinel requirements from current active browser tab
            let reqToken = "";
            try {
                const reqRes = await fetch("/backend-api/sentinel/chat-requirements", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: "{}"
                });
                if (reqRes.status === 200) {
                    const reqData = await reqRes.json();
                    reqToken = reqData.token || "";
                }
            } catch (e) {
                console.warn("Sentinel fetch warning:", e);
            }

            // 2. Send conversation request
            const headers = {
                "Content-Type": "application/json"
            };
            if (reqToken) {
                headers["openai-sentinel-chat-requirements-token"] = reqToken;
            }

            const convRes = await fetch("/backend-api/f/conversation", {
                method: "POST",
                headers: headers,
                body: JSON.stringify(payload)
            });

            if (convRes.status !== 200) {
                const errText = await convRes.text();
                console.error("Conversation error:", convRes.status, errText);
                await fetch("http://localhost:3000/bridge/error", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ job_id, error: `Upstream HTTP ${convRes.status}: ${errText}` })
                });
                return;
            }

            // 3. Stream chunks back to local server
            const reader = convRes.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunkStr = decoder.decode(value, { stream: true });
                await fetch("http://localhost:3000/bridge/chunk", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ job_id, chunk: chunkStr })
                });
            }

            await fetch("http://localhost:3000/bridge/done", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ job_id })
            });
            console.log("%c[Job Finished]%c Response streamed successfully!", "color: #10a37f; font-weight: bold;", "");

        } catch (err) {
            console.error("Bridge handleJob error:", err);
            await fetch("http://localhost:3000/bridge/error", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ job_id, error: err.message })
            });
        } finally {
            isProcessing = false;
        }
    }

    poll();
})();
