import shap
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import warnings

def generate_shap_summary(model, X_train, X_test, feature_names, config):
    """
    Generates SHAP values and saves the global feature importance summary plot.
    Receives the feature_names list as a parameter.
    """
    xai_config = config['explainability']
    if not xai_config['enabled']:
        print("\n--- Explainability Analysis Skipped (disabled in config) ---")
        return None, None, None

    print("\n--- Starting Explainable AI (XAI) Analysis with SHAP (KernelExplainer) ---")
    
    X_train_df = pd.DataFrame(X_train, columns=feature_names)
    X_test_df = pd.DataFrame(X_test, columns=feature_names)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        explainer_background = shap.kmeans(X_train_df, 50)

    prediction_function = lambda x: model.predict(x).ravel()
    explainer = shap.KernelExplainer(prediction_function, explainer_background)
    
    num_explanations = xai_config['num_explanations']
    X_test_sample = shap.sample(X_test_df, num_explanations)
    
    print(f"Generating SHAP values for {num_explanations} test samples... (This may take a while)")
    shap_values_matrix = explainer.shap_values(X_test_sample)

    if isinstance(shap_values_matrix, list):
        shap_values_matrix = shap_values_matrix[0]
    shap_values_matrix = np.array(shap_values_matrix)

    print("Generating and saving global feature importance plot...")
    plt.figure()
    shap.summary_plot(shap_values_matrix, X_test_sample, plot_type="bar", show=False)
    
    reports_dir = xai_config['reports_dir']
    summary_plot_path = os.path.join(reports_dir, xai_config['summary_plot_path'])
    plt.savefig(summary_plot_path, bbox_inches='tight')
    plt.close()
    print(f"Summary plot saved to: {summary_plot_path}")
    print("--- SHAP Summary Finished ---")
    
    return explainer, shap_values_matrix, X_test_sample

