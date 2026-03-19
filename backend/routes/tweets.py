import uuid
from fastapi import APIRouter, HTTPException
from models import GenerateRequest, GenerateResponse, TweetCandidate, PostRequest, PostResponse

router = APIRouter(prefix="/tweets")


@router.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    from ai import generate_tweets

    if not req.goal.strip():
        raise HTTPException(status_code=400, detail="goal is required")
    if req.count < 1 or req.count > 5:
        raise HTTPException(status_code=400, detail="count must be between 1 and 5")

    try:
        texts = generate_tweets(req.goal, req.context, req.count)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI generation failed: {str(e)}")

    candidates = [
        TweetCandidate(id=str(uuid.uuid4()), content=t, char_count=len(t))
        for t in texts
    ]
    return GenerateResponse(tweets=candidates)


@router.post("/post", response_model=PostResponse)
def post_now(req: PostRequest):
    from twitter import post_tweet

    if not req.content.strip():
        raise HTTPException(status_code=400, detail="content is required")
    if len(req.content) > 280:
        raise HTTPException(status_code=400, detail="content exceeds 280 characters")

    try:
        result = post_tweet(req.content)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Twitter post failed: {str(e)}")

    return PostResponse(**result)
