import numpy as np
import pandas as pd
from .base_agent import BaseAgent

class AnalystAgent(BaseAgent):
    def __init__(self, config, model, explainer, scaler, feature_cols):
        super().__init__(config)
        self.model = model
        self.explainer = explainer
        self.scaler = scaler
        self.feature_cols = feature_cols

    def run(self, provider_data):
        """
        Runs the deep learning model and SHAP explainer.
        """
        # Prepare data
        if isinstance(provider_data, pd.Series):
            provider_data = provider_data.to_frame().T
            
        provider_data_aligned = provider_data.reindex(columns=self.feature_cols, fill_value=0)
        feature_vector = self.scaler.transform(provider_data_aligned)
        
        # Predict
        final_score = self.model.predict(feature_vector)[0][0]
        
        # Explain
        shap_values = self.explainer.shap_values(feature_vector)
        
        # Handle different SHAP return types (list of arrays vs single array)
        if isinstance(shap_values, list):
            # For binary classification, it often returns [neg_class_shap, pos_class_shap]
            # We want the positive class (index 1) if 2 classes, or index 0 if 1 output
            if len(shap_values) == 2:
                 shap_values_flat = shap_values[1].flatten()
            else:
                 shap_values_flat = shap_values[0].flatten()
        else:
            shap_values_flat = np.array(shap_values).flatten()
            
        # Synthesize Feature Analysis for LLM
        feature_analysis_str = ""
        shap_data = []
        
        # Archetype Mapping
        name_map = {
            "provider_archetype_0": "Standard Practice Pattern",
            "provider_archetype_1": "High-Value Specialist",
            "provider_archetype_2": "Tier 2 High Cost",
            "provider_archetype_3": "Elevated Risk Profile",
            "provider_archetype_4": "Extreme Outlier"
        }

        for i, raw_name in enumerate(self.feature_cols):
            provider_value = float(feature_vector[0][i])
            shap_value = float(shap_values_flat[i])
            
            display_name = name_map.get(raw_name, raw_name)
            
            shap_data.append({"name": display_name, "value": shap_value})
            
            feature_analysis_str += f"- **Feature:** '{display_name}' | **Provider's Value:** {provider_value:.2f} | **Impact on Fraud Score (SHAP):** {shap_value:+.4f}\n"

        risk_level = "High" if final_score > 0.75 else ("Medium" if final_score > 0.30 else "Low")
        top_factor_idx = np.argmax(np.abs(shap_values))
        raw_top_factor = self.feature_cols[top_factor_idx]
        top_factor = name_map.get(raw_top_factor, raw_top_factor)

        # Generate rich HTML analysis directly (no LLM needed)
        # Build top 3 drivers HTML
        sorted_shap = sorted(shap_data, key=lambda x: abs(x['value']), reverse=True)
        top_3_drivers = sorted_shap[:3]
        
        drivers_html = "<ul class='space-y-2 mt-2'>\n"
        for i, item in enumerate(top_3_drivers, 1):
            impact_color = "text-red-600" if item['value'] > 0 else "text-green-600"
            impact_sign = "+" if item['value'] > 0 else ""
            drivers_html += f"<li class='text-sm'><b>{i}. {item['name']}</b>: <span class='{impact_color} font-semibold'>{impact_sign}{item['value']:.3f}</span> impact on risk score</li>\n"
        drivers_html += "</ul>"
        
        # Risk level specific message
        if risk_level == "High":
            risk_message = "<span class='text-red-600 font-bold'>⚠️ HIGH RISK</span> - Immediate investigation recommended"
        elif risk_level == "Medium":
            risk_message = "<span class='text-yellow-600 font-bold'>⚡ MEDIUM RISK</span> - Review recommended"
        else:
            risk_message = "<span class='text-green-600 font-bold'>✓ LOW RISK</span> - Standard monitoring"
        
        analysis_text = f"""
        <div class="space-y-2">
            <div class="bg-blue-50/40 p-3 rounded-lg">
                <h3 class="text-sm font-bold text-slate-700 mb-2">📊 Risk Score Analysis</h3>
                <p class="text-sm"><b>Overall Assessment:</b> {risk_message}</p>
                <p class="text-sm"><b>Risk Score:</b> <span class="font-mono font-bold text-lg">{final_score:.4f}</span></p>
            </div>
            
            <div class="bg-purple-50/40 p-3 rounded-lg">
                <h3 class="text-sm font-bold text-slate-700 mb-2">🎯 Key Risk Drivers</h3>
                <p class="text-xs text-slate-600 mb-1">The following features contributed most significantly to this risk assessment:</p>
                {drivers_html}
            </div>
        </div>
        """

        # Create features dict with mapped names
        features_dict = {}
        raw_features = provider_data_aligned.iloc[0].to_dict()
        for k, v in raw_features.items():
            features_dict[name_map.get(k, k)] = v

        return {
            "agent": "Analyst",
            "risk_level": risk_level,
            "final_score": float(final_score),
            "base_value": float(self.explainer.expected_value),
            "top_factor": top_factor,
            "shap_data": shap_data,
            "analysis_text": analysis_text,
            "features": features_dict
        }
