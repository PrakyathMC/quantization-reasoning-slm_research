@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=venv\Scripts\python.exe"
set "EVAL=qwen_testing\gguf_eval.py"

call "%PYTHON%" "%EVAL%" "models\llama-3.2-1b-it\quantized\q8_0\llama-3.2-1b-it-q8_0.gguf" "llama_testing\llama_it_q8_0_results.json"
if errorlevel 1 exit /b 1
call "%PYTHON%" "%EVAL%" "models\llama-3.2-1b-it\quantized\q6_k\llama-3.2-1b-it-q6_k.gguf" "llama_testing\llama_it_q6_k_results.json"
if errorlevel 1 exit /b 1
call "%PYTHON%" "%EVAL%" "models\llama-3.2-1b-it\quantized\q5_k_m\llama-3.2-1b-it-q5_k_m.gguf" "llama_testing\llama_it_q5_k_m_results.json"
if errorlevel 1 exit /b 1
call "%PYTHON%" "%EVAL%" "models\llama-3.2-1b-it\quantized\q4_k_m\llama-3.2-1b-it-q4_k_m.gguf" "llama_testing\llama_it_q4_k_m_results.json"
if errorlevel 1 exit /b 1
call "%PYTHON%" "%EVAL%" "models\llama-3.2-1b-it\quantized\q3_k_m\llama-3.2-1b-it-q3_k_m.gguf" "llama_testing\llama_it_q3_k_m_results.json"
if errorlevel 1 exit /b 1

echo ALL LLAMA IT EVALUATIONS COMPLETED
