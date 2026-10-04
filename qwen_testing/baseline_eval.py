from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import json
import time
import psutil
import re
from pathlib import Path
from datetime import datetime

# ========== CONFIG ==========
MODEL_PATH = "../base_model_weights"
DATA_PATH = "../data/gsm8k_pilot_50.json"
OUTPUT_PATH = "baseline_results.json"
MAX_NEW_TOKENS = 256
# ============================

def extract_final_answer(text):
    """Extract the last number from the generated text (simple GSM8K style)."""
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", text.replace(",", ""))
    if numbers:
        return numbers[-1]
    return None

def normalize_answer(ans):
    if ans is None:
        return None
    return ans.strip().lower()

print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float16,
    device_map="cpu"
)

print("Loading pilot data...")
with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

results = []
correct = 0
total_time = 0.0
peak_ram = psutil.virtual_memory().used

print(f"\nRunning baseline on {len(data)} examples...\n")

for i, example in enumerate(data):
    question = example["question"]
    gold = example["answer"].split("####")[-1].strip()  # GSM8K format

    prompt = f"Question: {question}\nAnswer:"

    inputs = tokenizer(prompt, return_tensors="pt")

    start = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False  # deterministic
        )
    elapsed = time.time() - start
    total_time += elapsed

    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
    pred = extract_final_answer(generated)

    is_correct = normalize_answer(pred) == normalize_answer(gold)
    if is_correct:
        correct += 1

    # Track peak RAM
    current_ram = psutil.virtual_memory().used
    if current_ram > peak_ram:
        peak_ram = current_ram

    results.append({
        "id": i,
        "question": question,
        "gold": gold,
        "prediction": pred,
        "correct": is_correct,
        "latency_sec": round(elapsed, 2),
        "generated_text": generated
    })

    print(f"[{i+1}/{len(data)}] Correct: {is_correct} | Latency: {elapsed:.2f}s")

# ========== SUMMARY ==========
accuracy = correct / len(data)
avg_latency = total_time / len(data)

summary = {
    "timestamp": str(datetime.now()),
    "model": "Qwen3-0.6B",
    "precision": "float16 (baseline)",
    "num_examples": len(data),
    "accuracy": round(accuracy, 4),
    "correct": correct,
    "avg_latency_sec": round(avg_latency, 2),
    "peak_ram_gb": round(peak_ram / 1e9, 2),
    "results": results
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print("\n========== BASELINE RESULTS ==========")
print(f"Accuracy:          {accuracy:.2%}")
print(f"Correct:           {correct}/{len(data)}")
print(f"Avg Latency:       {avg_latency:.2f} sec/example")
print(f"Peak RAM:          {peak_ram / 1e9:.2f} GB")
print(f"Results saved to:  {OUTPUT_PATH}")