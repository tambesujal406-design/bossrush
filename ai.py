"""AI mode: asks Gemini (free tier) or Claude to write smarter questions from your notes."""
import json
import os
import re
import urllib.request

PROMPT = ("From these study notes write {n} multiple-choice exam questions that test understanding, not just recall. "
          "Return ONLY a JSON array. Each item: {{\"q\": text, \"options\": [4 strings], \"answer\": one of the options}}.\n\nNOTES:\n{notes}")


def _post(url, body, headers):
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def generate(notes, n=10):
    prompt = PROMPT.format(n=n, notes=notes[:12000])
    if os.getenv("GEMINI_API_KEY"):
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # change if Google renames it
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={os.environ['GEMINI_API_KEY']}"
        out = _post(url, {"contents": [{"parts": [{"text": prompt}]}]}, {})
        text = out["candidates"][0]["content"]["parts"][0]["text"]
    elif os.getenv("ANTHROPIC_API_KEY"):
        out = _post("https://api.anthropic.com/v1/messages",
                    {"model": os.getenv("CLAUDE_MODEL", "claude-haiku-5-5"), "max_tokens": 3000,
                     "messages": [{"role": "user", "content": prompt}]},
                    {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"})
        text = out["content"][0]["text"]
    else:
        raise RuntimeError("Set GEMINI_API_KEY (free) or ANTHROPIC_API_KEY first. See README.")
    items = json.loads(re.search(r"\[.*\]", text, re.S).group(0))
    return [{"id": "ai:" + it["answer"].lower()[:60], "q": it["q"], "options": it["options"], "answer": it["answer"]}
            for it in items if it.get("answer") in it.get("options", [])]
