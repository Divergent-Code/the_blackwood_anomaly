import os
import re
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from the .env file
load_dotenv()

# Configure the Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("🚨 ERROR: GOOGLE_API_KEY not found. Please check your .env file.")
    exit(1)

genai.configure(api_key=api_key)

def load_rag_context():
    """Reads the world lore and combat mechanics markdown files."""
    try:
        with open("data/world_lore.md", "r") as lore_file:
            lore = lore_file.read()
        with open("data/combat_mechanics.md", "r") as mechanics_file:
            mechanics = mechanics_file.read()
        return lore, mechanics
    except FileNotFoundError as e:
        print(f"🚨 ERROR: RAG document missing. Ensure your /data folder has the correct files. Details: {e}")
        exit(1)

def build_system_instruction(lore, mechanics):
    """Combines the RAG documents into a strict system prompt for the AI."""
    return f"""
    You are the AI Game Master for a survival horror text adventure called 'The Blackwood Anomaly'.
    You must strictly adhere to the following world lore and mechanics. Do not break character.
    
    === WORLD LORE ===
    {lore}
    
    === COMBAT & SURVIVAL MECHANICS ===
    {mechanics}
    
    === YOUR OUTPUT FORMAT ===
    Respond with atmospheric, terrifying prose describing the outcome of the player's action.
    At the very end of your response, you MUST output the player's current status exactly in this format on a new line:
    [Health: X% | Stress: Y%]
    """

def main():
    print("🌲 Booting The Blackwood Anomaly Engine...")
    
    # 1. Load RAG Context
    lore, mechanics = load_rag_context()
    system_instruction = build_system_instruction(lore, mechanics)
    
    # 2. Initialize the AI Model
    # Using the fast model as requested, perfect for text-based real-time responses
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_instruction
    )
    
    # Start a persistent chat session to remember the conversation history
    chat = model.start_chat(history=[])
    
    # 3. Initial Game State
    health = 100
    stress = 0
    
    print("\n========================================================")
    print("💀 Welcome to Blackwood Sanatorium. Type 'quit' to exit.")
    print("========================================================\n")
    
    # 4. The Core Game Loop
    # We prime the AI to start the game
    initial_prompt = "The game has started. Describe the cold, damp room the player wakes up in. Do not wait for an action yet."
    response = chat.send_message(initial_prompt)
    print(f"\nGame Master: {response.text}\n")
    
    while True:
        # Get player input
        player_action = input("What do you do? > ")
        
        if player_action.lower() in ['quit', 'exit']:
            print("You have abandoned your character to the dark. Goodbye.")
            break
            
        if not player_action.strip():
            print("You stand paralyzed by fear. (Please enter an action).")
            continue
            
        # Send the action to the AI, appending the current state so it knows the math
        action_with_state = f"Player Action: {player_action}\n(Current State - Health: {health}%, Stress: {stress}%)"
        
        try:
            response = chat.send_message(action_with_state)
            ai_text = response.text
            print(f"\nGame Master: {ai_text}\n")
            
            # Simple state extraction using Regex to update our local variables based on AI output
            match = re.search(r"\[Health: (\d+)% \| Stress: (\d+)%\]", ai_text)
            if match:
                health = int(match.group(1))
                stress = int(match.group(2))
                
            if health <= 0:
                print("\n💀 YOU HAVE DIED. GAME OVER.")
                break
                
        except Exception as e:
            print(f"🚨 A system error occurred: {e}")

if __name__ == "__main__":
    main()