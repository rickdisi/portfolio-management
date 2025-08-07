import json, os
from pathlib import Path
# 1) Figure out where config.json lives:
BASE = Path(__file__).resolve().parent.parent
path = os.path.join(BASE, "config.json")

# 2) Load it exactly once:
with open(path) as f:
    _data = json.load(f)

# 3) Expose values as module globals:
globals().update(_data)
