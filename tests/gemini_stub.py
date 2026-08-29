"""
A stand-in for the Gemini API, used by tests/test_ai_and_auth.py.

The real API needs a key and outbound internet, neither of which is available
in CI. This stub speaks just enough of the protocol to let the tests assert
what actually matters: which prompt the backend built, whether it asked for
search grounding, and how the backend behaves when the API misbehaves.

Run:  python tests/gemini_stub.py [port]
Then: GEMINI_API_BASE=http://127.0.0.1:<port> GEMINI_API_KEY=stub python -m backend.main
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

# Set by the /__control endpoint so a test can make the next call fail.
STATE = {"mode": "ok", "last_prompt": "", "last_had_tools": False, "calls": 0}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep the test output readable

    def _send(self, code, body):
        payload = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path.startswith("/__control"):
            return self._send(200, STATE)
        # Model listing, used by the admin AI-status probe.
        if "?key=" in self.path or self.path.rstrip("/").endswith("models"):
            return self._send(200, {"models": [{"name": "models/gemini-2.5-flash"}]})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path.startswith("/__control"):
            length = int(self.headers.get("Content-Length", 0))
            STATE.update(json.loads(self.rfile.read(length) or b"{}"))
            return self._send(200, STATE)

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")

        prompt = ""
        for part in body.get("contents", [{}])[0].get("parts", []):
            prompt += part.get("text", "")

        STATE["last_prompt"] = prompt
        STATE["last_had_tools"] = "tools" in body
        STATE["calls"] += 1

        mode = STATE.get("mode", "ok")
        # ".../<model>:generateContent?key=..." — take the segment before the
        # colon, whatever prefix the caller used.
        model = self.path.split("?")[0].rstrip("/").split("/")[-1].split(":")[0] or "?"

        if mode == "unauthorized":
            return self._send(403, {"error": {"message": "API key not valid"}})
        if mode == "rate_limited":
            return self._send(429, {"error": {"message": "quota exceeded"}})
        if mode == "model_missing" and model == "gemini-2.5-flash":
            # Force the fallback chain: the first model 404s, the next answers.
            return self._send(404, {"error": {"message": "model not found"}})
        if mode == "no_tools" and "tools" in body:
            return self._send(400, {"error": {"message": "search grounding not enabled for this key"}})

        answer = f"[stub answer from {model}] " + prompt[-120:].replace("\n", " ")
        return self._send(200, {"candidates": [{"content": {"parts": [{"text": answer}]}}]})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8777
    print(f"Gemini stub listening on http://127.0.0.1:{port}", flush=True)
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
