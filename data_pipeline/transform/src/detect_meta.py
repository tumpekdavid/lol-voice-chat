import json

data = json.load(open("data/Aatrox.json", encoding="utf-8"))
fields = set()
for slot, abilities in data["abilities"].items():
    for ability in abilities:
        fields.update(ability.keys())
print(sorted(fields))
