@echo off
setlocal

cd /d "%~dp0"
set "PYTHON=venv\Scripts\python.exe"
set "EVAL=qwen_testing\gguf_eval.py"
set "LIMIT=3"

echo ============================================================
echo VALIDATION ONLY: 3 examples per quantized model
echo ============================================================

call :validate "q8_0" "models\qwen3-0.6b\quantized\q8_0\qwen3-0.6b-q8_0.gguf"
if errorlevel 1 exit /b 1
call :validate "q6_k" "models\qwen3-0.6b\quantized\q6_k\qwen3-0.6b-q6_k.gguf"
if errorlevel 1 exit /b 1
call :validate "q5_k_m" "models\qwen3-0.6b\quantized\q5_k_m\qwen3-0.6b-q5_k_m.gguf"
if errorlevel 1 exit /b 1
call :validate "q4_k_m" "models\qwen3-0.6b\quantized\q4_k_m\qwen3-0.6b-q4_k_m.gguf"
if errorlevel 1 exit /b 1
call :validate "q3_k_m" "models\qwen3-0.6b\quantized\q3_k_m\qwen3-0.6b-q3_k_m.gguf"
if errorlevel 1 exit /b 1

echo.
echo VALIDATION COMPLETED. Review the JSON files before the full rerun.
exit /b 0

:validate
set "NAME=%~1"
set "MODEL=%~2"
set "OUTPUT=qwen_testing\validation_%NAME%_results.json"
echo.
echo Testing %NAME%...
call "%PYTHON%" "%EVAL%" "%MODEL%" "%OUTPUT%" --limit %LIMIT%
if errorlevel 1 (
    echo ERROR: %NAME% validation failed.
    exit /b 1
)
exit /b 0
