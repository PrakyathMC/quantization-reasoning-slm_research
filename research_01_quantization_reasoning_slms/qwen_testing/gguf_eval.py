import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "data" / "gsm8k_pilot_50.json"
LLAMA_CLI = ROOT_DIR / "tools" / "llama.cpp" / "bin" / "llama-cli.exe"
MAX_NEW_TOKENS = 256
TEMPERATURE = 0


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


def clean_model_output(raw_output, question):
    """Remove llama.cpp's banner, echoed prompt, timing line, and exit text."""
    response = raw_output.rsplit(question, 1)[-1]
    response = response.split("[ Prompt:", 1)[0]
    response = response.replace("Exiting...", "")
    if "[Start thinking]" in response:
        response = response.split("[Start thinking]", 1)[1]
    return response.strip()


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def llama_version():
    result = subprocess.run(
        [str(LLAMA_CLI), "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return (result.stdout or result.stderr).strip()


def run_model(model_path, data):
    results = []
    correct = 0
    total_time = 0.0
    peak_process_ram = 0

    for index, example in enumerate(data):
        question = example["question"]
        gold = example["answer"].split("####")[-1].strip()
        prompt = (
            "Solve this GSM8K problem. Give a brief calculation and end with "
            "the final numeric answer in the format \\boxed{number}.\n\n"
            f"{question}"
        )

        command = [
            str(LLAMA_CLI),
            "-m", str(model_path),
            "-p", prompt,
            "-n", str(MAX_NEW_TOKENS),
            "--temp", "0",
            "-st",
            "--no-display-prompt",
            "--simple-io",
            "--chat-template-kwargs",
            '{"enable_thinking":false}',
        ]

        start = time.perf_counter()
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        child = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                peak_process_ram = max(peak_process_ram, child.memory_info().rss)
            except psutil.Error:
                pass
            time.sleep(0.05)

        stdout, stderr = process.communicate(timeout=30)
        elapsed = time.perf_counter() - start
        raw_output = stdout.strip() or stderr.strip()
        generated = clean_model_output(raw_output, question)
        diagnostics = f"{stdout}\n{stderr}"
        prompt_speed = re.search(r"Prompt:\s*([\d.]+)\s*t/s", diagnostics)
        generation_speed = re.search(r"Generation:\s*([\d.]+)\s*t/s", diagnostics)
        prediction = extract_final_answer(generated)
        is_correct = prediction == gold
        correct += int(is_correct)
        total_time += elapsed

        results.append({
            "id": index,
            "question": question,
            "gold": gold,
            "prediction": prediction,
            "correct": is_correct,
            "latency_sec": round(elapsed, 2),
            "generated_text": generated,
            "raw_output_sha256": hashlib.sha256(raw_output.encode("utf-8")).hexdigest(),
            "prompt_tokens_per_sec": float(prompt_speed.group(1)) if prompt_speed else None,
            "generation_tokens_per_sec": float(generation_speed.group(1)) if generation_speed else None,
            "return_code": process.returncode,
        })
        print(f"[{index + 1}/{len(data)}] Correct: {is_correct} | Latency: {elapsed:.2f}s", flush=True)

    generation_speeds = [
        item["generation_tokens_per_sec"]
        for item in results
        if item["generation_tokens_per_sec"] is not None
    ]
    prompt_speeds = [
        item["prompt_tokens_per_sec"]
        for item in results
        if item["prompt_tokens_per_sec"] is not None
    ]

    return {
        "timestamp": str(datetime.now()),
        "model": model_path.name,
        "runtime": "llama.cpp",
        "llama_version": llama_version(),
        "precision": model_path.stem,
        "model_size_bytes": model_path.stat().st_size,
        "model_sha256": sha256_file(model_path),
        "dataset": str(DATA_PATH),
        "dataset_sha256": sha256_file(DATA_PATH),
        "prompt_template": (
            "Solve this GSM8K problem. Give a brief calculation and end with "
            "the final numeric answer in the format \\boxed{number}. "
            "Use non-thinking mode. /no_think"
        ),
        "decoding": {
            "max_new_tokens": MAX_NEW_TOKENS,
            "temperature": TEMPERATURE,
            "single_turn": True,
            "no_display_prompt": True,
            "simple_io": True,
        },
        "environment": {
            "python": sys.version,
            "os": platform.platform(),
            "cpu": platform.processor(),
            "cpu_count": psutil.cpu_count(logical=True),
            "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 2),
        },
        "num_examples": len(data),
        "accuracy": round(correct / len(data), 4),
        "correct": correct,
        "avg_latency_sec": round(total_time / len(data), 2),
        "peak_process_ram_gb": round(peak_process_ram / 1e9, 2),
        "avg_prompt_tokens_per_sec": round(sum(prompt_speeds) / len(prompt_speeds), 2) if prompt_speeds else None,
        "avg_generation_tokens_per_sec": round(sum(generation_speeds) / len(generation_speeds), 2) if generation_speeds else None,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    if not LLAMA_CLI.exists():
        raise FileNotFoundError(f"Missing llama-cli: {LLAMA_CLI}")
    if not args.model.exists():
        raise FileNotFoundError(f"Missing model: {args.model}")

    with DATA_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if args.limit is not None:
        data = data[:args.limit]

    print(f"Loading model: {args.model}", flush=True)
    summary = run_model(args.model, data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    print("\n========== GGUF RESULTS ==========")
    print(f"Accuracy:          {summary['accuracy']:.2%}")
    print(f"Correct:           {summary['correct']}/{summary['num_examples']}")
    print(f"Avg Latency:       {summary['avg_latency_sec']:.2f} sec/example")
    print(f"Peak Process RAM:  {summary['peak_process_ram_gb']:.2f} GB")
    print(f"Avg Generation:    {summary['avg_generation_tokens_per_sec']} tokens/sec")
    print(f"Results saved to:  {args.output}")


if __name__ == "__main__":
    main()
