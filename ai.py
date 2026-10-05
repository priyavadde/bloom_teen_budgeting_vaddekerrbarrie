import os

SYSTEM_PROMPT = (
    "You are Bloom AI, a friendly budgeting assistant built into a teen's "
    "budgeting app. A teen is asking whether they should buy something. "
    "Give a short, direct, encouraging answer (3-5 sentences max). "
    "Consider their budget, goals, and whether it's a need or a want. "
    "Be honest if it's a bad idea, but never preachy or judgmental."
)


def ask_gemini(user_message: str, context: str = "") -> str:
    """
    Calls the Gemini API with the user's question plus optional budget context
    (e.g. their current balance, goals, spending). Requires a GEMINI_API_KEY
    environment variable.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return (
            "I'm not connected yet! Ask your developer to set a GEMINI_API_KEY "
            "environment variable so I can actually answer questions."
        )

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-3.8-flash")

        full_prompt = f"{SYSTEM_PROMPT}\n\n{context}\n\nTeen's question: {user_message}"
        response = model.generate_content(full_prompt)
        return response.text.strip()

    except ImportError:
        return (
            "The google-generativeai package isn't installed. Run: "
            "pip install google-generativeai"
        )
    except Exception as e:
        return f"Something went wrong talking to Gemini: {e}"
