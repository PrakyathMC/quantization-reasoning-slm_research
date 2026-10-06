@echo off
setlocal

cd /d "%~dp0"

set "QUANTIZE=tools\llama.cpp\bin\llama-quantize.exe"
set "SOURCE=models\qwen3-0.6b\gguf_reference\qwen3-0.6b-bf16.gguf"
set "THREADS=4"

if not exist "%QUANTIZE%" (
    echo ERROR: llama-quantize.exe was not found.
    exit /b 1
)
if not exist "%SOURCE%" (
    echo ERROR: reference GGUF was not found.
    exit /b 1
)

echo ============================================================
echo Qwen3-0.6B GGUF quantization
echo Source: %SOURCE%
echo Threads: %THREADS%
echo ============================================================

call :quantize "Q8_0" "models\qwen3-0.6b\quantized\q8_0\qwen3-0.6b-q8_0.gguf"
if errorlevel 1 exit /b 1

call :quantize "Q6_K" "models\qwen3-0.6b\quantized\q6_k\qwen3-0.6b-q6_k.gguf"
if errorlevel 1 exit /b 1

call :quantize "Q5_K_M" "models\qwen3-0.6b\quantized\q5_k_m\qwen3-0.6b-q5_k_m.gguf"
if errorlevel 1 exit /b 1

call :quantize "Q4_K_M" "models\qwen3-0.6b\quantized\q4_k_m\qwen3-0.6b-q4_k_m.gguf"
if errorlevel 1 exit /b 1

call :quantize "Q3_K_M" "models\qwen3-0.6b\quantized\q3_k_m\qwen3-0.6b-q3_k_m.gguf"
if errorlevel 1 exit /b 1

echo.
echo ============================================================
echo ALL QUANTIZATIONS COMPLETED SUCCESSFULLY
echo ============================================================
exit /b 0

:quantize
set "TYPE=%~1"
set "OUTPUT=%~2"
echo.
echo ------------------------------------------------------------
echo Starting %TYPE%
echo Output: %OUTPUT%
echo ------------------------------------------------------------
"%QUANTIZE%" "%SOURCE%" "%OUTPUT%" "%TYPE%" %THREADS%
if errorlevel 1 (
    echo ERROR: %TYPE% quantization failed.
    exit /b 1
)
echo Finished %TYPE%
exit /b 0
