---
name: local-llm-llama-cpp-serving
description: Use when running llama-cpp-python or llama-server locally.
category: local-llm-serving
---

Pin llama-cpp-python to a release that supports the model's architecture, then reach localhost without the agent proxy.

- A new model architecture (Qwen3-VL) fails to load on older pins. Check the release notes and install the newest version that supports it, then record the pin in the bench README.
- Localhost calls bypass the proxy: `curl --noproxy '*'`; in Python `urllib.request.build_opener(urllib.request.ProxyHandler({}))`.
- Wait for readiness with `until curl -s --noproxy '*' http://127.0.0.1:8080/v1/models >/dev/null; do sleep 2; done`, under a timeout.
- Start a server that must outlive one benchmark detached: `setsid nohup python -m llama_cpp.server … > log 2>&1 < /dev/null & disown`. A tracked background command is killed at its 2-hour cap, and every later call then fails with `Connection refused` and is scored wrong. Discard that run and rerun it.
- Keep the fixed system prompt first and the question last. The server reuses the repeated prefix from its cache, so only the new tokens are evaluated.
- The server holds several GB of RAM. Stop it before an export or quantization step, and restart it afterwards (see background-job-orchestration).
- - To swap in a second model on the same server, change only the `-m` file and the output name, then rerun the same commands. Gemma 4 E4B QAT Q4_0 is `gemma-4-E4B_q4_0-it.gguf` (5.15 GB, repo `google/gemma-4-E4B-it-qat-q4_0-gguf`). Before the scored run, send one chat request with a system message to confirm the model's chat template builds through the server.
- The llama-cpp-python server handles one request at a time and keeps generating after the client times out. One starved request makes every queued request time out after it. After a run with client timeouts, stop the client, restart the server, and rerun on an idle machine.
