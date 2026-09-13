from typing import Optional
from app.core.config import OLLAMA_BASE_URL, OPENROUTER_BASE_URL

def get_llm(llm_provider: str, model_name: str, api_key: Optional[str] = None, temperature: float = 0.2):
    """
    Factory to return the selected LLM wrapper (ChatOllama or ChatOpenAI via OpenRouter).
    """
    if llm_provider == "Ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=model_name,
            temperature=temperature,
            base_url=OLLAMA_BASE_URL
        )
    elif llm_provider == "OpenRouter":
        from langchain_openai import ChatOpenAI
        if not api_key:
            raise ValueError("OpenRouter API key is required.")
        return ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base=OPENROUTER_BASE_URL,
            temperature=temperature,
            default_headers={
                "HTTP-Referer": "https://github.com/google-deepmind/antigravity",
                "X-Title": "Ask-the-Syllabus Bot"
            }
        )
    else:
        raise ValueError(f"Unknown LLM provider: {llm_provider}")
