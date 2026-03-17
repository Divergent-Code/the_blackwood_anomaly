"""
app.py

This is the main Streamlit application script for the Game Glitch Investigator.
It handles the Web UI, manages user sessions via `st.session_state` (surviving reruns),
and wires up the visual inputs/outputs to the core business logic from `logic_utils.py`.
"""
import random
import streamlit as st
from logic_utils import (
    get_range_for_difficulty, parse_guess, check_guess, 
    update_score, load_high_scores, save_high_score, calculate_temperature
)

# File path for persisting high scores between sessions (Agent-assisted feature)
HIGH_SCORES_FILE = "high_scores.json"

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

# ---------------------------------------------------------
# Sidebar Configuration: Difficulty Settings
# ---------------------------------------------------------
st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard", "I'm Feeling Lucky"],
    index=0,  # Defaults to "Easy" on first load
)

# Map human-readable difficulty levels to raw attempt counts
attempt_limit_map = {
    "Easy": 15,
    "Normal": 10,
    "Hard": 5,
    "I'm Feeling Lucky": 1,
}
attempt_limit = attempt_limit_map[difficulty]

# Fetch the random number generation range based on current difficulty
low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

# Toggle for Hint Systems
st.sidebar.divider()
st.sidebar.subheader("💡 Hint Systems")
show_higher_lower = st.sidebar.checkbox("📈 Show Higher/Lower", value=True, help="Standard text telling you if the secret is higher or lower than your guess.")
show_hot_cold = st.sidebar.checkbox("🌡️ Show Hot/Cold", value=False, help="Color-coded temperature hints based on proximity to the secret.")

# ---------------------------------------------------------
# Sidebar: High Score Leaderboard (Agent-assisted feature)
# The agent suggested reading the file on every render so the
# leaderboard always reflects the latest saved data without
# requiring a manual refresh or extra session state.
# ---------------------------------------------------------
st.sidebar.divider()
st.sidebar.subheader("🏆 High Scores")
_hs = load_high_scores(HIGH_SCORES_FILE)
_scores_for_difficulty = _hs.get(difficulty, [])
if _scores_for_difficulty:
    for _rank, _pts in enumerate(_scores_for_difficulty, start=1):
        medal = ["🥇", "🥈", "🥉"][_rank - 1] if _rank <= 3 else f"{_rank}."
        st.sidebar.caption(f"{medal} {_pts} pts")
else:
    st.sidebar.caption("No scores yet — win a game!")

# ---------------------------------------------------------
# Application State Management
# ---------------------------------------------------------
# Streamlit relies on "rerunning" the entire script every time a user interacts
# with a widget (like clicking a button or pressing enter in a text box).
# `st.session_state` allows variables to persist across these constant reruns.

# Initialize or reset the entire game state when the app first loads
# or when the user changes the difficulty level.
if st.session_state.get("difficulty") != difficulty:
    st.session_state.difficulty = difficulty
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 1
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.new_game_started = False
    st.session_state.history = []
    st.session_state.hint = None
# ---------------------------------------------------------
# Main UI Layout
# ---------------------------------------------------------
st.subheader("Make a guess")

# Display the "New game started." message if it was flagged before a rerun
if st.session_state.new_game_started:
    st.success("New game started.")
    # Reset the flag so it only shows once
    st.session_state.new_game_started = False

st.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts used:", st.session_state.attempts)
    st.write("Attempts remaining:", attempt_limit - st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("Guess History:", st.session_state.history)

# We use st.form here to group the input and buttons together.
# This ensures that pressing the "Enter" key inside the text input 
# correctly triggers the form submission, identical to clicking the button.
with st.form(key=f"guess_form_{difficulty}", clear_on_submit=True):
    raw_guess = st.text_input(
        "Enter your guess:",
        key=f"guess_input_{difficulty}"  # unique key prevents cross-difficulty state collision
    )

    # Render buttons in a horizontal row to save space
    col1, col2 = st.columns(2)
    with col1:
        submit = st.form_submit_button("Submit Guess 🚀")
    with col2:
        new_game = st.form_submit_button("New Game 🔁")

# ---------------------------------------------------------
# New Game Logic
# ---------------------------------------------------------
if new_game:
    st.session_state.attempts = 1
    st.session_state.secret = random.randint(low, high)
    st.session_state.hint = None
    st.session_state.status = "playing"
    st.session_state.score = 0
    st.session_state.history = []
    
    # Flag that a new game just started so the success message survives the rerun
    st.session_state.new_game_started = True
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

# ---------------------------------------------------------
# Main Game Loop (Processing a Guess)
# ---------------------------------------------------------
if submit:
    # Step 1: Validate input. Returns (True/False, integer, error/None)
    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        # Halt processing sequence: Show error but don't cost the user an attempt
        st.error(err)
    else:
        # Retrieve secret before using it
        secret = st.session_state.secret
        outcome, message = check_guess(guess_int, secret)

        # Calculate temperatures
        temp_emoji, temp_label, temp_color = calculate_temperature(guess_int, secret, high - low)

        # Build the hint display based on user preferences
        hint_parts = []
        if show_hot_cold:
            hint_parts.append(f"{temp_emoji} **{temp_label}**")
        if show_higher_lower:
            hint_parts.append(message)
            
        if hint_parts:
            hint_display = " — ".join(hint_parts)
        else:
            hint_display = None  # User disabled all hints

        # Step 2: Input valid. Deduct an attempt and record the guess.
        st.session_state.attempts += 1
        st.session_state.history.append({
            "Attempt": st.session_state.attempts,
            "Guess": guess_int,
            "Hint": message if show_higher_lower else "Hidden",
            "Temperature": f"{temp_emoji} {temp_label}" if show_hot_cold else "Hidden"
        })

        # Store the formatted feedback for the standalone hint UI
        st.session_state.hint = hint_display
        st.session_state.hint_color = temp_color if show_hot_cold else "warning"

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
            difficulty=difficulty
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            # Persist the final score to the leaderboard file
            updated_scores = save_high_score(HIGH_SCORES_FILE, difficulty, st.session_state.score)
            is_top = updated_scores[0] == st.session_state.score and updated_scores.count(st.session_state.score) == 1
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
                + (" 🏆 New high score!" if is_top else "")
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

if st.session_state.hint and st.session_state.status != "won":
    # Render different alert box colors based on the temperature if enabled
    hint_color = st.session_state.get("hint_color", "warning")
    if hint_color == "error":
        st.error(st.session_state.hint)
    elif hint_color == "info":
        st.info(st.session_state.hint)
    else:
        st.warning(st.session_state.hint)

# Show the structured Game Summary table when the game ends
if st.session_state.status != "playing" and len(st.session_state.history) > 0:
    st.divider()
    st.subheader("📊 Game Summary")
    # Tell Streamlit to draw a sleek, interactive dataframe
    st.dataframe(
        st.session_state.history,
        use_container_width=True,
        hide_index=True
    )

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
