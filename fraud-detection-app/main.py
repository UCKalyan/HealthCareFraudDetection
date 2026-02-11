import os
import tensorflow as tf
from sklearn.utils import class_weight
import numpy as np

from src.utils.config_loader import load_config
from src.data_processing.loader import load_and_prep_data
from src.data_processing.preprocessor import create_advanced_features_and_split
from src.models.adaptive_deep_model import build_deep_learning_model
from src.training.train import train_model
from src.utils.evaluation import evaluate_model
from src.explainability.shap_analyzer import generate_shap_summary
from src.reporting.llm_reporter import generate_llm_report
from dotenv import load_dotenv

def main():
    """Main pipeline for the fraud detection project."""
    load_dotenv()
    print("--- Starting Healthcare Fraud Detection Pipeline ---")
    
    config = load_config('config.yaml')
    
    # Check if feature store exists to skip raw data loading
    feature_store_path = config['preprocessor']['feature_store_path']
    # Resolve env var if needed (already done by load_config but just in case)
    if feature_store_path.startswith('$'):
        feature_store_path = os.path.expandvars(feature_store_path)
        
    if os.path.exists(feature_store_path):
        from src.data_processing.preprocessor import load_features_and_split
        print(f"--- Fast Path: Loading from {feature_store_path} ---")
        
        leie_df = None
        if config['preprocessor'].get('labeling_method') == 'supervised':
            print("--- Loading LEIE for Supervised Labeling ---")
            import copy
            leie_config = copy.deepcopy(config['data'])
            # Disable other loaders to only load LEIE
            leie_config['loader']['physician_keyword'] = None
            leie_config['loader']['prescriber_keyword'] = None
            
            loaded_data = load_and_prep_data(leie_config)
            leie_df = loaded_data.get('leie')

        (
            X_train, X_val, X_test, 
            y_train, y_val, y_test, 
            feature_names, 
            _, _ 
        ) = load_features_and_split(feature_store_path, config, leie_df=leie_df)
    else:
        dataframes = load_and_prep_data(config['data'])
        phys_df = dataframes.get('physician')
        presc_df = dataframes.get('prescriber')
        leie_df = dataframes.get('leie')
        
        if phys_df is None or presc_df is None:
            print("--- Pipeline Halting due to data loading errors. ---")
            return
            
        (
            X_train, X_val, X_test, 
            y_train, y_val, y_test, 
            feature_names, 
            all_profiles_engineered, _ 
        ) = create_advanced_features_and_split(phys_df, presc_df, leie_df, config)
        
        # Save Feature Store
        print(f"--- Saving Feature Store to {feature_store_path} ---")
        all_profiles_engineered.to_csv(feature_store_path)

    # Fix config mapping
    model_type = config['model']['type']
    train_type = config['model']['train']
    model_config = config['model'][model_type]
    # Add paths to model_config for convenience
    model_config['model_path'] = config['preprocessor']['model_path']
    # Add other training params if missing
    if 'lr_warmup' not in model_config:
        model_config['lr_warmup'] = {'enabled': False}
    if 'early_stopping' not in model_config:
        model_config['early_stopping'] = {'enabled': True, 'monitor': 'val_loss', 'patience': 5}
    if 'reduce_lr' not in model_config:
        model_config['reduce_lr'] = {'enabled': True, 'monitor': 'val_loss', 'factor': 0.2, 'patience': 3}
    if 'learning_rate' not in model_config:
        model_config['learning_rate'] = 0.001
        
    # Inject Nested Learning config
    if 'training' in config and 'nested_learning' in config['training']:
        model_config['nested_learning'] = config['training']['nested_learning']
    else:
        model_config['nested_learning'] = {'enabled': False}
        
    force_retrain = train_type # Always retrain for this fix

    if not force_retrain and os.path.exists(model_config['model_path']):
        print(f"\n--- Loading existing model from {model_config['model_path']} ---")
        model = tf.keras.models.load_model(model_config['model_path'])
    else:
        print("\n--- Building and Training New Model ---")
        
        print("Applying SMOTE to handle class imbalance...")
        from imblearn.over_sampling import SMOTE
        smote = SMOTE(random_state=42)
        X_train, y_train = smote.fit_resample(X_train, y_train)
        print(f"Resampled training data shape: {X_train.shape}")
        print(f"Resampled class distribution: {np.unique(y_train, return_counts=True)}")

        print("Calculating class weights (should be balanced now)...")
        weights = class_weight.compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
        class_weights = dict(enumerate(weights))
        print(f"Class weights: {class_weights}\n")
        
        model = build_deep_learning_model(input_shape=(X_train.shape[1],), config=model_config)
        
        # Ensure data is float32
        X_train = X_train.astype('float32')
        y_train = y_train.astype('float32')
        X_val = X_val.astype('float32')
        y_val = y_val.astype('float32')
        
        train_model(model, X_train, y_train, X_val, y_val, class_weights, config=model_config)
    
    # Ensure test data is float32
    X_test = X_test.astype('float32')
    y_test = y_test.astype('float32')
    evaluate_model(model, X_test, y_test, config['evaluation'])

    explainer, shap_values, data_sample = generate_shap_summary(
        model, X_train, X_test, feature_names, config
    )

    if explainer is not None:
        generate_llm_report(
            explainer, shap_values, data_sample, model, feature_names, config['llm']
        )

    print("\n--- Pipeline Finished ---")

if __name__ == "__main__":
    main()

