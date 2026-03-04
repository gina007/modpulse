"""
ModPulse - Community Health Analytics for Reddit Moderators
Main application entry point
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .reddit_client import RedditClient
from .aggregator import CommunityAggregator
from .scheduler import start_scheduler
from .models import SubredditStats, TrendReport, AnomalyAlert
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting ModPulse...")
    start_scheduler()
    yield
    logger.info("Shutting down ModPulse...")


app = FastAPI(
    title="ModPulse API",
    description="Community health analytics for Reddit moderators",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

reddit_client = RedditClient()
aggregator = CommunityAggregator(reddit_client)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/subreddits/{subreddit}/stats", response_model=SubredditStats)
async def get_subreddit_stats(subreddit: str, days: int = 7):
    """
    Get community health stats for a subreddit over the past N days.
    Read-only. Only accesses public data.
    """
    try:
        stats = await aggregator.get_stats(subreddit, days=days)
        return stats
    except Exception as e:
        logger.error(f"Error fetching stats for r/{subreddit}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/subreddits/{subreddit}/trends", response_model=TrendReport)
async def get_trends(subreddit: str):
    """
    Get post volume and engagement trends for a subreddit.
    """
    try:
        trends = await aggregator.get_trends(subreddit)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/subreddits/{subreddit}/alerts", response_model=list[AnomalyAlert])
async def get_alerts(subreddit: str):
    """
    Get active anomaly alerts for a subreddit.
    Alerts are triggered when metrics exceed configured thresholds.
    """
    try:
        alerts = await aggregator.check_anomalies(subreddit)
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/subreddits/{subreddit}/keywords")
async def get_top_keywords(subreddit: str, limit: int = 20):
    """
    Get top keywords and topics from recent posts.
    """
    try:
        keywords = await aggregator.get_keyword_frequency(subreddit, limit=limit)
        return {"subreddit": subreddit, "keywords": keywords}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/subreddits/{subreddit}/digest")
async def get_weekly_digest(subreddit: str):
    """
    Generate a weekly moderator digest summary.
    """
    try:
        digest = await aggregator.generate_digest(subreddit)
        return digest
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8080, reload=True)
