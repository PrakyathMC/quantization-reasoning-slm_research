@echo off
setlocal

cd /d "%~dp0"
set "PYTHON=venv\Scripts\python.exe"
set "EVAL=qwen_testing\gguf_eval.py"

echo ============================================================
echo Qwen3-0.6B GGUF evaluation: 5 models x 50 GSM8K examples
echo ============================================================

call :evaluate "q8_0" "models\qwen3-0.6b\quantized\q8_0\qwen3-0.6b-q8_0.gguf"
if errorlevel 1 exit /b 1
call :evaluate "q6_k" "models\qwen3-0.6b\quantized\q6_k\qwen3-0.6b-q6_k.gguf"
if errorlevel 1 exit /b 1
call :evaluate "q5_k_m" "models\qwen3-0.6b\quantized\q5_k_m\qwen3-0.6b-q5_k_m.gguf"
if errorlevel 1 exit /b 1
call :evaluate "q4_k_m" "models\qwen3-0.6b\quantized\q4_k_m\qwen3-0.6b-q4_k_m.gguf"
if errorlevel 1 exit /b 1
call :evaluate "q3_k_m" "models\qwen3-0.6b\quantized\q3_k_m\qwen3-0.6b-q3_k_m.gguf"
if errorlevel 1 exit /b 1

echo.
echo ============================================================
echo ALL GGUF EVALUATIONS COMPLETED SUCCESSFULLY
echo ============================================================
exit /b 0

:evaluate
set "NAME=%~1"
set "MODEL=%~2"
set "OUTPUT=qwen_testing\corrected_%NAME%_results.json"
echo.
echo ------------------------------------------------------------
echo Starting %NAME%
echo ------------------------------------------------------------
call "%PYTHON%" "%EVAL%" "%MODEL%" "%OUTPUT%"
if errorlevel 1 (
    echo ERROR: %NAME% evaluation failed.
    exit /b 1
)
echo Finished %NAME%
exit /b 0
