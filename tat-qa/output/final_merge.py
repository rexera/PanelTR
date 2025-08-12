import json
import re

input_file = '/./PanelTR/tat-qa/output/MAS_ds_dev_0106_20.json'
output_file = '/./PanelTR/tat-qa/output/MAS_ds_dev_0106_20_final.json'

# Read file content
with open(input_file, 'r', encoding='utf-8') as f:
    file_content = f.read()

# Use regex to replace `}{` with `},{`
fixed_content = re.sub(r'}\s*{', '},{', file_content)

# Wrap the fixed JSON content into an array
fixed_json = "[" + fixed_content + "]"

# Parse the fixed JSON data
try:
    data = json.loads(fixed_json)
except json.JSONDecodeError as e:
    print(f"JSON parsing error: {e}")
    exit(1)

# Merge dictionaries
merged_dict = {}
for item in data:
    for key, value in item.items():
        if isinstance(value, list) and len(value) == 4:
            # Remove the first and fourth fields
            merged_dict[key] = [value[1], value[2]]

# Write the merged dictionary to a new JSON file
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(merged_dict, f, ensure_ascii=False, indent=4)  # Keep the output formatted