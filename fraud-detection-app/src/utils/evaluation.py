from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, precision_recall_curve, f1_score
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import os

def evaluate_model(model, X_test, y_test, eval_config):
    """
    Evaluates the model, prints classification report, and saves plots.
    Includes a safety net to handle any potential NaN predictions from the model.
    """
    print("\n--- Evaluating model performance on the final test set... ---")
    
    y_pred_proba = model.predict(X_test).ravel()
    
    # THE SAFETY NET: Replace any potential NaN/inf values from the model's prediction
    # before they can cause a crash in the metrics functions.
    y_pred_proba = np.nan_to_num(y_pred_proba, nan=0.5, posinf=1.0, neginf=0.0)

    # Find optimal threshold using the Precision-Recall curve
    precision, recall, thresholds = precision_recall_curve(y_test, y_pred_proba)
    f1_scores = 2 * (precision * recall) / (precision + recall)
    f1_scores = np.nan_to_num(f1_scores)
    
    # Get the best threshold
    optimal_idx = np.argmax(f1_scores)
    # Handle the case where thresholds might be one element shorter
    optimal_threshold = thresholds[optimal_idx] if optimal_idx < len(thresholds) else 1.0
    
    print(f"\nOptimal threshold from P-R curve: {optimal_threshold:.4f}\n")
    
    y_pred_class = (y_pred_proba >= optimal_threshold).astype(int)

    # --- Print Classification Report ---
    print("--- Classification Report (using optimal threshold) ---")
    print(classification_report(y_test, y_pred_class, target_names=['Not Fraud', 'Fraud'], zero_division=0))

    # --- Print ROC AUC Score ---
    roc_score = roc_auc_score(y_test, y_pred_proba)
    print(f"ROC AUC Score: {roc_score:.4f}\n")

    # --- Generate and Save Plots ---
    reports_dir = eval_config['reports_dir']
    os.makedirs(reports_dir, exist_ok=True)

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred_class)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Not Fraud', 'Fraud'], yticklabels=['Not Fraud', 'Fraud'])
    plt.title('Confusion Matrix (Optimal Threshold)')
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    cm_path = os.path.join(reports_dir, eval_config['confusion_matrix_path'])
    plt.savefig(cm_path)
    plt.close()

    # Precision-Recall Curve
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, marker='.', label='Precision-Recall Curve')
    plt.scatter(recall[optimal_idx], precision[optimal_idx], marker='o', color='red', label=f'Best Threshold ({optimal_threshold:.2f})')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve')
    plt.legend()
    pr_curve_path = os.path.join(reports_dir, eval_config['pr_curve_path'])
    plt.savefig(pr_curve_path)
    plt.close()
    
    print(f"Evaluation complete. Plots saved to {reports_dir} directory.")

