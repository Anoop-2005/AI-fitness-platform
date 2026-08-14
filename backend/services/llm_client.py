from config import GROQ_API_KEY, GOOGLE_API_KEY

MOCK_MODE = not (GROQ_API_KEY or GOOGLE_API_KEY)

class LLMUnavailableError(Exception):
    """Raised when the AI provider can't be reached (rate limit, network, etc)."""
    pass

def _get_llm():
    if GROQ_API_KEY:
        from langchain_groq import ChatGroq
        return ChatGroq(model="openai/gpt-oss-20b", api_key=GROQ_API_KEY, temperature=0.4)
    if GOOGLE_API_KEY:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model="gemini-3.5-flash", google_api_key=GOOGLE_API_KEY, temperature=0.4)
    return None


def chat(prompt: str) -> str:
    if MOCK_MODE:
        return "[MOCK MODE — set GROQ_API_KEY or GOOGLE_API_KEY in .env for real AI text]"
    try:
        llm = _get_llm()
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        raise LLMUnavailableError(str(e)) from e
        #return f"[Could not reach the AI provider right now: {e}]"
