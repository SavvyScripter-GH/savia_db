import json

with open("index.json", "r", encoding="utf-8") as f:
    data = json.load(f)

remove_difficulties = {"Hard", "Medium", "Easy"}

filtered_data = {
    key: value
    for key, value in data.items()
    if value.get("difficulty_name") not in remove_difficulties
}

with open("filtered_maps.json", "w", encoding="utf-8") as f:
    json.dump(filtered_data, f, indent=2)

print(f"Removed {len(data) - len(filtered_data)} maps.")
print(f"Remaining maps: {len(filtered_data)}")