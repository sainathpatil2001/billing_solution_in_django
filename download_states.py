import urllib.request
import json
import os

url = "https://raw.githubusercontent.com/sab99r/Indian-States-And-Districts/master/states-and-districts.json"
try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
        
    # Save as specific JS variable for easy embedding
    output_dir = os.path.join("static", "js")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "indian_states_districts.js")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("const INDIAN_STATES_DATA = ")
        json.dump(data, f, indent=4)
        f.write(";")
        
    print(f"Successfully saved to {output_path}")
except Exception as e:
    print(f"Error: {e}")
