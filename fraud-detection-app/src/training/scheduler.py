"""
Training Scheduler for Automatic Incremental Retraining

Runs as a background thread that periodically checks if model retraining
is needed based on configured thresholds (time since last training, new samples).

Features:
- Non-blocking background execution
- Configurable check intervals and schedules
- Graceful shutdown
- Exception handling to prevent server crashes
"""

import logging
import threading
import time
import schedule
from datetime import datetime, timedelta
from typing import Optional
from src.utils.config_loader import load_config

logger = logging.getLogger(__name__)


class TrainingScheduler:
    """
    Background scheduler for automatic incremental training.
    
    Runs in a separate thread and periodically checks if training
    thresholds are met. If so, triggers incremental retraining.
    """
    
    def __init__(self, config: dict):
        """
        Initialize scheduler with configuration.
        
        Args:
            config: Full application config dictionary
        """
        self.config = config
        self.training_config = config['incremental_training']
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Validate configuration
        if not self.training_config.get('enabled', False):
            logger.warning("Training scheduler initialized but disabled in config")
    
    def start(self):
        """Start the scheduler in a background thread."""
        if self.running:
            logger.warning("Training scheduler already running")
            return
        
        if not self.training_config.get('enabled', False):
            logger.info("Training scheduler disabled in config - not starting")
            return
        
        self.running = True
        self._stop_event.clear()
        
        # Set up schedule
        schedule_time = self.training_config.get('schedule', '02:00')
        schedule.every().day.at(schedule_time).do(self._check_and_train)
        
        # Start background thread
        self.thread = threading.Thread(target=self._worker, daemon=True, name="TrainingScheduler")
        self.thread.start()
        
        logger.info(f"✅ Training scheduler started (daily at {schedule_time})")
        logger.info(f"   Check interval: every {self.training_config.get('check_interval_minutes', 60)} minutes")
        
        # Calculate and log next scheduled run
        next_run = schedule.next_run()
        if next_run:
            logger.info(f"📅 Next scheduled training check: {next_run}")
    
    def stop(self):
        """Stop the scheduler gracefully."""
        if not self.running:
            return
        
        logger.info("🛑 Stopping training scheduler...")
        self.running = False
        self._stop_event.set()
        
        # Wait for thread to finish (with timeout)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        # Clear schedule
        schedule.clear()
        
        logger.info("✅ Training scheduler stopped")
    
    def _check_and_train(self):
        """
        Check if training is needed and trigger if thresholds met.
        
        This is the main callback function registered with the schedule.
        """
        try:
            logger.info("🔍 Checking if incremental training is needed...")
            
            # Import here to avoid circular dependencies
            from src.training.incremental_retrain import should_retrain, run_incremental_training
            
            # Check if training thresholds are met
            needs_training, reason = should_retrain(self.config)
            
            if needs_training:
                logger.info(f"✅ Training threshold met: {reason}")
                logger.info("🔄 Starting incremental training...")
                
                # Trigger training
                success, message = run_incremental_training(self.config)
                
                if success:
                    logger.info(f"✅ Incremental training completed successfully")
                    logger.info(f"   {message}")
                else:
                    logger.error(f"❌ Incremental training failed: {message}")
            else:
                logger.info(f"ℹ️  Training not needed: {reason}")
                
        except Exception as e:
            logger.error(f"❌ Error in scheduled training check: {e}", exc_info=True)
            # Don't re-raise - keep scheduler running
    
    def _worker(self):
        """
        Background worker loop.
        
        Runs schedule.run_pending() at configured intervals until stopped.
        """
        check_interval = self.training_config.get('check_interval_minutes', 60)
        check_interval_seconds = check_interval * 60
        
        logger.info(f"🔄 Training scheduler worker started (checking every {check_interval} min)")
        
        while self.running and not self._stop_event.is_set():
            try:
                # Run any pending scheduled jobs
                schedule.run_pending()
                
                # Sleep for check interval, but wake up if stop event is set
                self._stop_event.wait(timeout=check_interval_seconds)
                
            except Exception as e:
                logger.error(f"❌ Error in scheduler worker loop: {e}", exc_info=True)
                # Sleep briefly before continuing
                time.sleep(60)
        
        logger.info("🛑 Training scheduler worker exiting")
    
    def trigger_manual_check(self):
        """
        Manually trigger a training check (for testing/admin purposes).
        
        Runs the check in the background thread.
        """
        if not self.running:
            logger.warning("Cannot trigger manual check - scheduler not running")
            return False
        
        logger.info("🔧 Manual training check triggered")
        
        # Schedule immediate check
        schedule.every().second.do(self._check_and_train).tag('manual')
        
        # Clear manual tag after first run
        def clear_manual():
            schedule.clear('manual')
        
        schedule.every().second.do(clear_manual).tag('cleanup')
        
        return True


# Convenience function for creating and starting scheduler
def start_training_scheduler(config: dict) -> Optional[TrainingScheduler]:
    """
    Create and start training scheduler if enabled in config.
    
    Args:
        config: Application configuration
    
    Returns:
        TrainingScheduler instance if started, None otherwise
    """
    training_config = config.get('incremental_training', {})
    
    if not training_config.get('enabled', False):
        logger.info("Incremental training disabled in config")
        return None
    
    scheduler = TrainingScheduler(config)
    scheduler.start()
    return scheduler
