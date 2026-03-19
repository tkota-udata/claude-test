import tweepy
from config import settings
from datetime import datetime, timezone


def get_client() -> tweepy.Client:
    return tweepy.Client(
        consumer_key=settings.twitter_api_key,
        consumer_secret=settings.twitter_api_secret,
        access_token=settings.twitter_access_token,
        access_token_secret=settings.twitter_access_token_secret,
    )


def post_tweet(content: str) -> dict:
    client = get_client()
    response = client.create_tweet(text=content)
    tweet_id = str(response.data["id"])
    posted_at = datetime.now(timezone.utc).isoformat()
    # Derive username for URL (use a placeholder if lookup fails)
    try:
        me = client.get_me()
        username = me.data.username
    except Exception:
        username = "i"
    return {
        "tweet_id": tweet_id,
        "url": f"https://x.com/{username}/status/{tweet_id}",
        "posted_at": posted_at,
    }
