"""
Incremental Training Module for HOPE Architecture

Supports two training modes:
1. Incremental: Load existing models, train on new data only
2. Full: Build models from scratch, train on all historical data

Features:
- Smart threshold checking (min samples, max days)
- Timestamp tracking
- Quarterly full retrain scheduling
- Configurable via config.yaml
"""

import os
import json
import logging
import pandas as pd
import numpy as np
import tensorflow as tf
from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Defaults matching start_mcp_server.sh — used when env vars are not exported
_PATH_DEFAULTS = {
    'feature_store_path': 'data/processed/provider_features.csv',
    'scaler_path':        'models/robust_scaler.joblib',
    'kmeans_model_path':  'models/kmeans_model.joblib',
    'specialty_stats_path': 'models/specialty_stats.json',
    'explainer_path':     'models/shap_explainer.pkl',
    'feature_columns_path': 'models/specialty_stats.json',
}

def _resolve_config_path(config: dict, key: str) -> str:
    """Expand env vars in a preprocessor path, falling back to known defaults."""
    raw = config['preprocessor'].get(key, '')
    resolved = os.path.expandvars(raw)
    if not resolved or resolved.startswith('$'):
        resolved = _PATH_DEFAULTS.get(key, raw)
        logger.debug(f"Path '{key}' env var not set, using default: {resolved}")
    return resolved


def load_training_metadata(config: dict) -> dict:
    """
    Load training metadata from timestamp file.
    
    Returns:
        dict with last_training_time, samples_trained, etc.
    """
    timestamp_file = config['incremental_training']['timestamp_file']
    
    if not os.path.exists(timestamp_file):
        # First run - create default metadata
        metadata = {
            'last_training_time': None,
            'last_full_retrain': None,
            'samples_trained': 0,
            'incremental_updates': 0,
            'model_version': '1.0'
        }
        save_training_metadata(metadata, config)
        return metadata
    
    with open(timestamp_file, 'r') as f:
        metadata = json.load(f)
    
    # Convert string timestamps back to datetime
    if metadata['last_training_time']:
       metadata['last_training_time'] = datetime.fromisoformat(metadata['last_training_time'])
    if metadata.get('last_full_retrain'):
        metadata['last_full_retrain'] = datetime.fromisoformat(metadata['last_full_retrain'])
    
    return metadata


def save_training_metadata(metadata: dict, config: dict):
    """Save training metadata to timestamp file."""
    timestamp_file = config['incremental_training']['timestamp_file']
    os.makedirs(os.path.dirname(timestamp_file), exist_ok=True)
    
    # Convert datetime objects to ISO format strings
    metadata_copy = metadata.copy()
    if metadata_copy.get('last_training_time'):
        if isinstance(metadata_copy['last_training_time'], datetime):
            metadata_copy['last_training_time'] = metadata_copy['last_training_time'].isoformat()
    if metadata_copy.get('last_full_retrain'):
        if isinstance(metadata_copy['last_full_retrain'], datetime):
            metadata_copy['last_full_retrain'] = metadata_copy['last_full_retrain'].isoformat()
    
    with open(timestamp_file, 'w') as f:
        json.dump(metadata_copy, f, indent=2)


def get_new_data_since(timestamp: datetime, config: dict) -> pd.DataFrame:
    """
    Load providers added to the DB since the given timestamp.
    Uses the `created_at` column added to providers table.
    Falls back to reading batch CSVs from data/processed/ if DB has no new rows.
    """
    from src.database import get_db_connection

    try:
        ts_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        query = "SELECT * FROM providers WHERE created_at > ?"
        with get_db_connection() as conn:
            new_data = pd.read_sql_query(query, conn, params=(ts_str,))

        logger.info(f"DB query found {len(new_data)} new providers since {ts_str}")
        return new_data

    except Exception as e:
        logger.warning(f"DB query for new providers failed: {e}. Falling back to batch CSV files.")

        # Fallback: scan data/processed/ for CSVs newer than timestamp
        processed_dir = Path('data/processed')
        new_batches = []
        if processed_dir.exists():
            for bf in sorted(processed_dir.glob('*.csv'), key=lambda p: p.stat().st_mtime, reverse=True):
                if datetime.fromtimestamp(bf.stat().st_mtime) > timestamp:
                    logger.info(f"Loading fallback batch: {bf.name}")
                    new_batches.append(pd.read_csv(bf))
                else:
                    break

        if new_batches:
            return pd.concat(new_batches, ignore_index=True)

        logger.warning("No new providers found in DB or batch files.")
        return pd.DataFrame()


