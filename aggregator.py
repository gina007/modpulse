"""
CommunityAggregator — core analytics engine for ModPulse.
Aggregates Reddit data into health metrics, trends, and anomaly alerts.
"""

from collections import Counter
from datetime import datetime, timedelta
import re
import statistics
import logging

from .reddit_client import RedditClient
from .models import SubredditStats, TrendReport, AnomalyAlert
from .config import settings

logger = logging.getLogger(__name__)

# Common words to exclude from keyword analysis
STOPWORDS = {
    "the", "a", "an", "is", "it", "in", "on", "at", "to", "for",
    "of", "and", "or", "but", "with", "this", "that", "my", "i",
    "you", "we", "are", "was", "be", "have", "do", "not", "what",
    "how", "why", "when", "where", "who", "your", "just", "like",
    "get", "got", "can", "will", "has", "had", "been", "its", "so",
    "about", "from", "they", "their", "there", "more", "if", "any",
}


class CommunityAggregator:
    def __init__(self, reddit_client: RedditClient):
        self.client = reddit_client

    async def get_stats(self, subreddit: str, days: int = 7) -> SubredditStats:
        """Compute community health stats over the past N days."""
        posts = self.client.get_recent_posts(subreddit, limit=200, time_filter="week")

        if not posts:
            return SubredditStats(subreddit=subreddit, post_count=0)

        scores = [p["score"] for p in posts]
        comment_counts = [p["num_comments"] for p in posts]
        upvote_ratios = [p["upvote_ratio"] for p in posts]
        account_ages = [p["author_account_age_days"] for p in posts if p["author_account_age_days"] is not None]

        new_account_posts = sum(1 for age in account_ages if age < 30)
        new_account_ratio = new_account_posts / len(posts) if posts else 0

        return SubredditStats(
            subreddit=subreddit,
            post_count=len(posts),
            avg_score=round(statistics.mean(scores), 1),
            median_score=round(statistics.median(scores), 1),
            avg_comments=round(statistics.mean(comment_counts), 1),
            avg_upvote_ratio=round(statistics.mean(upvote_ratios), 3),
            new_account_ratio=round(new_account_ratio, 3),
            engagement_score=self._compute_engagement_score(posts),
        )

    async def get_trends(self, subreddit: str) -> TrendReport:
        """Get post volume trends bucketed by day."""
        posts = self.client.get_recent_posts(subreddit, limit=500, time_filter="month")

        # Bucket by day
        daily_counts: dict[str, int] = {}
        daily_scores: dict[str, list] = {}

        for post in posts:
            day = datetime.utcfromtimestamp(post["created_utc"]).strftime("%Y-%m-%d")
            daily_counts[day] = daily_counts.get(day, 0) + 1
            daily_scores.setdefault(day, []).append(post["score"])

        trend_data = [
            {
                "date": day,
                "post_count": daily_counts[day],
                "avg_score": round(statistics.mean(daily_scores[day]), 1),
            }
            for day in sorted(daily_counts.keys())
        ]

        return TrendReport(subreddit=subreddit, daily_trends=trend_data)

    async def check_anomalies(self, subreddit: str) -> list[AnomalyAlert]:
        """
        Check for anomalies that may indicate spam, brigading, or unusual activity.
        Returns a list of active alerts with severity levels.
        """
        alerts = []
        posts = self.client.get_recent_posts(subreddit, limit=200, time_filter="week")

        if len(posts) < 10:
            return alerts

        # --- Alert 1: Post volume spike ---
        recent_posts = [
            p for p in posts
            if datetime.utcfromtimestamp(p["created_utc"]) > datetime.utcnow() - timedelta(hours=24)
        ]
        older_posts = [
            p for p in posts
            if datetime.utcfromtimestamp(p["created_utc"]) <= datetime.utcnow() - timedelta(hours=24)
        ]
        avg_daily = len(older_posts) / 6 if older_posts else 1
        if avg_daily > 0 and len(recent_posts) / avg_daily > settings.SPIKE_THRESHOLD:
            alerts.append(AnomalyAlert(
                subreddit=subreddit,
                alert_type="volume_spike",
                severity="high",
                message=f"Post volume in last 24h ({len(recent_posts)}) is "
                        f"{len(recent_posts)/avg_daily:.1f}x the 6-day average ({avg_daily:.0f}/day)",
            ))

        # --- Alert 2: New account concentration ---
        account_ages = [p["author_account_age_days"] for p in posts if p["author_account_age_days"] is not None]
        if account_ages:
            new_ratio = sum(1 for a in account_ages if a < 30) / len(account_ages)
            if new_ratio > settings.NEW_ACCOUNT_RATIO:
                alerts.append(AnomalyAlert(
                    subreddit=subreddit,
                    alert_type="new_account_concentration",
                    severity="medium",
                    message=f"{new_ratio:.0%} of recent posts are from accounts less than 30 days old",
                ))

        # --- Alert 3: Low engagement (possible ghost posts) ---
        avg_comments = statistics.mean(p["num_comments"] for p in posts)
        if avg_comments < 1.5:
            alerts.append(AnomalyAlert(
                subreddit=subreddit,
                alert_type="low_engagement",
                severity="low",
                message=f"Average comments per post is very low ({avg_comments:.1f}), "
                        "which may indicate low community engagement or bot activity",
            ))

        return alerts

    async def get_keyword_frequency(
        self, subreddit: str, limit: int = 20
    ) -> list[dict]:
        """Extract top keywords from post titles."""
        posts = self.client.get_recent_posts(subreddit, limit=200, time_filter="week")
        words = []
        for post in posts:
            tokens = re.findall(r'\b[a-zA-Z]{3,}\b', post["title"].lower())
            words.extend([w for w in tokens if w not in STOPWORDS])

        counter = Counter(words)
        return [
            {"keyword": word, "count": count}
            for word, count in counter.most_common(limit)
        ]

    async def generate_digest(self, subreddit: str) -> dict:
        """Generate a weekly moderator digest."""
        stats = await self.get_stats(subreddit)
        alerts = await self.check_anomalies(subreddit)
        keywords = await self.get_keyword_frequency(subreddit, limit=10)
        info = self.client.get_subreddit_info(subreddit)

        return {
            "subreddit": subreddit,
            "generated_at": datetime.utcnow().isoformat(),
            "subscribers": info.get("subscribers"),
            "week_stats": stats,
            "active_alerts": len(alerts),
            "top_keywords": keywords,
            "summary": self._generate_summary_text(stats, alerts),
        }

    def _compute_engagement_score(self, posts: list[dict]) -> float:
        """
        Compute a 0-100 engagement health score.
        Considers score, comment depth, and upvote ratio.
        """
        if not posts:
            return 0.0

        avg_ratio = statistics.mean(p["upvote_ratio"] for p in posts)
        avg_comments = statistics.mean(p["num_comments"] for p in posts)
        comment_score = min(avg_comments / 20, 1.0)  # Normalize to 20 comments = max
        score = (avg_ratio * 0.5 + comment_score * 0.5) * 100
        return round(score, 1)

    def _generate_summary_text(self, stats: SubredditStats, alerts: list) -> str:
        """Generate a human-readable summary for the digest."""
        lines = [
            f"This week r/{stats.subreddit} had {stats.post_count} posts "
            f"with an average score of {stats.avg_score}.",
        ]
        if alerts:
            lines.append(f"⚠️ {len(alerts)} anomaly alert(s) require your attention.")
        else:
            lines.append("✅ No anomalies detected. Community looks healthy.")
        return " ".join(lines)
