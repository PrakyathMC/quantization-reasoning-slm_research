import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".matplotlib"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis"
FIGURES = OUT / "figures"

PRECISION_ORDER = ["BF16", "Q8_0", "Q6_K", "Q5_K_M", "Q4_K_M", "Q3_K_M"]
BIT_WIDTH = {"BF16": 16, "Q8_0": 8, "Q6_K": 6, "Q5_K_M": 5, "Q4_K_M": 4, "Q3_K_M": 3}

FILES = {
    "Qwen3-0.6B": {
        "BF16": "qwen_testing/reference_bf16_results.json",
        "Q8_0": "qwen_testing/corrected_q8_0_results.json",
        "Q6_K": "qwen_testing/corrected_q6_k_results.json",
        "Q5_K_M": "qwen_testing/corrected_q5_k_m_results.json",
        "Q4_K_M": "qwen_testing/corrected_q4_k_m_results.json",
        "Q3_K_M": "qwen_testing/corrected_q3_k_m_results.json",
    },
    "Gemma 3 1B IT": {
        "BF16": "gemma_testing/gemma_it_reference_results.json",
        "Q8_0": "gemma_testing/gemma_it_q8_0_results.json",
        "Q6_K": "gemma_testing/gemma_it_q6_k_results.json",
        "Q5_K_M": "gemma_testing/gemma_it_q5_k_m_results.json",
        "Q4_K_M": "gemma_testing/gemma_it_q4_k_m_results.json",
        "Q3_K_M": "gemma_testing/gemma_it_q3_k_m_results.json",
    },
    "Llama 3.2 1B Instruct": {
        "BF16": "llama_testing/llama_it_reference_results.json",
        "Q8_0": "llama_testing/llama_it_q8_0_results.json",
        "Q6_K": "llama_testing/llama_it_q6_k_results.json",
        "Q5_K_M": "llama_testing/llama_it_q5_k_m_results.json",
        "Q4_K_M": "llama_testing/llama_it_q4_k_m_results.json",
        "Q3_K_M": "llama_testing/llama_it_q3_k_m_results.json",
    },
}


def load_rows():
    rows = []
    for model, precisions in FILES.items():
        for precision in PRECISION_ORDER:
            path = ROOT / precisions[precision]
            if not path.exists():
                raise FileNotFoundError(path)
            data = json.loads(path.read_text(encoding="utf-8"))
            if data["num_examples"] != 50:
                raise ValueError(f"Expected 50 examples in {path}, found {data['num_examples']}")
            failures = sum(item.get("return_code", 0) != 0 for item in data["results"])
            rows.append({
                "model": model,
                "precision": precision,
                "bit_width": BIT_WIDTH[precision],
                "accuracy": data["accuracy"] * 100,
                "correct": data["correct"],
                "num_examples": data["num_examples"],
                "avg_latency_sec": data["avg_latency_sec"],
                "peak_process_ram_gb": data["peak_process_ram_gb"],
                "avg_prompt_tokens_per_sec": data.get("avg_prompt_tokens_per_sec"),
                "avg_generation_tokens_per_sec": data.get("avg_generation_tokens_per_sec"),
                "model_size_mb": data["model_size_bytes"] / (1024 ** 2),
                "return_code_failures": failures,
                "source_file": str(path.relative_to(ROOT)),
            })

    frame = pd.DataFrame(rows)
    references = frame[frame["precision"] == "BF16"].set_index("model")
    frame["accuracy_delta_pp"] = frame.apply(
        lambda r: r["accuracy"] - references.loc[r["model"], "accuracy"], axis=1
    )
    frame["accuracy_retention_pct"] = frame.apply(
        lambda r: (r["accuracy"] / references.loc[r["model"], "accuracy"]) * 100
        if references.loc[r["model"], "accuracy"] else np.nan,
        axis=1,
    )
    frame["latency_speedup"] = frame.apply(
        lambda r: references.loc[r["model"], "avg_latency_sec"] / r["avg_latency_sec"], axis=1
    )
    frame["ram_reduction_pct"] = frame.apply(
        lambda r: (1 - r["peak_process_ram_gb"] / references.loc[r["model"], "peak_process_ram_gb"]) * 100,
        axis=1,
    )
    frame["size_reduction_pct"] = frame.apply(
        lambda r: (1 - r["model_size_mb"] / references.loc[r["model"], "model_size_mb"]) * 100,
        axis=1,
    )
    return frame


