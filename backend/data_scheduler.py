"""
Automated Data Pipeline Scheduler
Runs the NBA data pipeline on a schedule to keep data fresh
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
from nba_data_pipeline import NBADataPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/data_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataScheduler:
    """
    Schedule automated data updates:
    - Daily: Full player stats update (3 AM)
    - Hourly: Quick injury/schedule update during game days
    - Weekly: Deep historical data refresh
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.pipeline = NBADataPipeline()

    def run_full_update(self):
        """Run complete data pipeline"""
        logger.info("Starting scheduled FULL data update...")
        try:
            self.pipeline.save_to_database()
            logger.info("✓ Scheduled full update completed successfully")
        except Exception as e:
            logger.error(f"✗ Scheduled update failed: {e}")

    def run_quick_update(self):
        """Quick update - injuries and today's games only"""
        logger.info("Starting scheduled QUICK update...")
        try:
            self.pipeline.connect_db()

            # Update team stats (quick)
            team_stats = self.pipeline.fetch_team_stats()
            self.pipeline._save_team_stats_to_db(team_stats)

            self.pipeline.close_db()
            logger.info("✓ Quick update completed")
        except Exception as e:
            logger.error(f"✗ Quick update failed: {e}")

    def setup_schedules(self):
        """Setup all scheduled jobs"""

        # Full update: Daily at 3 AM (after games are complete)
        self.scheduler.add_job(
            self.run_full_update,
            CronTrigger(hour=3, minute=0),
            id='daily_full_update',
            name='Daily Full Data Update',
            replace_existing=True
        )

        # Quick update: Every 6 hours during season
        self.scheduler.add_job(
            self.run_quick_update,
            CronTrigger(hour='*/6'),
            id='hourly_quick_update',
            name='6-Hour Quick Update',
            replace_existing=True
        )

        logger.info("Scheduled jobs configured:")
        logger.info("  - Full update: Daily at 3:00 AM")
        logger.info("  - Quick update: Every 6 hours")

    def start(self):
        """Start the scheduler"""
        self.setup_schedules()
        self.scheduler.start()
        logger.info("Data scheduler started!")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Data scheduler stopped")

    def run_now(self):
        """Manually trigger immediate update"""
        logger.info("Manual update triggered...")
        self.run_full_update()


if __name__ == "__main__":
    import sys

    scheduler = DataScheduler()

    if len(sys.argv) > 1 and sys.argv[1] == 'now':
        # Run immediately
        scheduler.run_now()
    else:
        # Start scheduler and keep running
        scheduler.start()
        logger.info("Scheduler running. Press Ctrl+C to exit.")

        try:
            # Keep the script running
            import time
            while True:
                time.sleep(60)
        except (KeyboardInterrupt, SystemExit):
            scheduler.stop()
