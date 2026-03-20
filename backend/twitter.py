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


def get_tweet_metrics(tweet_id: str) -> dict:
    """Fetch public metrics for a tweet."""
    client = get_client()
    response = client.get_tweet(tweet_id, tweet_fields=["public_metrics"])
    if response.data is None:
        return {"likes": 0, "retweets": 0, "replies": 0}
    metrics = response.data.public_metrics or {}
    return {
        "likes": metrics.get("like_count", 0),
        "retweets": metrics.get("retweet_count", 0),
        "replies": metrics.get("reply_count", 0),
    }


def get_follower_count() -> int:
    """Fetch current follower count."""
    client = get_client()
    response = client.get_me(user_fields=["public_metrics"])
    if response.data and response.data.public_metrics:
        return response.data.public_metrics.get("followers_count", 0)
    return 0
