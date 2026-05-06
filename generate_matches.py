import os
import json

BASE_PATH = "public/data"

for map_folder in os.listdir(BASE_PATH):
    full_path = os.path.join(BASE_PATH, map_folder)

    if not os.path.isdir(full_path):
        continue

    matches = []

    for file in os.listdir(full_path):
        if file.endswith(".json") and "nakama" in file:
            match_id = file.replace("match_", "").replace(".json", "")
            matches.append(match_id)

    output = {
        "matches": matches
    }

    with open(os.path.join(full_path, "matches.json"), "w") as f:
        json.dump(output, f, indent=2)

    print(f"Generated matches.json for {map_folder}")