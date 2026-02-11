import yaml
import os
import re

def load_config(config_path='config.yaml'):
    """
    Loads the YAML configuration file with environment variable substitution.
    Supports ${VAR_NAME} syntax.
    """
    path_matcher = re.compile(r'\$\{([^}^{]+)\}')

    def path_constructor(loader, node):
        value = node.value
        match = path_matcher.match(value)
        env_var = match.group(1)
        return os.environ.get(env_var) or value

    yaml.add_implicit_resolver('!env', path_matcher, None, yaml.SafeLoader)
    yaml.add_constructor('!env', path_constructor, yaml.SafeLoader)

    try:
        with open(config_path, 'r') as file:
            # First load as string to do regex replacement for simple values
            content = file.read()
            
        print(f"DEBUG: Available Env Vars: {[k for k in os.environ.keys() if 'PATH' in k or 'MODEL' in k]}")
        
        # Replace ${VAR} with value from env
        def replace_env(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0)) # Return original if not found
            
        content = path_matcher.sub(replace_env, content)
        
        config = yaml.safe_load(content)
        return config
        
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_path}")
        exit()
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        exit()

