import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, LearningRateScheduler
import os
import numpy as np

def _create_warmup_scheduler(config):
    """Creates a learning rate scheduler with a warmup phase."""
    warmup_config = config['lr_warmup']
    target_lr = config['learning_rate']
    
    def scheduler(epoch, lr):
        if epoch < warmup_config['warmup_epochs']:
            # Linear increase from initial_lr to target_lr
            initial_lr = target_lr * warmup_config['initial_lr_factor']
            step = (target_lr - initial_lr) / warmup_config['warmup_epochs']
            return initial_lr + (step * epoch)
        else:
            # After warmup, maintain the learning rate (ReduceLROnPlateau will take over)
            return lr
    return LearningRateScheduler(scheduler, verbose=1)

def train_model(model, X_train, y_train, X_val, y_val, class_weights, config):
    """
    Trains the model, now with a stable learning rate warmup schedule.
    """
    print("\n--- Model Training Started ---")
    
    model_path = config['model_path']
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    callbacks = []
    
    # Add the warmup scheduler first
    if config['lr_warmup']['enabled']:
        callbacks.append(_create_warmup_scheduler(config))
        
    if config['early_stopping']['enabled']:
        callbacks.append(EarlyStopping(
            monitor=config['early_stopping']['monitor'],
            patience=config['early_stopping']['patience'],
            verbose=1,
            mode='min',
            restore_best_weights=True
        ))
        
    if config['reduce_lr']['enabled']:
        callbacks.append(ReduceLROnPlateau(
            monitor=config['reduce_lr']['monitor'],
            factor=config['reduce_lr']['factor'],
            patience=config['reduce_lr']['patience'],
            verbose=1,
            mode='min',
            min_lr=1e-6
        ))

    # --- Nested Learning (HOPE) Setup ---
    nested_config = config.get('nested_learning', {'enabled': False})
    if nested_config['enabled']:
        print(f"\n--- 🧠 Initializing Google Nested Learning (HOPE) ---")
        print(f"    Alpha (Stability Factor): {nested_config.get('alpha', 0.99)}")
        
        from src.models.nested_learning_model import NestedLearningModel
        
        # Clone the model to create the Slow (Stable) Memory
        slow_model = tf.keras.models.clone_model(model)
        slow_model.set_weights(model.get_weights())
        
        # Wrap in Nested Learning Architecture
        nested_model = NestedLearningModel(
            fast_model=model, 
            slow_model=slow_model, 
            alpha=nested_config.get('alpha', 0.99)
        )
        
        # Compile the wrapper (needs same optimizer/loss as original)
        # Note: We need to re-instantiate optimizer to avoid binding issues
        from tensorflow.keras.optimizers import Adam
        optimizer = Adam(learning_rate=config['learning_rate'])
        
        nested_model.compile(
            optimizer=optimizer,
            loss_fn=tf.keras.losses.BinaryFocalCrossentropy(gamma=2.0, from_logits=False),
            metrics=[tf.keras.metrics.AUC(name='AUC')]
        )
        
        training_model = nested_model
        print("    ✅ Dual-Speed Model Created (Fast + Slow Weights)")
    else:
        training_model = model

    history = training_model.fit(
        X_train,
        y_train,
        epochs=config['epochs'],
        batch_size=config['batch_size'],
        validation_data=(X_val, y_val),
        callbacks=callbacks,
        class_weight=class_weights,
        verbose=1
    )
    
    print(f"\n--- Model Training Finished. Saving best model to {model_path} ---")
    
    # If Nested Learning, save the Slow (Stable) Model AND Fast (Early Warning) Model
    if nested_config['enabled']:
        print("    💾 Saving Stable (Slow) Model for robust inference...")
        training_model.slow_model.save(model_path)
        
        fast_path = model_path.replace('.keras', '_fast.keras')
        print(f"    💾 Saving Fast (Early Warning) Model to {fast_path}...")
        training_model.fast_model.save(fast_path)
    else:
        model.save(model_path)
    
    # --- Calculate and Log Metrics ---
    from sklearn.metrics import accuracy_score, roc_auc_score, f1_score
    import datetime
    
    print("\n--- Calculating Final Metrics ---")
    y_pred_prob = model.predict(X_val)
    y_pred = (y_pred_prob > 0.5).astype(int)
    
    acc = accuracy_score(y_val, y_pred)
    roc = roc_auc_score(y_val, y_pred_prob)
    f1 = f1_score(y_val, y_pred)
    
    print(f"Accuracy: {acc:.4f}")
    print(f"ROC-AUC: {roc:.4f}")
    print(f"F1-Score: {f1:.4f}")
    
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "model_metrics.log")
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] Accuracy: {acc:.4f}, ROC-AUC: {roc:.4f}, F1-Score: {f1:.4f}\n")
    
    print(f"Metrics saved to {log_file}")
    
    return history

