import json
import re
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


def _extract_json(text: str) -> list:
    """Extract JSON array from text, handling markdown code blocks."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()
    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        return json.loads(match.group(0))
    return json.loads(text)


def generate_tweets(goal: str, context: str, count: int,
                    performance_context: list = None) -> list[str]:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    perf_section = ""
    if performance_context:
        examples = "\n".join(
            f"- {t['content']} (いいね:{t.get('likes', 0)}, RT:{t.get('retweets', 0)})"
            for t in performance_context
        )
        perf_section = f"\n\nHigh-engagement past tweets for style reference:\n{examples}\n"

    user_prompt = (
        f"Goal: {goal}\nAdditional context: {context}"
        f"{perf_section}"
        f"\nGenerate exactly {count} distinct tweets."
    )

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    if not message.content:
        raise ValueError(f"Empty response from API. Stop reason: {message.stop_reason}")
    raw = message.content[0].text.strip()
    if not raw:
        raise ValueError(f"Empty text in response. Stop reason: {message.stop_reason}")

    try:
        tweets = _extract_json(raw)
    except (json.JSONDecodeError, ValueError):
        retry_message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": "["},
            ],
        )
        if not retry_message.content:
            raise ValueError(f"Empty retry response. Stop reason: {retry_message.stop_reason}")
        retry_raw = retry_message.content[0].text.strip()
        if not retry_raw:
            raise ValueError(f"Empty retry text. Stop reason: {retry_message.stop_reason}")
        tweets = json.loads("[" + retry_raw)

    return [t for t in tweets if isinstance(t, str)]
