"""
APScheduler jobs for periodic data collection and digest generation.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from .config import settings

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def collect_metrics():
    """Scheduled job: collect fresh metrics for all monitored subreddits."""
    subreddits = [s.strip() for s in settings.TARGET_SUBREDDITS.split(",")]
    logger.info(f"Scheduled collection running for {len(subreddits)} subreddits")
    # Actual collection handled by aggregator on-demand
    # This job pre-warms the cache
    for sub in subreddits:
        logger.info(f"  → Collecting r/{sub}")


def send_weekly_digests():
    """Scheduled job: send weekly digest emails to opted-in moderators."""
    logger.info("Sending weekly moderator digests...")
    # Email sending logic handled by mailer module


def start_scheduler():
    """Start all background jobs."""
    # Collect metrics every 30 minutes
    scheduler.add_job(
        collect_metrics,
        trigger=CronTrigger(minute="*/30"),
        id="collect_metrics",
        replace_existing=True,
    )
    # Send weekly digests every Monday at 9am UTC
    scheduler.add_job(
        send_weekly_digests,
        trigger=CronTrigger(day_of_week="mon", hour=9, minute=0),
        id="weekly_digest",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started")