def should_retrain(config: dict) -> Tuple[bool, str]:
    """
    Check if retraining thresholds are met.
    
    Returns:
        (should_train: bool, reason: str)
    """
    if not config['incremental_training']['enabled']:
        return False, "Incremental training disabled in config"
    
    metadata = load_training_metadata(config)
    inc_config = config['incremental_training']
    
    # Check if this is first training
    if metadata['last_training_time'] is None:
        return True, "First training run"
    
    # Calculate days since last training
    days_since = (datetime.now() - metadata['last_training_time']).days
    max_days = inc_config['max_days_between']
    
    # Check max days threshold
    if days_since >= max_days:
        return True, f"Max days exceeded: {days_since} >= {max_days}"
    
    # For incremental mode, check minimum samples
    if inc_config['training_mode'] == 'incremental':
        new_data = get_new_data_since(metadata['last_training_time'], config)
        new_count = len(new_data)
        min_samples = inc_config['min_new_samples']
        
        if new_count >= min_samples:
            return True, f"Sufficient new samples: {new_count} >= {min_samples}"
        else:
            return False, f"Insufficient new samples: {new_count} < {min_samples}"
    
    # For full mode, just check days
    return False, f"Only {days_since} days since last training"


def check_full_retrain_schedule(config: dict, metadata: dict) -> bool:
    """Check if quarterly full retrain is due."""
    schedule_config = config['incremental_training'].get('full_retrain_schedule', {})
    
    if not schedule_config.get('enabled', False):
        return False
    
    last_full = metadata.get('last_full_retrain')
    if not last_full:
        return True  # Never had full retrain
    
    interval_days = schedule_config.get('interval_days', 90)
    days_since_full = (datetime.now() - last_full).days
    
    return days_since_full >= interval_days


