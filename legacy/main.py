import os
import re
import math
from dotenv import load_dotenv
from google import genai

# Load environment variables from the .env file
load_dotenv()

# Configure the Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("🚨 ERROR: GOOGLE_API_KEY not found. Please check your .env file.")
    exit(1)

client = genai.Client(api_key=api_key)

def cosine_similarity(v1, v2):
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude_v1 = math.sqrt(sum(a * a for a in v1))
    magnitude_v2 = math.sqrt(sum(b * b for b in v2))
    if magnitude_v1 == 0 or magnitude_v2 == 0:
        return 0.0
    return dot_product / (magnitude_v1 * magnitude_v2)

class RAGEngine:
    def __init__(self, client: genai.Client):
        self.client = client
        self.chunks = [] # List of dicts: {"title": str, "content": str, "embedding": list}
        self.model_name = "text-embedding-004"
        self._load_and_chunk()
        
    def _parse_markdown(self, filename, prefix):
        chunks = []
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError as e:
            print(f"🚨 ERROR: RAG document missing. {e}")
            exit(1)
            
        # Split by markdown headers
        sections = re.split(r'\n## ', content)
        for i, section in enumerate(sections):
            if not section.strip(): continue
            lines = section.split('\n')
            title = lines[0].strip()
            # Ensure the title has a clean format
            if i == 0 and not section.startswith('##'):
                title = "Overview"
            title = f"[{prefix}] {title.replace('#', '').strip()}"
            body = '\n'.join(lines[1:]).strip()
            if body:
                chunks.append({"title": title, "content": f"{title}\n{body}"})
        return chunks

    def _load_and_chunk(self):
        print("📚 Loading and indexing RAG knowledge base...")
        raw_chunks = []
        raw_chunks.extend(self._parse_markdown("world_lore.md", "LORE"))
        raw_chunks.extend(self._parse_markdown("combat_mechanics.md", "MECHANICS"))
        
        # Cache embeddings
        for chunk in raw_chunks:
            response = self.client.models.embed_content(
                model=self.model_name,
                contents=chunk["content"]
            )
            chunk["embedding"] = response.embeddings[0].values
            self.chunks.append(chunk)
            
    def retrieve(self, query, top_k=2):
        query_response = self.client.models.embed_content(
            model=self.model_name,
            contents=query
        )
        query_embedding = query_response.embeddings[0].values
        
        # Calculate similarity
        scored_chunks = []
        for chunk in self.chunks:
            score = cosine_similarity(query_embedding, chunk["embedding"])
            scored_chunks.append((score, chunk))
            
        # Sort and return
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [c for score, c in scored_chunks[:top_k]]

def build_system_instruction():
    """Provides the base static system prompt for the AI."""
    return """
    You are the AI Game Master for a survival horror text adventure called 'The Blackwood Anomaly'.
    Do not break character. Keep the atmosphere tense and terrifying.
    
    === YOUR OUTPUT FORMAT ===
    Respond with atmospheric, terrifying prose describing the outcome of the player's action.
    At the very end of your response, you MUST output the player's current status exactly in this format on a new line:
    [Health: X% | Stress: Y%]
    """

def main():
    print("🌲 Booting The Blackwood Anomaly Engine...")
    
    # 1. Initialize RAG Engine
    rag_engine = RAGEngine(client)
    
    # 2. Initialize the AI Model
    system_instruction = build_system_instruction()
    # Using the fast model as requested, perfect for text-based real-time responses
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config={"system_instruction": system_instruction}
    )
    
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
            
        # 5. RAG Retrieval Step
        # Formulate a state-aware query
        retrieval_query = f"Player State: {health}% Health, {stress}% Stress. Action: {player_action}"
        retrieved_chunks = rag_engine.retrieve(retrieval_query, top_k=2)
        
        print("\n[RAG Engine] Retrieved Context:")
        context_texts = []
        for chunk in retrieved_chunks:
            print(f"  -> {chunk['title']}")
            context_texts.append(chunk['content'])
            
        rag_context_str = "\n\n".join(context_texts)
        
        # 6. Send the action with retrieved context and state
        action_with_state = f"""
=== RETRIEVED GAME MECHANICS ===
{rag_context_str}

=== PLAYER ACTION ===
(Current State - Health: {health}%, Stress: {stress}%)
Player: {player_action}
"""
        
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