#!/usr/bin/env python
"""
Scheduled Retraining Script for HOPE Architecture

This script is designed to be run via cron or task scheduler.
It checks if retraining thresholds are met and triggers training accordingly.

Usage:
    python scheduled_retrain.py [--force] [--mode=incremental|full]

Cron Examples:
    # Daily at 2 AM
    0 2 * * * cd /path/to/fraud-detection-app && python scheduled_retrain.py
    
    # Quarterly full retrain (first day of Jan, Apr, Jul, Oct at 2 AM)
    0 2 1 */3 * cd /path/to/fraud-detection-app && python scheduled_retrain.py --mode=full

Arguments:
    --force: Skip threshold checks, train regardless
    --mode: Override config training mode (incremental or full)
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config_loader import load_config
from src.training.incremental_retrain import (
    should_retrain,
    get_new_data_since,
    load_training_metadata,
    incremental_retrain,
    check_full_retrain_schedule
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduled_retrain.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Scheduled model retraining')
    parser.add_argument('--force', action='store_true', help='Force training regardless of thresholds')
    parser.add_argument('--mode', choices=['incremental', 'full'], help='Override training mode')
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("SCHEDULED RETRAINING CHECK")
    logger.info("=" * 60)
    
    # Load config
    config = load_config('config.yaml')
    
    if not config.get('incremental_training', {}).get('enabled', False):
        logger.info("❌ Incremental training disabled in config")
        return
    
    # Determine mode
    mode = args.mode or config['incremental_training'].get('training_mode', 'incremental')
    logger.info(f"Training mode: {mode}")
    
    # Check if quarterly full retrain is due
    if mode == 'incremental':
        metadata = load_training_metadata(config)
        if check_full_retrain_schedule(config, metadata):
            logger.info("⏰ Quarterly full retrain schedule triggered")
            mode = 'full'
            args.force = True  # Override threshold check
    
    # Check thresholds (unless forced or full mode)
    if not args.force and mode == 'incremental':
        should_train, reason = should_retrain(config)
        
        if not should_train:
            logger.info(f"⏭️  Skipping training: {reason}")
            return
        
        logger.info(f"✅ Training threshold met: {reason}")
    
    # Get new data (for incremental mode)
    new_data = None
    if mode == 'incremental':
        metadata = load_training_metadata(config)
        last_training = metadata.get('last_training_time')
        
        if last_training:
            new_data = get_new_data_since(last_training, config)
            logger.info(f"📊 Found {len(new_data)} new samples since {last_training}")
        else:
            logger.warning("No last training timestamp. Running full training instead.")
            mode = 'full'
    
    # Run training
    try:
        logger.info(f"🚀 Starting {mode} training...")
        results = incremental_retrain(config, new_data=new_data, mode=mode)

        logger.info("=" * 60)

        # Guard: incremental_retrain returns {'skipped': True} when all labels
        # are zero (batch providers without is_fraud). This is expected — log
        # and exit cleanly rather than crashing on missing keys.
        if results.get('skipped'):
            logger.info(f"⏭️  TRAINING SKIPPED — {results.get('reason', 'unknown reason')}")
            logger.info(f"   Providers seen: {results.get('samples_seen', 0)}")
            logger.info(f"   Tip: Incremental retraining requires labeled data "
                        f"(providers with known fraud/non-fraud outcomes).")
            logger.info("=" * 60)
            return   # exit 0 — this is not an error

        logger.info("✅ TRAINING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Mode: {results['mode']}")
        logger.info(f"Epochs: {results.get('epochs', 0)}")
        logger.info(f"Samples trained: {results.get('samples_trained', 0)}")
        logger.info(f"Final loss: {results.get('final_loss', 0):.4f}")
        logger.info(f"Final val loss: {results.get('final_val_loss', 0):.4f}")
        
        if 'val_accuracy' in results:
            logger.info(f"Val Accuracy: {results['val_accuracy']:.4f}")
            logger.info(f"Val Precision: {results['val_precision']:.4f}")
            logger.info(f"Val Recall: {results['val_recall']:.4f}")
            logger.info(f"Val F1 Score: {results['val_f1']:.4f}")
            logger.info(f"Val AUC: {results['val_auc']:.4f}")
            
        logger.info(f"Timestamp: {results.get('timestamp', '')}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Training failed: {e}", exc_info=True)
        sys.exit(1)



if __name__ == "__main__":
    main()
