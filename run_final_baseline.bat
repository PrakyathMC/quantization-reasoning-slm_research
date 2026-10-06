@echo off
cd /d "%~dp0"
call "venv\Scripts\python.exe" "qwen_testing\baseline_eval_final.py"
