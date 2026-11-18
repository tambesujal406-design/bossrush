"""Turns plain study notes into multiple-choice boss questions. No AI, no internet.

Idea: notes are full of definitions ("TCP is a ...", "ARP stands for ...", "DHCP: assigns ...").
1. split the notes into sentences
2. keep sentences that look like definitions (regex)
3. blank out the term  ->  question
4. use other terms from the same notes as wrong options  ->  distractors
"""
import re
import random

DEF = re.compile(r"^(?P<term>[A-Za-z][\w\s\-/()]{1,40}?)\s+(?:is|are|means|refers to|stands for|is called)\s+(?P<rest>.{15,})$")
COLON = re.compile(r"^(?P<term>[A-Za-z][\w\s\-/()]{1,40}?)\s*[:\-\u2013]\s+(?P<rest>.{15,})$")
BAD = {"it", "this", "that", "these", "those", "there", "they", "which", "he", "she", "we", "you",
       "what", "who", "note", "example", "answer", "definition", "key", "remember", "tip", "eg", "ie"}


def split_sentences(text):
    out = []
    for line in text.splitlines():
        line = line.strip(" \t\u2022*-\u2013\u00b7#")
        for s in re.split(r"(?<=[.!?])\s+", line):
            s = s.strip()
            if len(s.split()) >= 5:
                out.append(s)
    return out


def extract_definitions(text):
    found, seen = [], set()
    for s in split_sentences(text):
        s = s.rstrip(".")
        m = DEF.match(s) or COLON.match(s)
        if not m:
            continue
        term = re.sub(r"^(the|a|an)\s+", "", m.group("term").strip(" -:"), flags=re.I)
        words = term.split()
        if not words or len(words) > 5 or words[0].lower() in BAD:
            continue
        if term.lower() in seen:
            continue
        seen.add(term.lower())
        found.append((term, s))
    return found


def build_questions(text, limit=10, seed=None):
    rnd = random.Random(seed)
    defs = extract_definitions(text)
    terms = [t for t, _ in defs]
    questions = []
    for term, sentence in defs:
        others = [t for t in terms if t.lower() != term.lower()]
        if len(others) < 3:
            continue
        options = rnd.sample(others, 3) + [term]
        rnd.shuffle(options)
        stem = re.sub(re.escape(term), "_____", sentence, count=1, flags=re.I)
        questions.append({"id": term.lower(), "q": stem, "options": options, "answer": term})
    rnd.shuffle(questions)
    return questions[:limit]
