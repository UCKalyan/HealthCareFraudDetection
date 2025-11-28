import os
import json
import numpy as np
from urllib import request, error

def generate_llm_report(explainer, shap_values, data_sample, model, feature_names, config):
    """
    Takes clean SHAP explanation data and uses an LLM to generate a fraud analysis report.
    Receives the feature_names list as a parameter.
    """
    if not config['enabled']:
        print("\n--- LLM Reporting Skipped (disabled in config) ---")
        return

    print("\n--- Initializing AI Fraud Analyst Agent ---")
    
    instance_index = 0
    
    base_value = explainer.expected_value
    shap_instance_values = shap_values[instance_index, :]
    data_instance_values = data_sample.iloc[instance_index, :]
    
    final_prediction_score = model.predict(data_instance_values.values.reshape(1, -1))[0][0]

    system_prompt = config['system_prompt']
    user_prompt_template = config['user_prompt_template']

    feature_analysis_str = ""
    for i, name in enumerate(feature_names):
        provider_value = float(data_instance_values.iloc[i])
        shap_value = float(shap_instance_values[i])

        feature_analysis_str += (
            f"- **Feature:** '{name}' | "
            f"**Provider's Value:** {provider_value:.2f} | "
            f"**Impact on Fraud Score (SHAP):** {shap_value:+.4f}\n"
        )

    user_prompt = user_prompt_template.format(
        provider_name="Test Provider",
        npi="N/A",
        base_value=base_value,
        final_prediction_score=final_prediction_score,
        feature_analysis=feature_analysis_str
    )
    
    print("Sending data to the Gemini LLM for analysis...")
    api_key = config['api_key']
    api_url = f"{config['api_url']}?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]}
    }

    try:
        req = request.Request(api_url, method="POST", headers={"Content-Type": "application/json"}, data=json.dumps(payload).encode("utf-8"))
        with request.urlopen(req) as response:
            if response.status == 200:
                result = json.loads(response.read().decode())
                report_text = result['candidates'][0]['content']['parts'][0]['text']
                
                reports_dir = config['reports_dir']
                report_path = os.path.join(reports_dir, config['report_filename'])
                with open(report_path, 'w') as f:
                    f.write(report_text)
                print(f"Successfully generated and saved AI analysis to: {report_path}")

            else:
                print(f"Error from Gemini API: {response.status} - {response.read().decode()}")

    except error.HTTPError as e:
        print(f"HTTP Error calling Gemini API: {e.code} {e.reason}")
        print(f"Response body: {e.read().decode()}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    print("--- AI Fraud Analyst Agent Finished ---")

