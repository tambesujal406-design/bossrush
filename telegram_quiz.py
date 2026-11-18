"""Sends 5 quiz polls to your Telegram (weak spots first).
Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID, then: python telegram_quiz.py   or   python telegram_quiz.py --daily 18:30"""
import datetime
import json
import os
import sys
import time
import urllib.request

from app import load
from generator import build_questions

TOKEN, CHAT = os.getenv("TELEGRAM_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")


def send_quiz():
    data = load()
    qs = []
    for notes in data["subjects"].values():
        qs += build_questions(notes, limit=999)
    weak = {k for k, s in data["stats"].items() if s["miss"] > s["hit"]}
    qs.sort(key=lambda q: q["id"] not in weak)  # weak spots first
    for q in qs[:5]:
        body = {"chat_id": CHAT, "question": q["q"][:300], "options": [o[:100] for o in q["options"]],
                "type": "quiz", "correct_option_id": q["options"].index(q["answer"]), "is_anonymous": False}
        urllib.request.urlopen(urllib.request.Request(
            f"https://api.telegram.org/bot{TOKEN}/sendPoll", json.dumps(body).encode(),
            {"Content-Type": "application/json"}))
    print(f"Sent {min(5, len(qs))} questions.")


if __name__ == "__main__":
    if not (TOKEN and CHAT):
        sys.exit("Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID first (see README).")
    if "--daily" in sys.argv:
        hh, mm = map(int, sys.argv[sys.argv.index("--daily") + 1].split(":"))
        while True:
            now = datetime.datetime.now()
            target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
            if target <= now:
                target += datetime.timedelta(days=1)
            time.sleep((target - now).total_seconds())
            send_quiz()
    else:
        send_quiz()
