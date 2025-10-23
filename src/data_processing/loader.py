import pandas as pd
import os

def load_and_prep_data(data_config):
    """
    Finds and loads the core physician and prescriber datasets.
    Returns a dictionary of valid dataframes.
    """
    print("\n--- Loading and Preparing Core Datasets ---")
    
    loader_config = data_config['loader']
    col_config = data_config['columns']
    raw_data_path = loader_config['raw_data_path']
    
    keywords = ['physician', 'prescriber']
    paths = {}
    
    try:
        for keyword in keywords:
            key = loader_config.get(f"{keyword}_keyword")
            if not key: continue
            
            found_file = False
            for filename in os.listdir(raw_data_path):
                if key in filename and filename.lower().endswith('.csv'):
                    paths[keyword] = os.path.join(raw_data_path, filename)
                    found_file = True
                    break
            if not found_file:
                 print(f"Warning: Could not find data file for keyword: '{key}'")

    except FileNotFoundError:
        print(f"Error: The directory '{raw_data_path}' was not found.")
        return {}

    dataframes = {}
    for name, path in paths.items():
        print(f"Loading {name} data from: {os.path.basename(path)}")
        try:
            df = pd.read_csv(path, low_memory=False, encoding='utf-8')
        except UnicodeDecodeError:
            print(f"  -> UTF-8 failed. Retrying with 'latin1' encoding.")
            df = pd.read_csv(path, low_memory=False, encoding='latin1')

        npi_col = col_config[name]['provider_id']
        
        if npi_col in df.columns:
            df.rename(columns={npi_col: 'provider_id'}, inplace=True)
            print(f"Successfully loaded and prepped {name} data. Shape: {df.shape}")
            dataframes[name] = df
        else:
            print(f"  -> ERROR: Provider ID column '{npi_col}' not found in {os.path.basename(path)}. Skipping this file.")
            dataframes[name] = None

    return dataframes

