import math
import re
import asyncio
from app.llm_provider import LLMProvider

def cosine_similarity(v1, v2):
    """Pure Python dot-product implementation."""
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude_v1 = math.sqrt(sum(a * a for a in v1))
    magnitude_v2 = math.sqrt(sum(b * b for b in v2))
    if magnitude_v1 == 0 or magnitude_v2 == 0:
        return 0.0
    return dot_product / (magnitude_v1 * magnitude_v2)

class RAGEngine:
    def __init__(self):
        self.chunks = []
        self.model_name = "text-embedding-004"
        self.embeddings_cached = {}
        self._lock = asyncio.Lock()
        self._parse_markdown("data/world_lore.md", "LORE")
        self._parse_markdown("data/combat_mechanics.md", "MECHANICS")

    def _parse_markdown(self, filename, prefix):
        """Chunks the markdown files into memory."""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError as e:
            print(f"🚨 WARNING: RAG document missing. {e}")
            return
            
        sections = re.split(r'\n## ', content)
        for i, section in enumerate(sections):
            if not section.strip(): continue
            lines = section.split('\n')
            title = lines[0].strip()
            if i == 0 and not section.startswith('##'):
                title = "Overview"
            title = f"[{prefix}] {title.replace('#', '').strip()}"
            body = '\n'.join(lines[1:]).strip()
            if body:
                self.chunks.append({"title": title, "content": f"{title}\n{body}", "embedding": None})

    async def _ensure_document_embeddings(self, llm: LLMProvider):
        """Lazy-loads document embeddings using the first available user key."""
        provider_name = type(llm).__name__
        if self.embeddings_cached.get(provider_name) or not self.chunks:
            return
            
        async with self._lock:
            # Double check in case another request already populated them while we were waiting for the lock
            if self.embeddings_cached.get(provider_name):
                return
                
            print(f"⚙️ [RAG Engine] Generating knowledge base embeddings via user key ({provider_name})...")
            for chunk in self.chunks:
                chunk[f"embedding_{provider_name}"] = await llm.embed_content(self.model_name, chunk["content"])
                
            self.embeddings_cached[provider_name] = True

    async def retrieve(self, llm: LLMProvider, query: str, top_k=2):
        """Embeds the state-aware query and returns the most relevant rules."""
        await self._ensure_document_embeddings(llm)
        provider_name = type(llm).__name__
        
        # Embed the player's query
        query_embedding = await llm.embed_content(self.model_name, query)
        
        # Calculate similarity
        scored_chunks = []
        for chunk in self.chunks:
            chunk_embedding = chunk.get(f"embedding_{provider_name}")
            if chunk_embedding:
                score = cosine_similarity(query_embedding, chunk_embedding)
                scored_chunks.append((score, chunk))
                
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [c for score, c in scored_chunks[:top_k]]

# Instantiate a single global instance
rag_engine = RAGEngine()
