"""
app.py

This is the main Streamlit application script for the Game Glitch Investigator.
It handles the Web UI, manages user sessions via `st.session_state` (surviving reruns),
and wires up the visual inputs/outputs to the core business logic from `logic_utils.py`.
"""
import random
import streamlit as st
from logic_utils import get_range_for_difficulty, parse_guess, check_guess, update_score

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
    st.session_state.attempts = 0
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

with st.form(key=f"guess_form_{difficulty}"):
    raw_guess = st.text_input(
        "Enter your guess:",
        key=f"guess_input_{difficulty}"  # unique key prevents cross-difficulty state collision
    )

    # Render buttons in a horizontal row to save space
    col1, col2, col3 = st.columns(3)
    with col1:
        submit = st.form_submit_button("Submit Guess 🚀")
    with col2:
        new_game = st.form_submit_button("New Game 🔁")
    with col3:
        # A standalone toggle for the visual hint (the higher/lower arrow)
        show_hint = st.checkbox("Show hint", value=True)

# ---------------------------------------------------------
# New Game Logic
# ---------------------------------------------------------
if new_game:
    st.session_state.attempts = 0
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
        # Step 2: Input valid. Deduct an attempt and record the guess.
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)

        secret = st.session_state.secret

        # Step 3: Check for win / higher / lower
        outcome, message = check_guess(guess_int, secret)

        # Store the feedback for the standalone hint UI
        st.session_state.hint = message

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

if show_hint and st.session_state.hint and st.session_state.status != "won":
    st.warning(st.session_state.hint)

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
