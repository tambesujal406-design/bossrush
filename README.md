# BossRush

**Turn your own study notes into boss battles.** Paste your notes, and every definition becomes an attack. Right answers damage the boss, wrong answers cost a heart, and the terms you miss come back in a rematch.

<p align="center">
  <img src="Screenshots/notes.png" width="24%"> <img src="Screenshots/fight.png" width="24%"> <img src="Screenshots/combo.png" width="24%"> <img src="Screenshots/victory.png" width="24%">
</p>

## Why I built it
Re-reading notes feels like studying but doesn't stick. Testing yourself works much better, but writing your own quiz takes too long. BossRush makes the quiz for you and turns it into a game, so revising is something you want to do.

## Features
- **Notes to questions, offline:** finds definitions in your notes and makes multiple-choice questions. No AI or internet needed.
- **One boss per subject**, with a 20 second timer per question, combos, crit hits, XP and levels.
- **Rematch weak spots:** fights only the terms you keep missing.
- **Revision sheet:** a printable page of your weak terms with their definitions (save it as PDF).
- **PDF import:** load your professors' notes directly.
- **AI boss:** smarter "understanding" questions using Gemini or Claude.
- **Multiplayer raid:** friends on the same Wi-Fi fight one shared boss.
- **Telegram quiz bot:** 5 quiz polls on your phone, weak spots first, daily if you want.

## Quick start (Windows)
1. Install Python 3.
2. Open a terminal in this folder (type `cmd` in the File Explorer address bar).
3. Run `python app.py`. The game opens in your browser.
4. Press **Try sample notes**, then **Fight a boss**.

No pip install is needed for the basic game.

## Optional setups
| Feature | Setup |
|---|---|
| PDF import | `pip install pypdf` |
| AI boss | Set `GEMINI_API_KEY` (free from Google AI Studio) or `ANTHROPIC_API_KEY`. Change the model with `GEMINI_MODEL` or `CLAUDE_MODEL` if needed. |
| Multiplayer raid | Run `python app.py --lan`. Friends open the address it prints. One person presses **Host raid**, the others press **Join raid**. Only use this on a network you trust. |
| Telegram quiz | Create a bot with @BotFather, set `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID`, then run `python telegram_quiz.py` (or `--daily 18:30`). |

## Writing notes that work well
The generator looks for definition-style lines. You need at least 4.
```
ARP stands for Address Resolution Protocol and it maps an IP address to a MAC address.
DHCP: assigns IP addresses automatically to devices on a network.
A subnet mask is used to split an IP address into network and host parts.
```

## How it works
1. `generator.py` splits notes into sentences and uses regex to find definitions (`X is...`, `X stands for...`, `X: ...`).
2. The term is blanked out to make the question, and other terms from your notes become the wrong options.
3. `app.py` is a small web server built on Python's `http.server`. It stores subjects, notes and hit/miss stats in `data.json`, and runs raids, PDF import and the revision sheet.
4. `index.html` is the game screen (plain HTML, CSS and JavaScript, no frameworks).
5. Rematch picks terms where misses are higher than hits, a simple form of spaced repetition.
6. `ai.py` and `telegram_quiz.py` add the AI boss and the Telegram bot.

## Limits
- Normal mode only understands definition-style sentences (AI boss handles other kinds).
- Raid damage is a flat 10 per hit, with no combos.
- The Telegram bot sends quizzes but doesn't record your answers.

## Ideas for next
Boss rewards and achievements, a spaced-repetition schedule, and a leaderboard across raids.
