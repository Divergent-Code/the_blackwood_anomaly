import pytest
import re
import math
from main import cosine_similarity, build_system_instruction

def test_cosine_similarity():
    """Tests the pure-Python cosine similarity math logic."""
    # Identical vectors should have a similarity of 1.0
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert math.isclose(cosine_similarity(v1, v2), 1.0), "Identical vectors failed."
    
    # Orthogonal (unrelated) vectors should have a similarity of 0.0
    v3 = [0.0, 1.0, 0.0]
    assert math.isclose(cosine_similarity(v1, v3), 0.0), "Orthogonal vectors failed."
    
    # Opposite vectors should have a similarity of -1.0
    v4 = [-1.0, 0.0, 0.0]
    assert math.isclose(cosine_similarity(v1, v4), -1.0), "Opposite vectors failed."
    print("\n✅ PASS: Cosine similarity math is perfectly accurate.")

def test_system_instruction_compilation():
    """Tests if the static system instruction compiles correctly."""
    instruction = build_system_instruction()
    
    assert "The Blackwood Anomaly" in instruction, "System instruction missing title."
    assert "[Health: X% | Stress: Y%]" in instruction, "System instruction missing formatting constraint."
    print("\n✅ PASS: System Instruction compiles successfully.")

def test_ai_state_extraction_regex():
    """Evaluates the reliability of the regex extractor on simulated AI outputs."""
    # Simulate a perfect AI response
    perfect_response = "The monster swings wildly. [Health: 75% | Stress: 40%]"
    match_perfect = re.search(r"\[Health: (\d+)% \| Stress: (\d+)%\]", perfect_response)
    
    assert match_perfect is not None, "Regex failed to extract from perfect response."
    assert match_perfect.group(1) == "75", "Failed to extract correct Health."
    assert match_perfect.group(2) == "40", "Failed to extract correct Stress."
    
    # Simulate an AI response with extra text or formatting at the end
    messy_response = "You hide. [Health: 100% | Stress: 10%] \n *The room goes dark.*"
    match_messy = re.search(r"\[Health: (\d+)% \| Stress: (\d+)%\]", messy_response)
    
    assert match_messy is not None, "Regex failed to extract from a messy response."
    assert match_messy.group(1) == "100", "Failed to extract Health from messy response."
    assert match_messy.group(2) == "10", "Failed to extract Stress from messy response."
    print("\n✅ PASS: AI State Extraction Regex is highly reliable.")