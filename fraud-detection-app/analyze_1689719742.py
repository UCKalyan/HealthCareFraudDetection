import sqlite3, pandas as pd, numpy as np, joblib, json, os

os.environ['TF_USE_LEGACY_KERAS'] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

import tensorflow as tf
try: tf.config.set_visible_devices([], 'GPU')
except: pass
import keras, shap

npi = 1689719742
conn = sqlite3.connect('../shared-data/databases/providers.db')
row = conn.execute('SELECT * FROM providers WHERE provider_id = ?', (npi,)).fetchone()
if not row:
    print(f'NPI {npi} not found in database.')
    exit()

cols = [c[0] for c in conn.execute('PRAGMA table_info(providers)').fetchall()]
prov = dict(zip(cols, row))
conn.close()

print(f'\n=== Provider Details for NPI {npi} ===')
print(f'Specialty: ' + str(prov.get('specialty', 'Unknown')))
print(f'Risk Score: ' + str(prov.get('risk_score')))
print(f'agent_analysed_at: ' + str(prov.get('agent_analysed_at')))

print('\n=== Raw Features ===')
print(f'cost_per_service: ${prov.get("cost_per_service", 0):.2f}')
print(f'services_per_bene: {prov.get("services_per_bene", 0):.2f}')
print(f'total_claim_cost: ${prov.get("total_claim_cost", 0):.2f}')
print(f'total_service_cost: ${prov.get("total_service_cost", 0):.2f}')
print(f'total_benes: {prov.get("total_benes")}')

model = keras.models.load_model('models/fraud_detection_model.keras')
scaler = joblib.load('models/robust_scaler.joblib')
with open('models/specialty_stats.json') as f:
    stats = json.load(f)
feature_cols = stats['final_feature_columns']
explainer = joblib.load('[NOT_FOUND]')

print('\n=== Feature Vectors ===')
raw_vec = []
for col in feature_cols:
    val = prov.get(col, 0.0)
    if val is None: val = 0.0
    raw_vec.append(float(val))
    print(f'{col}: {val}')

X = np.array([raw_vec])
X_scaled = scaler.transform(X)
pred = model.predict(X_scaled, verbose=0)[0][0]
print(f'\nModel Prediction Re-run: {pred:.6f}')

print('\n=== SHAP Analysis (Why) ===')
shap_values = explainer.shap_values(X_scaled)
if isinstance(shap_values, list):
    if len(shap_values) == 2: sv = np.array(shap_values[1]).flatten()
    else: sv = np.array(shap_values[0]).flatten()
else:
    sv = np.array(shap_values).flatten()

sv = sv[:len(feature_cols)] if len(sv) > len(feature_cols) else np.pad(sv, (0, len(feature_cols)-len(sv)))

shap_dict = {feature_cols[i]: sv[i] for i in range(len(feature_cols))}
sorted_shap = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)

for feat, val in sorted_shap:
    direction = 'Increases risk' if val > 0 else 'Decreases risk'
    print(f'{feat}: {val:+.4f} ({direction})')
