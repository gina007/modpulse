"""
Tests for the CommunityAggregator.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from src.aggregator import CommunityAggregator
from src.reddit_client import RedditClient


def make_mock_post(score=100, num_comments=10, upvote_ratio=0.9,
                   account_age=365, created_offset_hours=0):
    from datetime import datetime, timedelta
    return {
        "id": "abc123",
        "title": "How to get started with machine learning in Python",
        "score": score,
        "upvote_ratio": upvote_ratio,
        "num_comments": num_comments,
        "created_utc": (datetime.utcnow() - timedelta(hours=created_offset_hours)).timestamp(),
        "flair": None,
        "is_self": True,
        "url": "https://reddit.com/r/test/abc123",
        "author_account_age_days": account_age,
    }


@pytest.fixture
def mock_client():
    client = MagicMock(spec=RedditClient)
    return client


@pytest.fixture
def aggregator(mock_client):
    return CommunityAggregator(mock_client)


@pytest.mark.asyncio
async def test_get_stats_basic(aggregator, mock_client):
    posts = [make_mock_post(score=i * 10, num_comments=i) for i in range(1, 11)]
    mock_client.get_recent_posts.return_value = posts

    stats = await aggregator.get_stats("python")

    assert stats.subreddit == "python"
    assert stats.post_count == 10
    assert stats.avg_score > 0
    assert 0 <= stats.engagement_score <= 100


@pytest.mark.asyncio
async def test_new_account_ratio_alert(aggregator, mock_client):
    # 80% of posts from new accounts — should trigger alert
    posts = (
        [make_mock_post(account_age=5) for _ in range(8)] +
        [make_mock_post(account_age=365) for _ in range(2)]
    )
    mock_client.get_recent_posts.return_value = posts

    alerts = await aggregator.check_anomalies("python")
    alert_types = [a.alert_type for a in alerts]
    assert "new_account_concentration" in alert_types


@pytest.mark.asyncio
async def test_no_alerts_healthy_community(aggregator, mock_client):
    # Healthy community — no new accounts, good engagement
    posts = [
        make_mock_post(
            score=100, num_comments=15, upvote_ratio=0.92,
            account_age=400, created_offset_hours=i * 4
        )
        for i in range(20)
    ]
    mock_client.get_recent_posts.return_value = posts

    alerts = await aggregator.check_anomalies("python")
    high_alerts = [a for a in alerts if a.severity == "high"]
    assert len(high_alerts) == 0


@pytest.mark.asyncio
async def test_keyword_frequency(aggregator, mock_client):
    posts = [
        {**make_mock_post(), "title": "Python machine learning tutorial"},
        {**make_mock_post(), "title": "Python data science guide"},
        {**make_mock_post(), "title": "Machine learning with Python"},
    ]
    mock_client.get_recent_posts.return_value = posts

    keywords = await aggregator.get_keyword_frequency("python", limit=5)
    keyword_words = [k["keyword"] for k in keywords]
    assert "python" in keyword_words
    assert "machine" in keyword_words


@pytest.mark.asyncio
async def test_get_stats_empty_subreddit(aggregator, mock_client):
    mock_client.get_recent_posts.return_value = []
    stats = await aggregator.get_stats("empty_sub")
    assert stats.post_count == 0
    assert stats.engagement_score == 0.0
