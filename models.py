"""
ModPulse data models.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SubredditStats(BaseModel):
    subreddit: str
    post_count: int
    avg_score: float = 0.0
    median_score: float = 0.0
    avg_comments: float = 0.0
    avg_upvote_ratio: float = 0.0
    new_account_ratio: float = 0.0
    engagement_score: float = 0.0


class DailyTrend(BaseModel):
    date: str
    post_count: int
    avg_score: float


class TrendReport(BaseModel):
    subreddit: str
    daily_trends: list[DailyTrend]


class AnomalyAlert(BaseModel):
    subreddit: str
    alert_type: str
    severity: str  # "low", "medium", "high"
    message: str
    created_at: datetime = datetime.utcnow()
