"""
Reddit API client wrapper using PRAW.
Read-only access only — no posting, voting, or account actions.
"""

import praw
import prawcore
from typing import Generator
from datetime import datetime, timedelta
import logging
import time

from .config import settings

logger = logging.getLogger(__name__)


class RedditClient:
    """
    Thin wrapper around PRAW for read-only Reddit access.
    Enforces rate limiting and handles errors gracefully.
    """

    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT,
        )
        # Verify read-only mode
        self.reddit.read_only = True
        logger.info("RedditClient initialized in read-only mode")

    def get_subreddit(self, name: str):
        """Get a subreddit instance."""
        return self.reddit.subreddit(name)

    def get_recent_posts(
        self,
        subreddit: str,
        limit: int = 100,
        time_filter: str = "week",
    ) -> list[dict]:
        """
        Fetch recent posts from a subreddit.
        Returns simplified post dicts with only the fields we need.
        """
        posts = []
        try:
            sub = self.reddit.subreddit(subreddit)
            for post in sub.top(time_filter=time_filter, limit=limit):
                posts.append(self._serialize_post(post))
                time.sleep(0.05)  # Be a good API citizen
        except prawcore.exceptions.NotFound:
            logger.warning(f"Subreddit r/{subreddit} not found")
        except prawcore.exceptions.Forbidden:
            logger.warning(f"r/{subreddit} is private or quarantined")
        except Exception as e:
            logger.error(f"Error fetching posts from r/{subreddit}: {e}")
        return posts

    def get_new_posts(self, subreddit: str, limit: int = 100) -> list[dict]:
        """Fetch the newest posts from a subreddit."""
        posts = []
        try:
            sub = self.reddit.subreddit(subreddit)
            for post in sub.new(limit=limit):
                posts.append(self._serialize_post(post))
                time.sleep(0.05)
        except Exception as e:
            logger.error(f"Error fetching new posts from r/{subreddit}: {e}")
        return posts

    def get_post_comments(self, post_id: str, limit: int = 50) -> list[dict]:
        """Fetch top-level comments for a post."""
        comments = []
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)
            for comment in list(submission.comments)[:limit]:
                comments.append({
                    "id": comment.id,
                    "body": comment.body[:500],  # Truncate long comments
                    "score": comment.score,
                    "author_account_age_days": self._get_account_age(comment.author),
                    "created_utc": comment.created_utc,
                })
                time.sleep(0.02)
        except Exception as e:
            logger.error(f"Error fetching comments for post {post_id}: {e}")
        return comments

    def search_subreddit(
        self, subreddit: str, query: str, limit: int = 50
    ) -> list[dict]:
        """Search for posts within a subreddit."""
        results = []
        try:
            sub = self.reddit.subreddit(subreddit)
            for post in sub.search(query, limit=limit):
                results.append(self._serialize_post(post))
        except Exception as e:
            logger.error(f"Search error in r/{subreddit}: {e}")
        return results

    def get_subreddit_info(self, subreddit: str) -> dict:
        """Get basic info about a subreddit."""
        try:
            sub = self.reddit.subreddit(subreddit)
            return {
                "name": sub.display_name,
                "title": sub.title,
                "description": sub.public_description[:500],
                "subscribers": sub.subscribers,
                "created_utc": sub.created_utc,
                "over18": sub.over18,
                "url": f"https://reddit.com{sub.url}",
            }
        except Exception as e:
            logger.error(f"Error fetching info for r/{subreddit}: {e}")
            return {}

    def _serialize_post(self, post) -> dict:
        """Convert a PRAW submission to a simple dict."""
        return {
            "id": post.id,
            "title": post.title,
            "score": post.score,
            "upvote_ratio": post.upvote_ratio,
            "num_comments": post.num_comments,
            "created_utc": post.created_utc,
            "flair": post.link_flair_text,
            "is_self": post.is_self,
            "url": post.url,
            "author_account_age_days": self._get_account_age(post.author),
        }

    def _get_account_age(self, author) -> int | None:
        """Get account age in days. Returns None if account is deleted."""
        if author is None:
            return None
        try:
            created = datetime.utcfromtimestamp(author.created_utc)
            return (datetime.utcnow() - created).days
        except Exception:
            return None
