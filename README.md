# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the broken app: `python -m streamlit run app.py`

## 🕵️‍♂️ Your Mission

1. **Play the game.** Open the "Developer Debug Info" tab in the app to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*
3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

- [ ] Describe the game's purpose.
- [ ] Detail which bugs you found.
- [ ] Explain what fixes you applied.

## 📸 Demo

- [ ] [Insert a screenshot of your fixed, winning game here]
- [ ] [Insert a screenshot of the pytest command and passing tests here]

## 🚀 Challenge 4: Stretch Features (Agent Mode Feature)

A **Game Session Summary Table** and an **Interactive Hot/Cold Tracker** were added to give the player a more visual, user-friendly experience.

### What it does
- Choose to enable **🌡️ Hot/Cold Hints** in the sidebar. When enabled, your hints are replaced with temperatures (e.g., 🔥 Boiling, ❄️ Freezing) based on how close you are to the secret number.
- The color of the hint message dynamically changes based on your temperature!
- When the game ends, a **📊 Game Summary Table** is displayed showing a timeline of all your guesses, temps, and hints.

### 📸 Demo

- [ ] [Insert a screenshot of your shiny new 📊 Game Summary Table and 🌡️ Hot/Cold hints here!]

---

## 🏆 Challenge 3: High Score Tracker (Agent Mode Feature)

A persistent **High Score leaderboard** was added as part of the Agent Mode challenge.

### What it does
- After winning a game, your score is automatically saved to `high_scores.json`.
- The sidebar shows a live **Top 5 leaderboard** for whichever difficulty level you are currently playing.
- If you set the #1 score, the win message displays a **🏆 New high score!** banner.
- Scores are tracked **per difficulty** (Easy, Normal, Hard, I'm Feeling Lucky).

### Files changed
| File | What changed |
|---|---|
| `logic_utils.py` | Added `load_high_scores()` and `save_high_score()` |
| `app.py` | Imports new helpers, renders sidebar leaderboard, saves score on win |
| `tests/test_game_logic.py` | Added 3 new tests for high score persistence |

### How the Agent contributed
**Antigravity AI Agent** (Google DeepMind) was used in Agent Mode to:
1. **Plan the feature** — the agent proposed the architecture, recommending that persistence logic live in `logic_utils.py` so it stays testable independently of the Streamlit UI.
2. **Write the code** — the agent implemented `load_high_scores`, `save_high_score`, all sidebar UI changes in `app.py`, and the new pytest cases.
3. **Verify correctness** — the agent ran `python -m pytest` after each change and confirmed all 9 tests pass.
