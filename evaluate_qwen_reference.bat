@echo off
cd /d "%~dp0"
call "venv\Scripts\python.exe" "qwen_testing\gguf_eval.py" ^
  "models\qwen3-0.6b\gguf_reference\qwen3-0.6b-bf16.gguf" ^
  "qwen_testing\reference_bf16_results.json"
