import logging
import os
import tensorflow as tf
from tensorflow.keras import Model

class NestedLearningModel(Model):
    """
    Implements Google Nested Learning (HOPE) concept via Dual-Speed Weights.
    
    Architecture:
    - Fast Model: Learns quickly from new data (High Learning Rate).
    - Slow Model: Learns slowly from the Fast Model via EMA (Exponential Moving Average).
    
    This prevents "Catastrophic Forgetting" by keeping a stable "Core Memory" (Slow Model)
    while allowing rapid adaptation to new fraud trends (Fast Model).
    """
    
    def __init__(self, fast_model, slow_model, alpha=0.99, log_frequency=50):
        """
        Args:
            fast_model: The main trainable model.
            slow_model: A clone of the model (non-trainable via gradient).
            alpha: The decay rate for the moving average (e.g., 0.99).
                   Higher alpha = Slower updates (More stability).
            log_frequency: How often (in batches) to log divergence metrics.
        """
        super(NestedLearningModel, self).__init__()
        self.fast_model = fast_model
        self.slow_model = slow_model
        self.alpha = alpha
        self.log_frequency = log_frequency
        self.step_counter = 0
        
        # Setup logger
        self.logger = self._setup_logger()
        self.logger.info(f"HOPE Initialized | Alpha: {alpha} | Log Frequency: {log_frequency}")
        
        # Ensure slow model is not trainable via gradient descent
        self.slow_model.trainable = False

    def compile(self, optimizer, loss_fn, metrics):
        super(NestedLearningModel, self).compile()
        self.optimizer = optimizer
        self.loss_fn = loss_fn
        self.custom_metrics = metrics

    def train_step(self, data):
        # Unpack data, handling optional sample_weights
        if len(data) == 3:
            x, y, sample_weight = data
        else:
            x, y = data
            sample_weight = None
        
        with tf.GradientTape() as tape:
            # Forward pass (Fast Model)
            y_pred = self.fast_model(x, training=True)
            
            # Compute loss with optional sample weights
            if sample_weight is not None:
                # Ensure sample_weight is (batch, 1)
                sample_weight = tf.reshape(sample_weight, [-1, 1])
                # Ensure y is (batch, 1)
                y = tf.reshape(y, [-1, 1])
                loss = self.loss_fn(y, y_pred, sample_weight=sample_weight)
            else:
                loss = self.loss_fn(y, y_pred)
            
        # Backward pass (Update Fast Model)
        trainable_vars = self.fast_model.trainable_variables
        gradients = tape.gradient(loss, trainable_vars)
        self.optimizer.apply_gradients(zip(gradients, trainable_vars))
        
        # Update Slow Model (EMA)
        # slow_weight = alpha * slow_weight + (1 - alpha) * fast_weight
        weight_divergences = []
        for fast_var, slow_var in zip(self.fast_model.variables, self.slow_model.variables):
            # Calculate divergence BEFORE update
            divergence = tf.reduce_mean(tf.abs(fast_var - slow_var))
            weight_divergences.append(divergence)

            slow_var.assign(
                self.alpha * slow_var + (1 - self.alpha) * fast_var
            )

        # Log updates periodically
        self.step_counter += 1
        if self.step_counter % self.log_frequency == 0:
            avg_div = tf.reduce_mean(weight_divergences).numpy()
            max_div = tf.reduce_max(weight_divergences).numpy()
            
            self.logger.info(
                f"Step {self.step_counter:5d} | "
                f"Avg Divergence: {avg_div:.8f} | "
                f"Max Divergence: {max_div:.8f}"
            )
            
        # Update metrics
        for metric in self.custom_metrics:
            metric.update_state(y, y_pred)
            
        return {m.name: m.result() for m in self.custom_metrics}

    def call(self, inputs, training=False):
        # During inference, we can choose to use the Stable (Slow) model
        # or the Adaptive (Fast) model.
        # For fraud detection, we usually want the Stable one for final decisions,
        # but maybe the Fast one for "Early Warning".
        # Let's return the Slow Model's prediction by default for stability.
        if training:
            return self.fast_model(inputs)
        else:
            return self.slow_model(inputs)

    def _setup_logger(self):
        """Create dedicated logger for HOPE updates."""
        logger = logging.getLogger('HOPE')
        logger.setLevel(logging.INFO)
        
        # Only add handler if not already added to avoid duplicates
        if not logger.handlers:
            os.makedirs('logs', exist_ok=True)
            handler = logging.FileHandler('logs/hope_updates.log', mode='a')
            formatter = logging.Formatter(
                '[%(asctime)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
