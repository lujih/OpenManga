import os
import re
import yaml


def load_config(path: str) -> dict:
    with open(path) as f:
        raw = f.read()
    raw = os.path.expandvars(raw)
    raw = re.sub(r'\$\{[^}]+\}', '', raw)
    return yaml.safe_load(raw)
