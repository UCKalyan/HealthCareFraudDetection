import pandas as pd
import os

# Paths
part_b_path = 'data/raw_data/MUP_PHY_R25_P05_V20_D23_Prov_Svc.csv'
part_d_path = 'data/raw_data/MUP_DPR_RY25_P04_V10_DY23_NPI.csv'
leie_path = 'data/raw_data/LEIE.csv'

print("--- Loading Datasets for Analysis ---")

# Load Part B (NPI only to save memory)
print("Loading Part B NPIs...")
part_b_df = pd.read_csv(part_b_path, usecols=['Rndrng_NPI'], low_memory=False)
part_b_npis = set(part_b_df['Rndrng_NPI'].unique())
print(f"Part B Unique NPIs: {len(part_b_npis)}")

# Load Part D (NPI only)
print("Loading Part D NPIs...")
part_d_df = pd.read_csv(part_d_path, usecols=['PRSCRBR_NPI'], low_memory=False)
part_d_npis = set(part_d_df['PRSCRBR_NPI'].unique())
print(f"Part D Unique NPIs: {len(part_d_npis)}")

# Load LEIE
print("Loading LEIE...")
if os.path.exists(leie_path):
    leie_df = pd.read_csv(leie_path, low_memory=False)
    leie_npis = set(leie_df['NPI'].unique())
    # Filter out 0 or NaN NPIs if any
    leie_npis = {npi for npi in leie_npis if npi != 0 and not pd.isna(npi)}
    print(f"LEIE Total Records: {len(leie_df)}")
    print(f"LEIE Unique NPIs: {len(leie_npis)}")
else:
    print("LEIE file not found.")
    leie_npis = set()

# --- Intersection Analysis ---
intersection = part_b_npis.intersection(part_d_npis)
part_b_only = part_b_npis - part_d_npis
part_d_only = part_d_npis - part_b_npis
union = part_b_npis.union(part_d_npis)

print("\n--- Overlap Statistics ---")
print(f"Providers in BOTH Part B and Part D: {len(intersection)}")
print(f"Providers in Part B ONLY: {len(part_b_only)}")
print(f"Providers in Part D ONLY: {len(part_d_only)}")
print(f"Total Unique Providers (Union): {len(union)}")

# --- LEIE Analysis ---
leie_in_union = leie_npis.intersection(union)
print("\n--- LEIE Coverage ---")
print(f"LEIE Providers found in our dataset: {len(leie_in_union)}")
print(f"LEIE Providers NOT in our dataset: {len(leie_npis - leie_in_union)}")
