import yaml

def load_config(config_path='config.yaml'):
    """
    Loads the YAML configuration file.

    Args:
        config_path (str): The path to the configuration file.

    Returns:
        dict: A dictionary containing the configuration parameters.
    """
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_path}")
        exit()
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        exit()

