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
            mode='max',
            restore_best_weights=True
        ))
        
    if config['reduce_lr']['enabled']:
        callbacks.append(ReduceLROnPlateau(
            monitor=config['reduce_lr']['monitor'],
            factor=config['reduce_lr']['factor'],
            patience=config['reduce_lr']['patience'],
            verbose=1,
            mode='max',
            min_lr=1e-6
        ))

    history = model.fit(
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
    model.save(model_path)
    
    return history

