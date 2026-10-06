from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import json
import time
import psutil
import re
from pathlib import Path
from datetime import datetime

# ========== CONFIG ==========
ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT_DIR / "qwen_base_model_weights"
DATA_PATH = ROOT_DIR / "data" / "gsm8k_pilot_50.json"
OUTPUT_PATH = Path(__file__).resolve().parent / "baseline_results.json"
MAX_NEW_TOKENS = 256
# ============================

def extract_final_answer(text):
    """Extract a GSM8K-style final answer from generated text."""
    boxed = re.findall(r"\\boxed\{\s*([^{}]+?)\s*\}", text)
    if boxed:
        text = boxed[-1]

    answer_markers = re.findall(
        r"(?:final answer|answer)\s*[:=]?\s*\$?\s*([-+]?\d[\d,]*(?:\.\d+)?)",
        text,
        flags=re.IGNORECASE,
    )
    if answer_markers:
        return answer_markers[-1].replace(",", "")

    numbers = re.findall(r"[-+]?\d[\d,]*(?:\.\d+)?", text)
    if numbers:
        return numbers[-1].replace(",", "")
    return None

def normalize_answer(ans):
    if ans is None:
        return None
    return ans.strip().lower()

print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype="auto",
    device_map="cpu"
)
model.eval()

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

    messages = [{
        "role": "user",
        "content": (
            f"Solve this GSM8K problem. Give a brief calculation and end with "
            f"the final numeric answer in the format \\boxed{{number}}.\n\n{question}"
        ),
    }]
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
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

    generated_ids = outputs[0][inputs.input_ids.shape[1]:]
    generated = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
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
    "precision": "model config dtype (reference baseline)",
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
