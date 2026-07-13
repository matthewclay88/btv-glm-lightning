import json
from datetime import datetime, timezone

data = {
    "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "counts": {
        "5": 0,
        "15": 0,
        "30": 0,
        "60": 0
    }
}

with open("data/lightning.json", "w") as f:
    json.dump(data, f, indent=2)

print("lightning.json created!")
