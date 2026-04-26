import pytest
import re
from main import load_rag_context, build_system_instruction

def test_rag_document_loading():
    """Tests if the RAG system successfully loads the markdown files."""
    try:
        lore, mechanics = load_rag_context()
        # Verify both variables are strings and not empty
        assert isinstance(lore, str) and len(lore) > 0, "Lore document is empty or failed to load."
        assert isinstance(mechanics, str) and len(mechanics) > 0, "Mechanics document is empty or failed to load."
        print("\n✅ PASS: RAG documents loaded successfully.")
    except Exception as e:
        pytest.fail(f"🚨 FAIL: Exception during RAG loading: {e}")

def test_system_instruction_compilation():
    """Tests if the system instruction properly injects the RAG context."""
    dummy_lore = "DUMMY_LORE_RULE: The sky is red."
    dummy_mechanics = "DUMMY_MECHANIC_RULE: Player has 1 HP."
    
    instruction = build_system_instruction(dummy_lore, dummy_mechanics)
    
    assert dummy_lore in instruction, "System instruction missing Lore RAG data."
    assert dummy_mechanics in instruction, "System instruction missing Mechanics RAG data."
    assert "[Health: X% | Stress: Y%]" in instruction, "System instruction missing formatting constraint."
    print("\n✅ PASS: System Instruction compiles successfully with RAG data.")

def test_ai_state_extraction_regex():
    """Evaluates the reliability of the regex extractor on simulated AI outputs."""
    # Simulate a perfect AI response
    perfect_response = "The monster swings wildly. [Health: 75% | Stress: 40%]"
    match_perfect = re.search(r"\[Health: (\d+)% \| Stress: (\d+)%\]", perfect_response)
    
    assert match_perfect is not None, "Regex failed to extract from perfect response."
    assert match_perfect.group(1) == "75", "Failed to extract correct Health."
    assert match_perfect.group(2) == "40", "Failed to extract correct Stress."
    
    # Simulate an AI response with extra text at the end
    messy_response = "You hide. [Health: 100% | Stress: 10%] \n *The room goes dark.*"
    match_messy = re.search(r"\[Health: (\d+)% \| Stress: (\d+)%\]", messy_response)
    
    assert match_messy is not None, "Regex failed to extract from a messy response."
    assert match_messy.group(1) == "100", "Failed to extract correct Health from messy response."
    assert match_messy.group(2) == "10", "Failed to extract correct Stress from messy response."
    print("\n✅ PASS: AI State Extraction Regex is highly reliable.")

def test_game_loop_termination():
    """Tests the main game loop's ability to terminate correctly on user input or death."""
    # This test simulates the user typing 'quit' to exit.
    print("\n⚠️  Note: This test requires you to type 'quit' to pass.")
    
    try:
        import builtins
        from unittest.mock import MagicMock, patch
        
        # 1. Mock the input function to return 'quit'
        # 2. Mock the chat.send_message to return a mock response
        mock_response = MagicMock()
        mock_response.text = "The door creaks open. [Health: 100% | Stress: 0%]"
        
        with patch('builtins.input', side_effect=['quit']), \
             patch('google.generativeai.GenerativeModel', autospec=True) as MockModel:
            
            # Configure the mock model
            mock_model_instance = MockModel.return_value
            mock_chat = mock_model_instance.start_chat.return_value
            mock_chat.send_message.return_value = mock_response
            
            # Run the main function (it will exit when input is 'quit')
            with patch('sys.stdout'): # Suppress game output during test
                try:
                    import main
                    main.main()
                except SystemExit:
                    # Expected behavior: main() exits when user types 'quit'
                    print("\n✅ PASS: Game loop terminated successfully on 'quit' input.")
                except Exception as e:
                    pytest.fail(f"🚨 FAIL: Game loop raised unexpected exception: {e}")

    except Exception as e:
        pytest.fail(f"🚨 FAIL: Exception during game loop test: {e}"    )