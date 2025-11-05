#!/usr/bin/env python3
"""
Team Statistics Auto-Update Scheduler
Automatically fetches and updates team stats on a schedule
"""
import schedule
import time
import logging
from datetime import datetime
from fetch_team_stats import TeamStatsPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_team_stats():
    """Update team statistics"""
    logger.info("=" * 70)
    logger.info("SCHEDULED TEAM STATS UPDATE")
    logger.info("=" * 70)

    try:
        pipeline = TeamStatsPipeline()
        pipeline.save_comprehensive_team_stats('2024-25')
        logger.info("✓ Team stats updated successfully")
    except Exception as e:
        logger.error(f"Error updating team stats: {e}")

def run_scheduler():
    """
    Run the scheduler with the following schedule:
    - Daily at 4:00 AM (during off-hours)
    - Every 6 hours during game days
    """
    logger.info("Starting Team Stats Scheduler...")
    logger.info("Schedule:")
    logger.info("  - Daily at 4:00 AM (comprehensive update)")
    logger.info("  - Every 6 hours (quick updates)")
    logger.info("")

    # Daily comprehensive update at 4 AM
    schedule.every().day.at("04:00").do(update_team_stats)

    # Quick updates every 6 hours
    schedule.every(6).hours.do(update_team_stats)

    # Run once immediately on startup
    logger.info("Running initial update...")
    update_team_stats()

    # Keep running
    logger.info("\nScheduler is running. Press Ctrl+C to stop.")

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == '__main__':
    run_scheduler()
