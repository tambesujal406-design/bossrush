"""BossRush server. Standard library only. Optional: pypdf (PDF import), an API key (AI mode)."""
import base64
import io
import json
import os
import re
import socket
import sys
import threading
import webbrowser
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import ai
from generator import build_questions, extract_definitions

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "data.json")  # subjects, notes and hit/miss stats
LOCK = threading.Lock()
RAID = None  # the running multiplayer raid lives in memory


def load():
    try:
        with open(DB, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        d = {}
    d.setdefault("stats", {})
    if "subjects" not in d:  # upgrade from the old single-notes format
        d["subjects"] = {"General": d.pop("notes", "")}
    return d


def save(data):
    with open(DB, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def sheet(data):
    items = ""
    for notes in data["subjects"].values():
        for term, sentence in extract_definitions(notes):
            s = data["stats"].get(term.lower())
            if s and s["miss"] > 0:
                items += f"<li><b>{escape(term)}</b> <small>missed {s['miss']}x</small><p>{escape(sentence)}.</p></li>"
    body = items or "<p>No weak spots yet. Fight a few bosses first.</p>"
    return ("<!doctype html><meta charset=utf-8><title>BossRush revision sheet</title>"
            "<style>body{font:18px/1.5 Georgia,serif;max-width:720px;margin:30px auto;padding:0 16px}"
            "li{margin-bottom:14px;break-inside:avoid}p{margin:2px 0}small{color:#a00}</style>"
            f"<h1>My weak spots</h1><ol>{body}</ol><script>onload=()=>print()</script>").encode()


class Handler(BaseHTTPRequestHandler):
    def reply(self, code, body, ctype="application/json"):
        if not isinstance(body, bytes):
            body = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        args = parse_qs(url.query)
        data = load()
        if url.path == "/":
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                return self.reply(200, f.read(), "text/html; charset=utf-8")
        if url.path == "/sheet":
            return self.reply(200, sheet(data), "text/html; charset=utf-8")
        if url.path == "/api/data":
            return self.reply(200, {"subjects": data["subjects"]})
        if url.path == "/api/start":
            mode = args.get("mode", ["normal"])[0]
            count = int(args.get("n", ["10"])[0])
            notes = data["subjects"].get(args.get("subject", ["General"])[0], "")
            if mode == "ai":
                try:
                    return self.reply(200, {"questions": ai.generate(notes, count)})
                except Exception as e:
                    return self.reply(200, {"questions": [], "error": f"AI mode failed: {e}"})
            qs = build_questions(notes, limit=999)
            if mode == "rematch":  # only the terms you keep getting wrong
                qs = [q for q in qs if data["stats"].get(q["id"], {}).get("miss", 0)
                      > data["stats"].get(q["id"], {}).get("hit", 0)]
            return self.reply(200, {"questions": qs[:count]})
        if url.path == "/api/stats":
            weak = [{"term": s.get("term", k), "miss": s["miss"], "hit": s["hit"]}
                    for k, s in data["stats"].items() if s["miss"] > 0]
            weak.sort(key=lambda w: w["miss"] - w["hit"], reverse=True)
            return self.reply(200, {"weak": weak[:8]})
        if url.path == "/api/raid":
            if RAID is None:
                return self.reply(200, {"active": False})
            players = sorted(({"name": n, "dmg": d} for n, d in RAID["players"].items()), key=lambda p: -p["dmg"])
            return self.reply(200, {"active": True, "hp": RAID["hp"], "max": RAID["max"], "players": players,
                                    "questions": RAID["qs"], "subject": RAID["subject"]})
        self.reply(404, {"error": "not found"})

    def do_POST(self):
        global RAID
        url = urlparse(self.path)
        size = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(size) or b"{}")
        data = load()
        if url.path == "/api/notes":
            subject = body.get("subject", "General")
            data["subjects"][subject] = body.get("notes", "")
            save(data)
            return self.reply(200, {"questions": len(build_questions(data["subjects"][subject], limit=999))})
        if url.path == "/api/answer":
            stat = data["stats"].setdefault(body["id"], {"hit": 0, "miss": 0, "term": body.get("term", "")})
            stat["hit" if body.get("correct") else "miss"] += 1
            save(data)
            return self.reply(200, {"ok": True})
        if url.path == "/api/pdf":
            try:
                from pypdf import PdfReader
            except ImportError:
                return self.reply(200, {"error": "PDF import needs one install: pip install pypdf"})
            try:
                reader = PdfReader(io.BytesIO(base64.b64decode(body["data"])))
                text = "\n".join(p.extract_text() or "" for p in reader.pages)
            except Exception as e:
                return self.reply(200, {"error": f"Could not read this PDF: {e}"})
            text = re.sub(r"(?<![.!?:])\n(?=[a-z])", " ", text)  # re-join lines that PDFs break mid-sentence
            return self.reply(200, {"text": text})
        if url.path == "/api/raid/start":
            subject = body.get("subject", "General")
            qs = build_questions(data["subjects"].get(subject, ""), limit=10)
            if not qs:
                return self.reply(200, {"error": "Add at least 4 definition lines to this subject first."})
            with LOCK:
                RAID = {"qs": qs, "max": 15 * len(qs), "hp": 15 * len(qs), "players": {}, "subject": subject}
            return self.reply(200, {"ok": True})
        if url.path == "/api/raid/hit" and RAID:
            dmg = min(int(body.get("dmg", 0)), 10)
            with LOCK:
                RAID["hp"] -= dmg
                RAID["players"][body["name"]] = RAID["players"].get(body["name"], 0) + dmg
            return self.reply(200, {"ok": True})
        self.reply(404, {"error": "not found"})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = 8000
    lan = "--lan" in sys.argv  # python app.py --lan  -> friends on your Wi-Fi can join a raid
    if lan:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except OSError:
            ip = "your-pc-ip"
        print(f"RAID MODE: friends on your Wi-Fi open http://{ip}:{port}")
    print(f"BossRush running at http://localhost:{port}  (Ctrl+C to stop)")
    webbrowser.open(f"http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0" if lan else "127.0.0.1", port), Handler).serve_forever()