def incremental_retrain(config: dict, new_data: pd.DataFrame = None, mode: str = None) -> dict:
    """
    Main training function supporting both incremental and full modes.
    
    Args:
        config: Training configuration
        new_data: New data for incremental training (optional if mode='full')
        mode: Override training mode ('incremental' or 'full')
    
    Returns:
        dict with training metrics
    """
    from src.utils.config_loader import load_config
    from src.models.adaptive_deep_model import build_deep_learning_model
    from src.models.nested_learning_model import NestedLearningModel
    from src.training.train import train_model
    from sklearn.utils import class_weight
    from imblearn.over_sampling import SMOTE
    
    # Determine mode
    if mode is None:
        mode = config['incremental_training'].get('training_mode', 'incremental')
    
    metadata = load_training_metadata(config)
    model_path = config['preprocessor']['model_path']
    
    logger.info(f"===== {mode.upper()} RETRAIN MODE =====")
    
    if mode == 'full':
        logger.info("Building new models from scratch on all historical data...")
        
        # Load ALL data
        from src.data_processing.loader import load_and_prep_data
        from src.data_processing.preprocessor import create_advanced_features_and_split
        
        dataframes = load_and_prep_data(config['data'])
        phys_df = dataframes.get('physician')
        presc_df = dataframes.get('prescriber')
        leie_df = dataframes.get('leie')
        
        (X_train, X_val, X_test, 
         y_train, y_val, y_test, 
         feature_names, _, _) = create_advanced_features_and_split(
            phys_df, presc_df, leie_df, config
        )
        
        # Build NEW model
        model_config = config.get('model', {}).get('deep_learning', {
            'learning_rate': 0.001,
            'l2_regularization_factor': 0.001,
        })
        if 'learning_rate' not in model_config:
            model_config['learning_rate'] = 0.001
        model = build_deep_learning_model(
            input_shape=(X_train.shape[1],), 
            config=model_config
        )
        
        epochs = config['incremental_training'].get('full_retrain_epochs', 20)
        metadata['last_full_retrain'] = datetime.now()
        
    elif mode == 'incremental':
        if new_data is None or len(new_data) == 0:
            raise ValueError("Incremental mode requires new_data")
        
        logger.info(f"Loading existing models and training on {len(new_data)} new samples...")
        
        # Load existing HOPE models
        fast_model_path = model_path.replace('.keras', '_fast.keras')
        
        if not os.path.exists(model_path) or not os.path.exists(fast_model_path):
            raise FileNotFoundError(
                f"Existing models not found. Run full training first.\n"
                f"Expected: {model_path} and {fast_model_path}"
            )
        
        fast_model = tf.keras.models.load_model(fast_model_path)
        slow_model = tf.keras.models.load_model(model_path)
        
        # Prepare NEW data only
        # Load feature columns from specialty_stats.json (same source as the API)
        import json as _json
        _stats_path = _resolve_config_path(config, 'specialty_stats_path')
        with open(_stats_path, 'r') as _f:
            _stats = _json.load(_f)
        feature_columns = _stats['final_feature_columns']
        logger.info(f"Loaded {len(feature_columns)} feature columns from specialty_stats.json")

        # Apply scaler
        import joblib as _joblib
        scaler = _joblib.load(_resolve_config_path(config, 'scaler_path'))

        # Ensure all feature columns exist in new_data (fill missing with 0)
        for col in feature_columns:
            if col not in new_data.columns:
                new_data[col] = 0.0

        X_new = scaler.transform(new_data[feature_columns])

        # ── LABEL RESOLUTION ───────────────────────────────────────────────────
        # Priority: 1) is_fraud column in data  2) feedback.db labels  3) zeros
        if 'is_fraud' in new_data.columns:
            y_new = new_data['is_fraud'].values
            logger.info(f"Labels: using 'is_fraud' column from provider data")
        else:
            # Merge labels from feedback.db (written by Monitor Agent + UI)
            y_new = np.zeros(len(new_data))
            feedback_db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                '..', 'shared-data', 'databases', 'feedback.db'
            )
            if os.path.exists(feedback_db_path):
                try:
                    import sqlite3
                    conn = sqlite3.connect(feedback_db_path)
                    fb_df = pd.read_sql_query("SELECT npi, action FROM feedback", conn)
                    conn.close()

                    if len(fb_df) > 0:
                        # Map actions to fraud labels
                        action_map = {
                            'confirm': 1, 'suspicious': 1,
                            'false_positive': 0, 'dismiss': 0
                        }
                        fb_df['label'] = fb_df['action'].map(action_map)
                        fb_df = fb_df.dropna(subset=['label'])
                        fb_df = fb_df.drop_duplicates(subset=['npi'], keep='last')
                        fb_df['npi'] = fb_df['npi'].astype(str)

                        # Match feedback NPIs to new_data provider_ids
                        new_data_ids = new_data['provider_id'].astype(str).values
                        matched = 0
                        for idx, pid in enumerate(new_data_ids):
                            match = fb_df[fb_df['npi'] == pid]
                            if len(match) > 0:
                                y_new[idx] = match.iloc[0]['label']
                                matched += 1

                        logger.info(
                            f"Labels: merged {matched} labels from feedback.db "
                            f"({int(y_new.sum())} fraud, {matched - int(y_new.sum())} clean, "
                            f"{len(y_new) - matched} unlabeled)"
                        )
                    else:
                        logger.info("Labels: feedback.db is empty, no labels available")
                except Exception as e:
                    logger.warning(f"Labels: failed to read feedback.db: {e}")
            else:
                logger.info(f"Labels: feedback.db not found at {feedback_db_path}")

        # ── GUARD: refuse training on fully-unlabeled batch data ────────────────
        # Training BinaryFocalCrossentropy on all-zero labels causes the fast
        # model to collapse and – via EMA – corrupts the slow (production) model.
        n_fraud_labels = int(y_new.sum())
        if n_fraud_labels == 0:
            logger.warning(
                f"Incremental training SKIPPED: all {len(y_new)} new providers have "
                f"label=0 (no fraud labels found in data or feedback.db). "
                f"Training on fully-unlabeled data would corrupt the HOPE model. "
                f"Provide labeled data (via UI confirm/dismiss or Monitor Agent) "
                f"or run a full retrain instead."
            )
            return {
                'mode': mode,
                'skipped': True,
                'reason': 'no_labeled_data',
                'samples_seen': len(y_new),
                'timestamp': datetime.now().isoformat()
            }

        # ── GUARD 2: require minimum fraud labels to prevent collapse ──────────
        # With extreme imbalance (e.g. 1 fraud vs 99 non-fraud), the model
        # learns to predict all-zero, collapsing both Fast and Slow models.
        MIN_FRAUD_LABELS = 5
        if n_fraud_labels < MIN_FRAUD_LABELS:
            logger.warning(
                f"Incremental training SKIPPED: only {n_fraud_labels} fraud label(s) "
                f"found (minimum {MIN_FRAUD_LABELS} required). Training with extreme "
                f"class imbalance would corrupt the HOPE model. "
                f"Wait for more labeled data from Monitor Agent or manual feedback."
            )
            return {
                'mode': mode,
                'skipped': True,
                'reason': 'insufficient_fraud_labels',
                'fraud_labels': n_fraud_labels,
                'min_required': MIN_FRAUD_LABELS,
                'samples_seen': len(y_new),
                'timestamp': datetime.now().isoformat()
            }
        # ────────────────────────────────────────────────────────────────────────

        # Train/val split
        from sklearn.model_selection import train_test_split
        X_train, X_val, y_train, y_val = train_test_split(
            X_new, y_new, test_size=0.1, random_state=42
        )
        
        model = fast_model
        epochs = config['incremental_training'].get('incremental_epochs', 5)
        metadata['incremental_updates'] += 1
    
    # Apply SMOTE only when we have both fraud and non-fraud examples
    # and enough minority samples for the k-neighbors algorithm
    n_classes = len(np.unique(y_train))
    if n_classes >= 2:
        minority_count = int(min(np.bincount(y_train.astype(int))))
        if minority_count >= 2:
            # SMOTE needs k_neighbors < minority_count; default is 5
            k = min(5, minority_count - 1)
            logger.info(f"Applying SMOTE to balance classes (k_neighbors={k}, minority_count={minority_count})...")
            from imblearn.over_sampling import SMOTE
            smote = SMOTE(random_state=42, k_neighbors=k)
            X_train, y_train = smote.fit_resample(X_train, y_train)
        else:
            logger.info(f"Skipping SMOTE: only {minority_count} minority sample(s) — "
                        "need at least 2 for SMOTE. Training on imbalanced data with class weights.")
    else:
        logger.info(f"Skipping SMOTE: only {n_classes} class in training labels (unlabeled batch data). "
                    "Training autoencoder on feature reconstruction only.")
    
    # Calculate class weights (only meaningful when 2+ classes)
    if n_classes >= 2:
        weights = class_weight.compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
        class_weights = dict(enumerate(weights))
    else:
        class_weights = None

    
    # Ensure float32
    X_train = X_train.astype('float32')
    y_train = y_train.astype('float32')
    X_val = X_val.astype('float32')
    y_val = y_val.astype('float32')
    
    # Wrap in HOPE if needed
    if mode == 'full':
        # Create new HOPE wrapper
        slow_model_new = tf.keras.models.clone_model(model)
        slow_model_new.set_weights(model.get_weights())
        
        nested_model = NestedLearningModel(
            fast_model=model,
            slow_model=slow_model_new,
            alpha=config['training']['nested_learning'].get('alpha', 0.99),
            log_frequency=config['training']['nested_learning'].get('log_frequency', 50)
        )
        
        # Compile
        from tensorflow.keras.optimizers import Adam
        optimizer = Adam(learning_rate=config['model'].get('deep_learning', {}).get('learning_rate', 0.001))
        nested_model.compile(
            optimizer=optimizer,
            loss_fn=tf.keras.losses.BinaryFocalCrossentropy(gamma=2.0, from_logits=False),
            metrics=[tf.keras.metrics.AUC(name='AUC')]
        )
        
        training_model = nested_model
    else:
        # Use existing HOPE wrapper
        nested_model = NestedLearningModel(
            fast_model=fast_model,
            slow_model=slow_model,
            alpha=config['training']['nested_learning'].get('alpha', 0.99),
            log_frequency=config['training']['nested_learning'].get('log_frequency', 50)
        )
        
        from tensorflow.keras.optimizers import Adam
        optimizer = Adam(learning_rate=config['model'].get('deep_learning', {}).get('learning_rate', 1e-4))
        nested_model.compile(
            optimizer=optimizer,
            loss_fn=tf.keras.losses.BinaryFocalCrossentropy(gamma=2.0, from_logits=False),
            metrics=[tf.keras.metrics.AUC(name='AUC')]
        )
        
        training_model = nested_model
    
    # Train
    logger.info(f"Training for {epochs} epochs...")
    history = training_model.fit(
        X_train, y_train,
        epochs=epochs,
        batch_size=config['incremental_training']['batch_size'],
        validation_data=(X_val, y_val),
        class_weight=class_weights,
        verbose=1
    )
    
    # Save models
    logger.info("Saving updated models...")
    training_model.slow_model.save(model_path)
    fast_path = model_path.replace('.keras', '_fast.keras')
    training_model.fast_model.save(fast_path)
    
    # Update metadata
    metadata['last_training_time'] = datetime.now()
    metadata['samples_trained'] = metadata.get('samples_trained', 0) + len(X_train)
    save_training_metadata(metadata, config)
    
    logger.info(f"Training complete. Models saved to {model_path}")
    
    # Calculate final evaluation metrics on validation set
    y_pred_proba = training_model.predict(X_val, verbose=0)
    y_pred_probs = y_pred_proba.flatten()
    y_pred_binary = (y_pred_probs > 0.5).astype(int)
    
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    n_classes_val = len(np.unique(y_val))
    if n_classes_val >= 2:
        val_acc = accuracy_score(y_val, y_pred_binary)
        val_prec = precision_score(y_val, y_pred_binary, zero_division=0)
        val_rec = recall_score(y_val, y_pred_binary, zero_division=0)
        val_f1 = f1_score(y_val, y_pred_binary, zero_division=0)
        val_auc = roc_auc_score(y_val, y_pred_probs)
    else:
        val_acc = accuracy_score(y_val, y_pred_binary)
        val_prec = 0.0
        val_rec = 0.0
        val_f1 = 0.0
        val_auc = 0.0
    
    return {
        'mode': mode,
        'epochs': epochs,
        'samples_trained': len(X_train),
        'final_loss': float(history.history.get('loss', history.history.get('val_loss', [0]))[-1]),
        'final_val_loss': float(history.history.get('val_loss', [0])[-1]),
        'val_accuracy': float(val_acc),
        'val_precision': float(val_prec),
        'val_recall': float(val_rec),
        'val_f1': float(val_f1),
        'val_auc': float(val_auc),
        'timestamp': metadata['last_training_time'].isoformat()
    }