def save_outputs(frame):
    OUT.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    frame.to_csv(OUT / "comparison_summary.csv", index=False, float_format="%.4f")
    (OUT / "comparison_summary.json").write_text(
        frame.to_json(orient="records", indent=2), encoding="utf-8"
    )


def plot_metric(frame, column, ylabel, filename, title):
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    for model, group in frame.groupby("model", sort=False):
        group = group.set_index("precision").loc[PRECISION_ORDER]
        ax.plot(PRECISION_ORDER, group[column], marker="o", linewidth=2, label=model)
    ax.set_title(title)
    ax.set_xlabel("Weight format")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES / f"{filename}.png", dpi=300)
    fig.savefig(FIGURES / f"{filename}.svg")
    plt.close(fig)


def plot_accuracy_heatmap(frame):
    table = frame.pivot(index="model", columns="precision", values="accuracy").loc[:, PRECISION_ORDER]
    fig, ax = plt.subplots(figsize=(9, 2.8))
    image = ax.imshow(table.values, cmap="YlGnBu", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(PRECISION_ORDER)), PRECISION_ORDER)
    ax.set_yticks(range(len(table.index)), table.index)
    for i in range(table.shape[0]):
        for j in range(table.shape[1]):
            ax.text(j, i, f"{table.iloc[i, j]:.0f}%", ha="center", va="center", fontsize=9)
    ax.set_title("Accuracy across models and weight formats")
    fig.colorbar(image, ax=ax, label="Accuracy (%)")
    fig.tight_layout()
    fig.savefig(FIGURES / "accuracy_heatmap.png", dpi=300)
    fig.savefig(FIGURES / "accuracy_heatmap.svg")
    plt.close(fig)


def plot_efficiency_frontier(frame):
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    markers = {"Qwen3-0.6B": "o", "Gemma 3 1B IT": "s", "Llama 3.2 1B Instruct": "^"}
    for model, group in frame.groupby("model", sort=False):
        ax.scatter(group["model_size_mb"], group["accuracy"], s=65, marker=markers[model], label=model)
        for _, row in group.iterrows():
            ax.annotate(row["precision"], (row["model_size_mb"], row["accuracy"]), xytext=(4, 4), textcoords="offset points", fontsize=7)
    ax.set_title("Accuracy versus stored model size")
    ax.set_xlabel("Model size (MB)")
    ax.set_ylabel("Accuracy (%)")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES / "accuracy_vs_model_size.png", dpi=300)
    fig.savefig(FIGURES / "accuracy_vs_model_size.svg")
    plt.close(fig)


def main():
    frame = load_rows()
    save_outputs(frame)
    plot_metric(frame, "accuracy", "Accuracy (%)", "accuracy_by_precision", "Reasoning accuracy by weight format")
    plot_metric(frame, "avg_latency_sec", "Average latency (seconds)", "latency_by_precision", "Inference latency by weight format")
    plot_metric(frame, "avg_generation_tokens_per_sec", "Generation speed (tokens/s)", "throughput_by_precision", "Generation throughput by weight format")
    plot_metric(frame, "peak_process_ram_gb", "Peak process RAM (GB)", "ram_by_precision", "Peak process RAM by weight format")
    plot_metric(frame, "model_size_mb", "Stored model size (MB)", "model_size_by_precision", "Stored model size by weight format")
    plot_accuracy_heatmap(frame)
    plot_efficiency_frontier(frame)
    print(f"Consolidated rows: {len(frame)}")
    print(f"CSV: {OUT / 'comparison_summary.csv'}")
    print(f"Figures: {FIGURES}")


if __name__ == "__main__":
    main()
