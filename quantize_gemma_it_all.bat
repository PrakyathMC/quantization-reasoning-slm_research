@echo off
setlocal

cd /d "%~dp0"

set "QUANTIZE=tools\llama.cpp\bin\llama-quantize.exe"
set "SOURCE=models\gemma-3-1b-it\gguf_reference\gemma-3-1b-it-bf16.gguf"
set "THREADS=4"

if not exist "%QUANTIZE%" exit /b 1
if not exist "%SOURCE%" exit /b 1

echo ============================================================
echo Gemma 3 1B IT GGUF quantization
echo Source: %SOURCE%
echo ============================================================

call :quantize "Q8_0" "models\gemma-3-1b-it\quantized\q8_0\gemma-3-1b-it-q8_0.gguf"
if errorlevel 1 exit /b 1
call :quantize "Q6_K" "models\gemma-3-1b-it\quantized\q6_k\gemma-3-1b-it-q6_k.gguf"
if errorlevel 1 exit /b 1
call :quantize "Q5_K_M" "models\gemma-3-1b-it\quantized\q5_k_m\gemma-3-1b-it-q5_k_m.gguf"
if errorlevel 1 exit /b 1
call :quantize "Q4_K_M" "models\gemma-3-1b-it\quantized\q4_k_m\gemma-3-1b-it-q4_k_m.gguf"
if errorlevel 1 exit /b 1
call :quantize "Q3_K_M" "models\gemma-3-1b-it\quantized\q3_k_m\gemma-3-1b-it-q3_k_m.gguf"
if errorlevel 1 exit /b 1

echo ============================================================
echo ALL GEMMA IT QUANTIZATIONS COMPLETED SUCCESSFULLY
echo ============================================================
exit /b 0

:quantize
set "TYPE=%~1"
set "OUTPUT=%~2"
for %%D in ("%OUTPUT%") do if not exist "%%~dpD" mkdir "%%~dpD"
echo.
echo Starting %TYPE%
"%QUANTIZE%" "%SOURCE%" "%OUTPUT%" "%TYPE%" %THREADS%
if errorlevel 1 exit /b 1
echo Finished %TYPE%
exit /b 0
