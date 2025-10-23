import pandas as pd
import numpy as np
import networkx as nx
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler, OneHotEncoder
from sklearn.cluster import KMeans
import warnings

def create_advanced_features_and_split(physician_df, prescriber_df, config):
    """
    The final, definitive, re-architected, and leak-proof feature engineering pipeline.
    This version has been re-architected for clarity, correctness, and to fix all overlap errors.
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
        Prscrbr_Last_Org_Name=('Prscrbr_Last_Org_Name', 'first')
    ).reset_index()

    provider_profiles = pd.merge(phys_agg, presc_agg, on='provider_id', how='outer').fillna(0)
    
    provider_profiles['total_claim_cost'] = provider_profiles['total_service_cost'] + provider_profiles['total_drug_cost']
    provider_profiles['total_benes'] = provider_profiles['total_benes_phys'] + provider_profiles['total_benes_presc']
    total_actions = provider_profiles['total_services'] + provider_profiles['total_scripts']
    
    provider_profiles['cost_per_service'] = (provider_profiles['total_claim_cost'] / total_actions).replace([np.inf, -np.inf], 0).fillna(0)
    provider_profiles['services_per_bene'] = (total_actions / provider_profiles['total_benes']).replace([np.inf, -np.inf], 0).fillna(0)
    
    # --- Stage 2: Immediate Data Split ---
    train_df, test_df = train_test_split(provider_profiles, test_size=pp_config['test_size'], random_state=pp_config['random_state'])
    train_df, val_df = train_test_split(train_df, test_size=pp_config['validation_size'], random_state=pp_config['random_state'])
    
    # --- Stage 3: Create Labels & Fit Models using ONLY Training Set ---
    cost_stats = train_df.groupby('specialty')['total_claim_cost'].agg(['mean', 'std']).reset_index()
    spb_stats = train_df.groupby('specialty')['services_per_bene'].agg(['mean', 'std']).reset_index()
    z_threshold = pp_config['fraud_label_zscore_threshold']

    def calculate_zscores(df, stats_df, feature):
        merged = df.merge(stats_df, on='specialty', how='left').fillna({'mean': df[feature], 'std': 1})
        merged['zscore'] = (merged[feature] - merged['mean']) / merged['std'].replace(0, 1)
        return merged['zscore'].fillna(0).values

    y_train = calculate_zscores(train_df, cost_stats, 'total_claim_cost') > z_threshold
    y_val = calculate_zscores(val_df, cost_stats, 'total_claim_cost') > z_threshold
    y_test = calculate_zscores(test_df, cost_stats, 'total_claim_cost') > z_threshold

    # Fit Clustering Model
    clustering_config = pp_config['feature_engineering']['clustering']
    kmeans = KMeans(n_clusters=clustering_config['n_clusters'], random_state=pp_config['random_state'], n_init=10)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        kmeans.fit(train_df[clustering_config['features']])
    
    # Fit Graph Model
    G = nx.from_pandas_edgelist(train_df.dropna(subset=['provider_id', 'specialty']), 'provider_id', 'specialty', create_using=nx.Graph())
    pagerank = nx.pagerank(G)
    median_pagerank = pd.Series(pagerank).median()
    
    # --- Stage 4: A Single, Unified Feature Engineering Function ---
    archetype_cols = [f'provider_archetype_{i}' for i in range(clustering_config['n_clusters'])]
    
    def engineer_final_features(df, kmeans_model, pagerank_map):
        df_out = pd.DataFrame(index=df.index)
        
        # 1. Non-Leaky Behavioral Features
        df_out['spb_z_tanh'] = np.tanh(calculate_zscores(df, spb_stats, 'services_per_bene'))
        df_out['cost_per_service'] = df['cost_per_service']
        df_out['services_per_bene'] = df['services_per_bene']

        # 2. Archetype Features (using pre-fitted model)
        clusters = kmeans_model.predict(df[clustering_config['features']])
        encoder = OneHotEncoder(categories=[range(clustering_config['n_clusters'])], sparse_output=False, handle_unknown='ignore')
        archetypes = encoder.fit_transform(clusters.reshape(-1, 1))
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
    # We join the final features back to the original split dataframes
    train_full = train_df.join(X_train, rsuffix='_eng')
    val_full = val_df.join(X_val, rsuffix='_eng')
    test_full = test_df.join(X_test, rsuffix='_eng')
    all_profiles_engineered = pd.concat([train_full, val_full, test_full])
    
    print("--- Preprocessing Finished ---")
    return X_train_scaled, X_val_scaled, X_test_scaled, y_train, y_val, y_test, final_feature_columns, all_profiles_engineered, artifacts

