import openai
from typing import List, Dict, Any
from app.config import settings
try:
    # Optional profile support. If the profile loader is missing (e.g.,
    # after a revert), we fall back to a built-in default profile.
    from app.services.profile_loader import load_profile  # type: ignore
except Exception:  # pragma: no cover
    load_profile = None  # Fallback handled below

class OpenAIService:
    def __init__(self):
        self.openai_api_key = settings.openai_api_key
        self.model_name = settings.model_name
        self.embedding_model = settings.embedding_model
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature
    
    def _truncate_to_word_limit(self, text: str, max_words: int = 300) -> str:
        """Truncate a text to a maximum number of words without cutting mid-sentence when possible."""
        if not text:
            return text
        words = text.split()
        if len(words) <= max_words:
            return text
        truncated = " ".join(words[:max_words])
        # Try to end on a sentence boundary
        last_period = truncated.rfind(".")
        if last_period >= int(max_words * 0.6):
            return truncated[: last_period + 1]
        return truncated
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key, timeout=30.0)
            response = client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            raise Exception(f"Error generating embeddings: {str(e)}")
    
    async def get_chat_completion(self, messages: List[Dict[str, str]], context: str = "") -> str:
        """Generate a chat completion with optional context"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key, timeout=60.0)
            
            # Create system message with context
            if load_profile is not None:
                try:
                    profile = load_profile()
                except Exception:
                    profile = {}
            else:
                profile = {}

            system_message = {
                "role": "system",
                "content": f"""You are {profile.get('identity', 'a Christian apologetics assistant')}.

Goals:
- """ + "\n- ".join(profile.get("goals", [])) + f"""

Tone/style: {profile.get('tone', {}).get('style', 'clear and warm')}.

Debate style: Use the following structure when helpful: """ + ", ".join(profile.get("debate_style", {}).get("structure", [])) + f""".

Do:
- """ + "\n- ".join(profile.get("do", [])) + f"""

Don't:
- """ + "\n- ".join(profile.get("dont", [])) + f"""

Length policy: at most {profile.get('length_policy', {}).get('max_words', 300)} words (aim {profile.get('length_policy', {}).get('target_range', '280-300')}).

Citations: Bible format {profile.get('citations', {}).get('bible', {}).get('format', 'Book Chapter:Verse')}; Qur'an format {profile.get('citations', {}).get('quran', {}).get('format', 'Surah:Ayah')}.

Context (use faithfully, but do not fabricate):
{context}
"""
            }
            
            # Combine system message with user messages
            full_messages = [system_message] + messages
            
            # Ensure we always allow enough budget for a ~300-word answer
            # by clamping to a safe minimum if an env var is set too low.
            max_tokens_to_use = max(int(self.max_tokens), 480)

            response = client.chat.completions.create(
                model=self.model_name,
                messages=full_messages,
                max_tokens=max_tokens_to_use,
                temperature=self.temperature
            )
            content = response.choices[0].message.content
            return self._truncate_to_word_limit(content, max_words=300)
        except Exception as e:
            raise Exception(f"Error generating chat completion: {str(e)}")
    
    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """Split text into overlapping chunks"""
        if chunk_size is None:
            chunk_size = settings.chunk_size
        if overlap is None:
            overlap = settings.chunk_overlap
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
            
            if start >= len(text):
                break
        
        return chunks 