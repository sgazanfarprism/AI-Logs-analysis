import os
import yaml
from pathlib import Path
import sys

def substitute_env_variables(content):
    import re
    pattern = r'\$\{([^}]+)\}'
    def replace_var(match):
        var_name = match.group(1)
        value = os.getenv(var_name)
        if value is None:
            raise Exception(f"Required environment variable not set: {var_name}")
        return value
    return re.sub(pattern, replace_var, content)

def test_config(path):
    print(f"Testing {path}...")
    try:
        if not Path(path).exists():
            print(f"  ERROR: File does not exist")
            return
        with open(path, 'r') as f:
            content = f.read()
        content = substitute_env_variables(content)
        config = yaml.safe_load(content)
        print(f"  SUCCESS: Loaded and substituted")
    except Exception as e:
        print(f"  ERROR: {e}")

if __name__ == "__main__":
    configs = [
        "config/elasticsearch.yaml",
        "config/ai.yaml",
        "config/smtp.yaml"
    ]
    for c in configs:
        test_config(c)
