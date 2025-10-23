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

def main():
    """Main pipeline for the fraud detection project."""
    print("--- Starting Healthcare Fraud Detection Pipeline ---")
    
    config = load_config('config.yaml')
    
    dataframes = load_and_prep_data(config['data'])
    phys_df = dataframes.get('physician')
    presc_df = dataframes.get('prescriber')
    
    if phys_df is None or presc_df is None:
        print("--- Pipeline Halting due to data loading errors. ---")
        return
        
    # THE DEFINITIVE FIX: Pass the entire config object.
    (
        X_train, X_val, X_test, 
        y_train, y_val, y_test, 
        feature_names, 
        _, _ 
    ) = create_advanced_features_and_split(phys_df, presc_df, config)

    model_config = config['training']
    
    if not model_config['force_retrain'] and os.path.exists(model_config['model_path']):
        print(f"\n--- Loading existing model from {model_config['model_path']} ---")
        model = tf.keras.models.load_model(model_config['model_path'])
    else:
        print("\n--- Building and Training New Model ---")
        print("Calculating class weights to handle data imbalance...")
        weights = class_weight.compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
        class_weights = dict(enumerate(weights))
        print(f"Class weights: {class_weights}\n")
        
        model = build_deep_learning_model(input_shape=(X_train.shape[1],), config=model_config)
        train_model(model, X_train, y_train, X_val, y_val, class_weights, config=model_config)
    
    evaluate_model(model, X_test, y_test, config['evaluation'])

    explainer, shap_values, data_sample = generate_shap_summary(
        model, X_train, X_test, feature_names, config
    )

    if explainer is not None:
        generate_llm_report(
            explainer, shap_values, data_sample, model, feature_names, config['llm_reporting']
        )

    print("\n--- Pipeline Finished ---")

if __name__ == "__main__":
    main()

