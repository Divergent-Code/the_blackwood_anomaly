def get_range_for_difficulty(difficulty: str) -> tuple[int, int]:
    """Retrieve the inclusive minimum and maximum range for a given difficulty.

    The range dictates the possible values for the secret number. Wider ranges
    make the game harder as there are more possibilities for the player to guess.

    Args:
        difficulty (str): The difficulty level selected by the user. Expected
            values are "Easy", "Normal", "Hard", or "I'm Feeling Lucky".

    Returns:
        tuple[int, int]: A tuple containing the (low, high) bounds for the secret.
            Defaults to (1, 100) if an unknown difficulty is provided.
    """
    ranges = {
        "Easy": (1, 20),
        "Normal": (1, 100),
        "Hard": (1, 200),
        "I'm Feeling Lucky": (1, 200)
    }
    return ranges.get(difficulty, (1, 100))


def parse_guess(raw: str) -> tuple[bool, int | None, str | None]:
    """Parse and validate raw user input into an integer guess.

    This function handles input validation before an attempt is consumed.
    It rejects empty inputs and decimals, providing specific error messages
    so the UI can guide the user without crashing or penalizing them.

    Args:
        raw (str): The raw string input provided by the user from the text box.

    Returns:
        tuple[bool, int | None, str | None]: A 3-tuple containing:
            - ok (bool): True if the guess is a valid integer, False otherwise.
            - guess_int (int | None): The parsed integer if valid, else None.
            - error_message (str | None): A user-facing error string if invalid, else None.
    """
    if not raw:
        return False, None, "Enter a guess."

    if "." in raw:
        return False, None, "Please enter a whole number, not a decimal."

    try:
        value = int(raw)
        return True, value, None
    except ValueError:
        return False, None, "That is not a number."


def check_guess(guess: int, secret: int) -> tuple[str, str]:
    """Compare the player's guess to the secret number and determine the outcome.

    Evaluates whether the guess is exactly correct, too high, or too low,
    and provides a formatted hint message suitable for display in the UI.

    Args:
        guess (int): The integer value guessed by the player.
        secret (int): The actual secret number they are trying to guess.

    Returns:
        tuple[str, str]: A 2-tuple containing:
            - outcome (str): A string indicating "Win", "Too High", or "Too Low".
            - message (str): A user-facing hint (e.g., "🎯 Correct!", "📉 Go LOWER!").
    """
    if guess == secret:
        return "Win", "🎯 Correct!"
    elif guess > secret:
        return "Too High", "📉 Go LOWER!"
    return "Too Low", "📈 Go HIGHER!"


def calculate_temperature(guess: int, secret: int, limit: int) -> tuple[str, str, str]:
    """Calculate the proximity of a guess to the secret number.

    Returns an emoji, string modifier, and color to display based on the absolute
    distance between the guess and the secret. The thresholds scale with the 
    maximum range limit to provide consistent feel across difficulty levels.

    Args:
        guess (int): The integer value guessed by the player.
        secret (int): The actual secret number.
        limit (int): The maximum possible number (e.g., 20, 100, 200).

    Returns:
        tuple[str, str, str]: A 3-tuple containing:
            - emoji (str): A relevant icon (e.g., "🔥", "🧊")
            - label (str): The textual temperature label (e.g., "Boiling", "Freezing")
            - color (str): The Streamlit alert color ("error", "warning", "info")
    """
    distance = abs(guess - secret)
    # Define thresholds as percentages of the total limit
    if distance <= max(1, limit * 0.05):
        return "🔥", "Boiling!", "error"  # Red
    elif distance <= max(3, limit * 0.15):
        return "☀️", "Hot!", "warning" # Yellow
    elif distance <= max(8, limit * 0.30):
        return "❄️", "Cold", "info"    # Blue
    else:
        return "🧊", "Freezing", "info" # Blue




def update_score(
    current_score: int,
    outcome: str,
    attempt_number: int,
    difficulty: str = "Normal"
) -> int:
    """Calculate and update the player's score based on the outcome of a guess.

    The scoring system rewards efficiency (fewer attempts). Harder difficulties
    apply a higher multiplier to the base score. Incorrect guesses do not
    actively deduct points from the current total to prevent double penalties.

    Args:
        current_score (int): The player's score before this attempt is evaluated.
        outcome (str): The result of the guess (e.g., "Win", "Too High").
        attempt_number (int): The number of attempts taken so far, including this one.
        difficulty (str, optional): The current game difficulty setting.
            Defaults to "Normal".

    Returns:
        int: The updated integer score. If the outcome is not "Win", this
            is identical to the `current_score`.
    """
    if outcome == "Win":
        base_points = max(10, 100 - 10 * attempt_number)
        multipliers = {
            "Easy": 1.0,
            "Normal": 2.0,
            "Hard": 5.0,
            "I'm Feeling Lucky": 10.0
        }
        multiplier = multipliers.get(difficulty, 1.0)
        return current_score + int(base_points * multiplier)

    return current_score


# ---------------------------------------------------------------
# High Score Persistence (Agent-assisted feature)
#
# These two functions were designed and implemented with the help
# of Antigravity AI Agent during the Phase 3 challenge. The agent
# identified that separating persistence from the UI layer (app.py)
# makes both halves independently testable.
# ---------------------------------------------------------------

import json
import os

def load_high_scores(filepath: str) -> dict[str, list[int]]:
    """Load the high scores dictionary from a persistent JSON file.

    Reads the specified JSON file and parses the high scores. If the file
    does not exist, is unreadable, or contains invalid JSON, it fails safely
    and returns an empty dictionary.

    Args:
        filepath (str): The relative or absolute path to the JSON file.

    Returns:
        dict[str, list[int]]: A dictionary mapping difficulty levels (str)
            to lists of integer scores descending, e.g.:
            {"Easy": [90, 70, 50], "Normal": [180, 160]}.
    """
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def save_high_score(filepath: str, difficulty: str, score: int) -> list[int]:
    """Insert a new score into the leaderboard and persist to disk.

    Adds the provided score to the specified difficulty's leaderboard, sorts
    the leaderboard in descending order, crops it to the top 5 scores, and
    writes the entire updated dictionary back to the JSON file.

    Args:
        filepath (str): The relative or absolute path to the JSON file.
        difficulty (str): The difficulty bucket to insert the score into.
        score (int): The integer score achieved by the player.

    Returns:
        list[int]: The newly updated top-5 score list for the given difficulty,
            useful for immediately rendering UI updates without reloading.
    """
    scores = load_high_scores(filepath)
    bucket = scores.get(difficulty, [])
    bucket.append(score)

    bucket = sorted(bucket, reverse=True)[:5]
    scores[difficulty] = bucket

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(scores, file, indent=2)

    return bucket