@echo off
cd /d "%~dp0"
call "venv\Scripts\python.exe" "gemma_testing\gemma_baseline_eval.py"