def run_incremental_training(config: dict) -> tuple:
    """
    Wrapper function for scheduler to trigger incremental training.
    
    Args:
        config: Application configuration dictionary
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        logger.info("🔄 Starting scheduled incremental training...")
        
        # Load training metadata
        metadata = load_training_metadata(config)
        last_time = metadata.get('last_training_time')
        
        if not last_time:
            last_time = datetime.now() - timedelta(days=30)
        
        # Get new data
        new_data = get_new_data_since(last_time, config)
        
        if len(new_data) == 0:
            return False, "No new data available"
        
        # Check if full retrain needed
        mode = 'full' if check_full_retrain_schedule(config, metadata) else 'incremental'
        
        # Run training
        results = incremental_retrain(config, new_data=new_data, mode=mode)
        
        message = f"Training completed: {results.get('samples_trained')} samples"
        logger.info(f"✅ {message}")
        
        return True, message
        
    except Exception as e:
        error_msg = f"Training failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg


if __name__ == '__main__':
    import argparse
    import sys

    # ── Configure logging to stdout so all logger.info/warning/error calls are visible ──
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

    parser = argparse.ArgumentParser(
        description='HOPE Incremental Retraining CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Normal incremental run (checks thresholds first):
    python -m src.training.incremental_retrain --mode incremental

  Force immediate incremental retrain (bypass threshold checks):
    python -m src.training.incremental_retrain --mode incremental --force

  Force full retrain from scratch:
    python -m src.training.incremental_retrain --mode full --force
"""
    )
    parser.add_argument(
        '--mode',
        choices=['incremental', 'full'],
        default='incremental',
        help='Training mode: incremental (new data only) or full (all historical data)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force training immediately, bypassing min-samples and schedule thresholds'
    )
    args = parser.parse_args()

    # Load config
    try:
        from src.utils.config_loader import load_config
        config = load_config()
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        sys.exit(1)

    logger.info(f"Starting {args.mode.upper()} training run{' (FORCED)' if args.force else ''}...")

    if args.force:
        # Bypass all threshold checks — load data and train directly
        try:
            if args.mode == 'incremental':
                # Load only recently-uploaded batch files from data/processed/
                # (not the full 1.7M feature store - that's for full retrain only)
                processed_dir = Path('data/processed')
                batch_files = sorted(processed_dir.glob('*.csv'), key=lambda p: p.stat().st_mtime, reverse=True)

                if not batch_files:
                    logger.warning("No uploaded batch files found in data/processed/. Upload a CSV first via the UI.")
                    sys.exit(1)

                # Load all batch file(s) uploaded since last training
                metadata = load_training_metadata(config)
                last_time = metadata.get('last_training_time') or datetime.min

                new_batches = []
                for bf in batch_files:
                    mtime = datetime.fromtimestamp(bf.stat().st_mtime)
                    if mtime > last_time:
                        logger.info(f"Loading batch: {bf.name} ({bf.stat().st_size // 1024} KB, {mtime:%Y-%m-%d %H:%M})")
                        new_batches.append(pd.read_csv(bf))
                    else:
                        break  # files are sorted newest-first; stop when older than last training

                if not new_batches:
                    logger.warning("No batch files newer than last training run. Use --mode full to retrain on all data, or upload new providers.")
                    sys.exit(0)

                new_data = pd.concat(new_batches, ignore_index=True)
                # Batch files use 'provider_id' not a standard label column
                logger.info(f"Forcing incremental retrain on {len(new_data)} newly-uploaded providers...")
                results = incremental_retrain(config, new_data=new_data, mode='incremental')
            else:
                logger.info("Forcing full retrain from scratch...")
                results = incremental_retrain(config, mode='full')
            logger.info(f"✅ Training complete: {results}")
        except Exception as e:
            logger.error(f"❌ Training failed: {e}", exc_info=True)
            sys.exit(1)
    elif args.mode == 'incremental':
        # Normal path: respects min_new_samples and max_days thresholds
        success, message = run_incremental_training(config)
        if success:
            logger.info(f"✅ {message}")
        else:
            logger.warning(f"⚠️  Training skipped: {message}")
            sys.exit(0)
    else:  # full, no force
        try:
            results = incremental_retrain(config, mode='full')
            logger.info(f"✅ Full retrain complete: {results}")
        except Exception as e:
            logger.error(f"❌ Full retrain failed: {e}", exc_info=True)
            sys.exit(1)
