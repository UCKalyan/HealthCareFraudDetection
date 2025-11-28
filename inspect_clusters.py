import joblib
import numpy as np

def inspect_clusters():
    try:
        # Load the model
        kmeans = joblib.load('models/kmeans_model.joblib')
        centers = kmeans.cluster_centers_
        
        print("\n--- K-Means Cluster Analysis ---")
        print("Features: [Cost per Service, Services per Beneficiary]")
        print("-" * 50)
        
        for i, center in enumerate(centers):
            cost = center[0]
            vol = center[1]
            
            # Determine a rough label based on the values
            label = []
            if cost > 150: label.append("High Cost")
            elif cost < 50: label.append("Low Cost")
            else: label.append("Medium Cost")
            
            if vol > 5: label.append("High Volume")
            elif vol < 2: label.append("Low Volume")
            else: label.append("Medium Volume")
            
            desc = ", ".join(label)
            
            print(f"Archetype {i}: Cost=${cost:7.2f} | Vol={vol:5.2f}  -->  {desc}")
            
    except Exception as e:
        print(f"Error loading model: {e}")
        print("Make sure 'models/kmeans_model.joblib' exists.")

if __name__ == "__main__":
    inspect_clusters()
