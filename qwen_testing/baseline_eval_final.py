import hashlib
import json
import os
import platform
import re
import time
from datetime import datetime
from pathlib import Path

import psutil
import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer


ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT_DIR / "qwen_base_model_weights"
DATA_PATH = ROOT_DIR / "data" / "gsm8k_pilot_50.json"
OUTPUT_PATH = Path(__file__).resolve().parent / "baseline_final_results.json"
MAX_NEW_TOKENS = 256
TEMPERATURE = 0


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_final_answer(text):
    boxed = re.findall(r"\\boxed\{\s*([^{}]+?)\s*\}", text)
    if boxed:
        text = boxed[-1]
    answers = re.findall(
        r"(?:final answer|answer)\s*[:=]?\s*\$?\s*([-+]?\d[\d,]*(?:\.\d+)?)",
        text,
        flags=re.IGNORECASE,
    )
    if answers:
        return answers[-1].replace(",", "")
    numbers = re.findall(r"[-+]?\d[\d,]*(?:\.\d+)?", text)
    return numbers[-1].replace(",", "") if numbers else None


def main():
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    print("Loading tokenizer and model...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.float16,
        device_map="cpu",
    )
    model.eval()
    process = psutil.Process(os.getpid())
    peak_process_ram = process.memory_info().rss
    peak_system_ram = psutil.virtual_memory().used
    results = []
    correct = 0
    total_time = 0.0
    total_generated_tokens = 0

    for index, example in enumerate(data):
        question = example["question"]
        gold = example["answer"].split("####")[-1].strip()
        messages = [{
            "role": "user",
            "content": (
                "Solve this GSM8K problem. Give a brief calculation and end with "
                "the final numeric answer in the format \\boxed{number}.\n\n"
                f"{question}"
            ),
        }]
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        inputs = tokenizer(prompt, return_tensors="pt")

        start = time.perf_counter()
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False,
            )
        elapsed = time.perf_counter() - start
        generated_ids = outputs[0][inputs.input_ids.shape[1]:]
        generated = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
        prediction = extract_final_answer(generated)
        is_correct = prediction == gold
        correct += int(is_correct)
        total_time += elapsed
        total_generated_tokens += len(generated_ids)
        peak_process_ram = max(peak_process_ram, process.memory_info().rss)
        peak_system_ram = max(peak_system_ram, psutil.virtual_memory().used)

        results.append({
            "id": index,
            "question": question,
            "gold": gold,
            "prediction": prediction,
            "correct": is_correct,
            "latency_sec": round(elapsed, 2),
            "generated_tokens": len(generated_ids),
            "generation_tokens_per_sec": round(len(generated_ids) / elapsed, 2) if elapsed else None,
            "generated_text": generated,
        })
        print(f"[{index + 1}/{len(data)}] Correct: {is_correct} | Latency: {elapsed:.2f}s", flush=True)

    summary = {
        "timestamp": str(datetime.now()),
        "model": "Qwen3-0.6B",
        "runtime": "Transformers",
        "model_path": str(MODEL_PATH),
        "model_size_bytes": sum(p.stat().st_size for p in MODEL_PATH.rglob("*") if p.is_file()),
        "model_sha256": sha256_file(MODEL_PATH / "model.safetensors"),
        "dataset": str(DATA_PATH),
        "dataset_sha256": sha256_file(DATA_PATH),
        "transformers_version": transformers.__version__,
        "torch_version": torch.__version__,
        "prompt_template": "GSM8K brief calculation ending in \\boxed{number}; enable_thinking=False",
        "decoding": {"max_new_tokens": MAX_NEW_TOKENS, "temperature": TEMPERATURE, "do_sample": False},
        "environment": {
            "python": platform.python_version(),
            "os": platform.platform(),
            "cpu": platform.processor(),
            "cpu_count": psutil.cpu_count(logical=True),
            "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 2),
        },
        "precision": "float16",
        "num_examples": len(data),
        "accuracy": round(correct / len(data), 4),
        "correct": correct,
        "avg_latency_sec": round(total_time / len(data), 2),
        "avg_generation_tokens_per_sec": round(total_generated_tokens / total_time, 2),
        "peak_process_ram_gb": round(peak_process_ram / 1e9, 2),
        "peak_system_ram_gb": round(peak_system_ram / 1e9, 2),
        "results": results,
    }
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    print("\n========== FINAL BASELINE RESULTS ==========")
    print(f"Accuracy:          {summary['accuracy']:.2%}")
    print(f"Correct:           {summary['correct']}/{summary['num_examples']}")
    print(f"Avg Latency:       {summary['avg_latency_sec']:.2f} sec/example")
    print(f"Peak Process RAM:  {summary['peak_process_ram_gb']:.2f} GB")
    print(f"Avg Generation:    {summary['avg_generation_tokens_per_sec']:.2f} tokens/sec")
    print(f"Results saved to:  {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
