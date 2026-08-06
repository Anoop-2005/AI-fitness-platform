"""
Talks to Groq or Gemini via LangChain's chat model wrappers. Both are free-
tier providers; whichever API key is set in .env is used (Groq preferred
if both are set, since it's faster).

If no API key is set, `chat()` returns a clearly-labeled placeholder so the
rest of the app still works end to end with zero signup.
"""
from config import GROQ_API_KEY, GOOGLE_API_KEY

MOCK_MODE = not (GROQ_API_KEY or GOOGLE_API_KEY)


def _get_llm():
    if GROQ_API_KEY:
        from langchain_groq import ChatGroq
        return ChatGroq(model="llama-3.1-8b-instant", api_key=GROQ_API_KEY, temperature=0.4)
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
        return f"[Could not reach the AI provider right now: {e}]"
