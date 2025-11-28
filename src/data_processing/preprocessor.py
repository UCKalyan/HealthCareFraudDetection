import pandas as pd
import numpy as np
import networkx as nx
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler, OneHotEncoder
from sklearn.cluster import KMeans
import warnings

def create_advanced_features_and_split(physician_df, prescriber_df, leie_df, config):
    """
    The final, definitive, re-architected, and leak-proof feature engineering pipeline.
    This version includes LEIE integration and improved data merging.
    """
    print("\n--- Starting Advanced Feature Engineering ---")
    
    pp_config = config['preprocessor']
    col_config = config['data']['columns']
    
    # --- Stage 1: Create Unified Provider Profiles ---
    phys_agg = physician_df.groupby(['provider_id', col_config['physician']['specialty']]).agg(
        total_service_cost=(col_config['physician']['claim_cost'], 'sum'),
        total_services=(col_config['physician']['service_count'], 'sum'),
        total_benes_phys=(col_config['physician']['bene_count'], 'sum')
    ).reset_index().rename(columns={col_config['physician']['specialty']: 'specialty'})
    
    presc_agg = prescriber_df.groupby('provider_id').agg(
        total_drug_cost=(col_config['prescriber']['claim_cost'], 'sum'),
        total_scripts=(col_config['prescriber']['service_count'], 'sum'),
        total_benes_presc=(col_config['prescriber']['bene_count'], 'sum'),
        Prscrbr_First_Name=('Prscrbr_First_Name', 'first'),
        Prscrbr_Last_Org_Name=('Prscrbr_Last_Org_Name', 'first'),
        prescriber_specialty=(col_config['prescriber']['specialty'], 'first') # Capture Part D Specialty
    ).reset_index()

    # Outer Join to keep all providers
    provider_profiles = pd.merge(phys_agg, presc_agg, on='provider_id', how='outer')
    
    # --- Improved Data Merging (Coalesce Logic) ---
    # 1. Coalesce Specialty: Use Part B if available, else Part D
    provider_profiles['specialty'] = provider_profiles['specialty'].fillna(provider_profiles['prescriber_specialty']).fillna('Unknown')
    provider_profiles.drop(columns=['prescriber_specialty'], inplace=True)
    
    # 2. Add Missing Data Indicators
    provider_profiles['has_part_b'] = provider_profiles['total_services'].notna().astype(int)
    provider_profiles['has_part_d'] = provider_profiles['total_scripts'].notna().astype(int)
    
    # 3. Fill Numeric NaNs with 0
    provider_profiles.fillna(0, inplace=True)
    
    provider_profiles['total_claim_cost'] = provider_profiles['total_service_cost'] + provider_profiles['total_drug_cost']
    provider_profiles['total_benes'] = provider_profiles['total_benes_phys'] + provider_profiles['total_benes_presc']
    total_actions = provider_profiles['total_services'] + provider_profiles['total_scripts']
    
    provider_profiles['cost_per_service'] = (provider_profiles['total_claim_cost'] / total_actions).replace([np.inf, -np.inf], 0).fillna(0)
    provider_profiles['services_per_bene'] = (total_actions / provider_profiles['total_benes']).replace([np.inf, -np.inf], 0).fillna(0)
    
    # --- Stage 2: Immediate Data Split ---
    train_df, test_df = train_test_split(provider_profiles, test_size=pp_config['test_size'], random_state=pp_config['random_state'])
    train_df, val_df = train_test_split(train_df, test_size=pp_config['validation_size'], random_state=pp_config['random_state'])
    
    # --- Stage 3: Create Labels (Configurable) ---
    labeling_method = pp_config.get('labeling_method', 'unsupervised')
    print(f"  - Generating labels using method: {labeling_method.upper()}")

    if labeling_method == 'supervised' and leie_df is not None:
        print("    > Using LEIE Ground Truth.")
        fraud_npis = set(leie_df['provider_id'].unique())
        y_train = train_df['provider_id'].isin(fraud_npis).astype(int)
        y_val = val_df['provider_id'].isin(fraud_npis).astype(int)
        y_test = test_df['provider_id'].isin(fraud_npis).astype(int)
        print(f"    > Fraud cases in Train: {y_train.sum()} / {len(y_train)}")
    else:
        if labeling_method == 'supervised':
            print("    > WARNING: LEIE data missing despite 'supervised' config. Falling back to Unsupervised (Z-score).")
        else:
            print("    > Using Unsupervised Anomaly Detection (Z-score).")
            
        cost_stats = train_df.groupby('specialty')['total_claim_cost'].agg(['mean', 'std']).reset_index()
        spb_stats = train_df.groupby('specialty')['services_per_bene'].agg(['mean', 'std']).reset_index() # <-- Added this line
        z_threshold = pp_config['fraud_label_zscore_threshold']
        
        def calculate_zscores(df, stats_df, feature):
            merged = df.merge(stats_df, on='specialty', how='left').fillna({'mean': df[feature], 'std': 1})
            merged.loc[merged['std'] == 0, 'std'] = 1
            merged['zscore'] = (merged[feature] - merged['mean']) / merged['std']
            return merged['zscore'].fillna(0).values

        y_train = calculate_zscores(train_df, cost_stats, 'total_claim_cost') > z_threshold
        y_val = calculate_zscores(val_df, cost_stats, 'total_claim_cost') > z_threshold
        y_test = calculate_zscores(test_df, cost_stats, 'total_claim_cost') > z_threshold

    # Fit Clustering Model
    print("  - Creating behavioral cluster features (Archetypes)...")
    clustering_config = pp_config['feature_engineering']['clustering']
    kmeans = KMeans(n_clusters=clustering_config['n_clusters'], random_state=pp_config['random_state'], n_init=10)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        kmeans.fit(train_df[clustering_config['features']])
    
    # Fit Graph Model
    print("  - Creating network graph features (Centrality)...")
    G = nx.from_pandas_edgelist(train_df.dropna(subset=['provider_id', 'specialty']), 'provider_id', 'specialty', create_using=nx.Graph())
    pagerank = nx.pagerank(G)
    median_pagerank = pd.Series(pagerank).median()
    
    # Fit OneHotEncoder for clusters
    encoder = OneHotEncoder(categories=[range(clustering_config['n_clusters'])], sparse_output=False, handle_unknown='ignore')
    train_clusters_for_fit = kmeans.predict(train_df[clustering_config['features']])
    encoder.fit(train_clusters_for_fit.reshape(-1, 1))

    # --- Stage 4: A Single, Unified Feature Engineering Function ---
    archetype_cols = [f'provider_archetype_{i}' for i in range(clustering_config['n_clusters'])]
    
    def engineer_final_features(df, kmeans_model, pagerank_map):
        df_out = pd.DataFrame(index=df.index)
        
        # 1. Non-Leaky Behavioral Features
        df_out['spb_z_tanh'] = np.tanh(calculate_zscores(df, spb_stats, 'services_per_bene'))
        df_out['cost_per_service'] = df['cost_per_service']
        df_out['services_per_bene'] = df['services_per_bene']
        df_out['has_part_b'] = df['has_part_b']
        df_out['has_part_d'] = df['has_part_d']

        # 2. Archetype Features (using pre-fitted model)
        clusters = kmeans_model.predict(df[clustering_config['features']])
        archetypes = encoder.transform(clusters.reshape(-1, 1))
        df_out[archetype_cols] = archetypes

        # 3. Graph Features (using pre-calculated ranks)
        df_out['pagerank_centrality'] = df['provider_id'].map(pagerank_map).fillna(median_pagerank)
        
        return df_out

    X_train = engineer_final_features(train_df, kmeans, pagerank)
    X_val = engineer_final_features(val_df, kmeans, pagerank)
    X_test = engineer_final_features(test_df, kmeans, pagerank)
    
    final_feature_columns = list(X_train.columns)
    print(f"Data shapes after feature engineering. Training: {X_train.shape}, Validation: {X_val.shape}, Test: {X_test.shape}")
    
    # --- Stage 5: Final Scaling ---
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    artifacts = {
        'cost_stats': cost_stats, 'spb_stats': spb_stats, 'kmeans_model': kmeans,
        'median_pagerank': median_pagerank, 'scaler': scaler
    }
    
    # THE DEFINITIVE FIX for the feature store and the ValueError
    # We create the feature store by joining the *newly created features* back to the *original profiles*.
    # This avoids any column overlap.
    all_features_df = pd.concat([X_train, X_val, X_test])
    
    # We must drop the overlapping columns from the original profiles BEFORE joining
    cols_to_drop = [col for col in ['cost_per_service', 'services_per_bene', 'has_part_b', 'has_part_d'] if col in provider_profiles.columns]
    provider_profiles_base = provider_profiles.drop(columns=cols_to_drop)
    
    all_profiles_engineered = provider_profiles_base.join(all_features_df)
    all_profiles_engineered.dropna(subset=final_feature_columns, inplace=True) # Clean up rows
    
    print("--- Preprocessing Finished ---")
    return X_train_scaled, X_val_scaled, X_test_scaled, y_train, y_val, y_test, final_feature_columns, all_profiles_engineered, artifacts

