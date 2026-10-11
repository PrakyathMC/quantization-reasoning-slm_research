# Post-Training Weight Quantization in Small Language Models: Reasoning–Efficiency Trade-offs Across GGUF Precision Levels

Reproducible research code and analysis for evaluating how post-training weight quantization affects the reasoning accuracy and inference efficiency of small instruction-tuned language models.

## Research question

> Does weight quantization cause a gradual or abrupt degradation in the reasoning capabilities of small language models?

The study evaluates whether lower numerical precision produces a consistent accuracy loss, a model-dependent effect, or a sharper degradation at particular low-bit formats.

## Models and quantization formats

Three small instruction-tuned models were converted to BF16 GGUF reference files and quantized locally using `llama.cpp`:

- Qwen3-0.6B
- Gemma 3 1B IT
- Llama 3.2 1B Instruct

Tested formats:

`BF16`, `Q8_0`, `Q6_K`, `Q5_K_M`, `Q4_K_M`, and `Q3_K_M`

The study uses the same 50-question GSM8K pilot subset, prompt structure, deterministic decoding configuration, and answer-normalization procedure for every model and precision level.

## Main results

Accuracy is reported on the 50-question evaluation subset. Efficiency measurements were collected on the same CPU-only Windows environment.

| Model | BF16 | Q8_0 | Q6_K | Q5_K_M | Q4_K_M | Q3_K_M |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3-0.6B | 54% | 46% | 42% | 48% | 54% | 24% |
| Gemma 3 1B IT | 42% | 32% | 36% | 36% | 44% | 40% |
| Llama 3.2 1B Instruct | 34% | 36% | 38% | 34% | 32% | 20% |

The results do not show one universal degradation pattern. Quantization substantially reduced stored model size and generally improved CPU inference speed, while accuracy changes varied by model and precision. Q3_K_M produced the largest accuracy reductions for Qwen and Llama, whereas some mid-range formats matched or exceeded their BF16 references.

## Evaluation metrics

- Exact-answer accuracy
- Average per-question latency
- Peak process RAM
- Prompt-processing speed
- Generation speed in tokens per second
- Stored GGUF model size
- Per-example predictions and return codes

## Repository structure

```text
.
├── analysis/
│   ├── build_comparison.py
│   ├── comparison_summary.csv
│   ├── comparison_summary.json
│   └── figures/
├── qwen_testing/
│   ├── gguf_eval.py
│   └── corrected_*_results.json
├── gemma_testing/
│   ├── gemma_baseline_eval.py
│   └── gemma_it_*_results.json
├── llama_testing/
│   └── llama_it_*_results.json
├── docs/
│   └── Research_papaer.pdf
├── scripts/
│   ├── quantize_*_all.bat
│   ├── evaluate_*.bat
│   └── run_*_awake.ps1
├── requirements.txt
└── README.md
```

Large model weights, GGUF files, the virtual environment, raw local data, logs, and the `llama.cpp` build are intentionally excluded from Git. The tracked result files contain the model hashes, dataset hash, runtime metadata, decoding configuration, measurements, and per-example outputs needed to audit the reported results.

## Reproduction overview

The commands below are Windows `cmd.exe` commands and assume the repository is located at `D:\slm_research`.

### 1. Create the environment

```bat
cd /d D:\slm_research
py -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```

Install or place the required `llama.cpp` Windows binaries under `tools\llama.cpp\bin\` and obtain the model weights separately. Model weights are not committed to this repository.

### 2. Run the evaluations

The repository contains model-specific batch and PowerShell wrappers. Examples:

```bat
scripts\evaluate_qwen_reference.bat
scripts\evaluate_qwen_quantized.bat
scripts\evaluate_gemma_it_quantized.bat
scripts\evaluate_llama_it_quantized.bat
```

For long-running jobs, the `*_awake.ps1` wrappers prevent Windows from entering sleep during execution. Run them from `cmd.exe`, for example:

```bat
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\run_llama_it_quantized_awake.ps1"
```

### 3. Rebuild the comparison outputs

```bat
venv\Scripts\python.exe analysis\build_comparison.py
```

This regenerates the consolidated CSV/JSON summary and analysis figures from the final result files.

## Experimental configuration

- Runtime: `llama.cpp`
- Platform: Windows CPU-only execution
- Decoding temperature: `0`
- Maximum new tokens: `256`
- Evaluation mode: single-turn generation
- Dataset: fixed 50-question GSM8K pilot subset
- Scoring: extracted numeric answer compared with the reference answer
- Model conversion: Hugging Face weights to BF16 GGUF
- Quantization: BF16 GGUF to `Q8_0`, `Q6_K`, `Q5_K_M`, `Q4_K_M`, and `Q3_K_M`

## Limitations

This is a controlled pilot study rather than a definitive benchmark. It uses 50 GSM8K questions, one deterministic run per configuration, one CPU-only Windows laptop, and one GGUF quantization implementation. The results should therefore be interpreted as preliminary evidence and not as a universal ranking of model quality.

## Paper and analysis outputs

- Paper: [`docs/Research_papaer.pdf`](docs/Research_papaer.pdf)
- Consolidated results: [`analysis/comparison_summary.csv`](analysis/comparison_summary.csv)
- Machine-readable results: [`analysis/comparison_summary.json`](analysis/comparison_summary.json)
- Figures: [`analysis/figures/`](analysis/figures/)

## References

The paper contains the academic references for GSM8K, GPTQ, AWQ, SmoothQuant, the evaluated model families, and `llama.cpp`.

## Status

This repository contains the completed pilot experiments, consolidated analysis, figures, and research paper draft. It is intended as a reproducible AI research portfolio project and can be extended with larger datasets, repeated trials, additional quantization methods, and multiple hardware platforms.
