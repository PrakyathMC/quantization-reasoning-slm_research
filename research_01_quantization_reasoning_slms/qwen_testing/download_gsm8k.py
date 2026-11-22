from datasets import load_dataset
import json
from pathlib import Path

# Create data folder
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# Load GSM8K test split
dataset = load_dataset("openai/gsm8k", "main", split="test")

# Take a small pilot set (first 50 examples)
pilot = dataset.select(range(50))

# Save as clean JSON
output_path = data_dir / "gsm8k_pilot_50.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(list(pilot), f, indent=2, ensure_ascii=False)

print(f"Saved {len(pilot)} examples to {output_path}")
print("Example question:")
print(pilot[0]["question"])
print("Answer:", pilot[0]["answer"])