@echo off
cd /d "%~dp0"
call "venv\Scripts\python.exe" "qwen_testing\gguf_eval.py" "models\gemma-3-1b-it\gguf_reference\gemma-3-1b-it-bf16.gguf" "gemma_testing\gemma_it_reference_results.json"
