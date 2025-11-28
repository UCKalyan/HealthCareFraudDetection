import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Input, Dense, Dropout, BatchNormalization, PReLU
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2

def build_deep_learning_model(input_shape, config):
    """
    Builds a simpler, more stable DNN model with L2 regularization.
    """
    l2_factor = config.get('l2_regularization_factor', 0.001)

    model = Sequential([
        Input(shape=input_shape),
        
        Dense(64, kernel_regularizer=l2(l2_factor)),
        PReLU(),
        BatchNormalization(),
        Dropout(0.4),
        
        Dense(32, kernel_regularizer=l2(l2_factor)),
        PReLU(),
        BatchNormalization(),
        Dropout(0.4),
        
        Dense(1, activation='sigmoid')
    ])
    
    optimizer = Adam(learning_rate=config['learning_rate'])
    
    model.compile(
        optimizer=optimizer,
        loss=tf.keras.losses.BinaryFocalCrossentropy(gamma=2.0, from_logits=False),
        metrics=[tf.keras.metrics.AUC(name='AUC')]
    )
    
    model.summary()
    return model

