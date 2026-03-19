import json
import anthropic
from config import settings

SYSTEM_PROMPT = """You are a professional social media strategist specializing in Twitter/X.
Generate high-quality tweets that directly serve the user's stated goal.

Rules:
- Each tweet MUST be under 280 characters
- Write in first person, natural and authentic voice
- Vary the formats: some tips, some observations, some questions, some hooks
- Do NOT use generic filler phrases like "Excited to share" or "Thrilled to announce"
- Return ONLY a valid JSON array of strings, no other text
- Example output: ["Tweet one text", "Tweet two text", "Tweet three text"]
"""


def generate_tweets(goal: str, context: str, count: int) -> list[str]:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    user_prompt = f"Goal: {goal}\nAdditional context: {context}\nGenerate exactly {count} distinct tweets."

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw = message.content[0].text.strip()

    try:
        tweets = json.loads(raw)
    except json.JSONDecodeError:
        # Retry once with explicit instruction
        retry_message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": raw},
                {"role": "user", "content": "Return ONLY a valid JSON array. No other text."},
            ],
        )
        tweets = json.loads(retry_message.content[0].text.strip())

    return [t for t in tweets if isinstance(t, str)]