def load_features_and_split(feature_store_path, config, leie_df=None):
    """
    Loads pre-computed features from CSV, splits, and prepares for training.
    Bypasses raw data loading and feature engineering.
    """
    print(f"\n--- Loading Pre-computed Features from {feature_store_path} ---")
    df = pd.read_csv(feature_store_path)
    
    # Ensure numeric columns are numeric
    numeric_cols = ['total_claim_cost', 'services_per_bene', 'spb_z_tanh', 'cost_per_service', 'pagerank_centrality']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    pp_config = config['preprocessor']
    
    # --- Split ---
    train_df, test_df = train_test_split(df, test_size=pp_config['test_size'], random_state=pp_config['random_state'])
    train_df, val_df = train_test_split(train_df, test_size=pp_config['validation_size'], random_state=pp_config['random_state'])
    
    # --- Re-create Targets (y) ---
    # --- Re-create Targets (y) ---
    labeling_method = pp_config.get('labeling_method', 'unsupervised')
    print(f"  - Generating labels using method: {labeling_method.upper()}")
    
    # We need to recalculate stats on train_df to avoid leakage, just like in the full pipeline
    cost_stats = train_df.groupby('specialty')['total_claim_cost'].agg(['mean', 'std']).reset_index()
    z_threshold = pp_config['fraud_label_zscore_threshold']
    
    def calculate_zscores(df, stats_df, feature):
        merged = df.merge(stats_df, on='specialty', how='left').fillna({'mean': df[feature], 'std': 1})
        merged.loc[merged['std'] == 0, 'std'] = 1
        merged['zscore'] = (merged[feature] - merged['mean']) / merged['std']
        return merged['zscore'].fillna(0).values

    if labeling_method == 'supervised' and leie_df is not None:
        print("    > Using LEIE Ground Truth.")
        # Ensure provider_id is in the dataframe. It should be if we loaded the feature store.
        # But feature store might not have provider_id if it was dropped? 
        # Wait, provider_id is the index or a column? 
        # In create_advanced_features_and_split, we join back to provider_profiles_base which has provider_id.
        # The CSV saved is all_profiles_engineered, which HAS provider_id.
        
        fraud_npis = set(leie_df['provider_id'].unique())
        y_train = train_df['provider_id'].isin(fraud_npis).astype(int)
        y_val = val_df['provider_id'].isin(fraud_npis).astype(int)
        y_test = test_df['provider_id'].isin(fraud_npis).astype(int)
        print(f"    > Fraud cases in Train: {y_train.sum()} / {len(y_train)}")
    else:
        if labeling_method == 'supervised':
             print("    > WARNING: LEIE data missing or not passed. Falling back to Unsupervised (Z-score).")
        else:
             print("    > Using Unsupervised Anomaly Detection (Z-score).")

        y_train = calculate_zscores(train_df, cost_stats, 'total_claim_cost') > z_threshold
        y_val = calculate_zscores(val_df, cost_stats, 'total_claim_cost') > z_threshold
        y_test = calculate_zscores(test_df, cost_stats, 'total_claim_cost') > z_threshold
    
    # --- Select Features (X) ---
    # We need to identify the feature columns. 
    # Based on the CSV header: spb_z_tanh, cost_per_service, services_per_bene, provider_archetype_*, pagerank_centrality
    # Note: services_per_bene is in the CSV, but in the full pipeline it's used.
    # Let's use the same list as in engineer_final_features
    
    feature_cols = ['spb_z_tanh', 'cost_per_service', 'services_per_bene', 'pagerank_centrality', 'has_part_b', 'has_part_d']
    feature_cols += [c for c in df.columns if 'provider_archetype_' in c]
    
    X_train = train_df[feature_cols]
    X_val = val_df[feature_cols]
    X_test = test_df[feature_cols]
    
    print(f"Data shapes. Training: {X_train.shape}, Validation: {X_val.shape}, Test: {X_test.shape}")
    
    # --- Scaling ---
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    return X_train_scaled, X_val_scaled, X_test_scaled, y_train, y_val, y_test, feature_cols, df, {'scaler': scaler}