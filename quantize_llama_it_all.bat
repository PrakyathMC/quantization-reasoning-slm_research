@echo off
setlocal
cd /d "%~dp0"

set "QUANTIZE=tools\llama.cpp\bin\llama-quantize.exe"
set "SOURCE=models\llama-3.2-1b-it\gguf_reference\llama-3.2-1b-it-bf16.gguf"
set "THREADS=4"

if not exist "%QUANTIZE%" exit /b 1
if not exist "%SOURCE%" exit /b 1

echo ============================================================
echo Llama 3.2 1B IT GGUF quantization
echo Source: %SOURCE%
echo ============================================================

call :quantize "Q8_0" "models\llama-3.2-1b-it\quantized\q8_0\llama-3.2-1b-it-q8_0.gguf"
if errorlevel 1 exit /b 1
call :quantize "Q6_K" "models\llama-3.2-1b-it\quantized\q6_k\llama-3.2-1b-it-q6_k.gguf"
if errorlevel 1 exit /b 1
call :quantize "Q5_K_M" "models\llama-3.2-1b-it\quantized\q5_k_m\llama-3.2-1b-it-q5_k_m.gguf"
if errorlevel 1 exit /b 1
call :quantize "Q4_K_M" "models\llama-3.2-1b-it\quantized\q4_k_m\llama-3.2-1b-it-q4_k_m.gguf"
if errorlevel 1 exit /b 1
call :quantize "Q3_K_M" "models\llama-3.2-1b-it\quantized\q3_k_m\llama-3.2-1b-it-q3_k_m.gguf"
if errorlevel 1 exit /b 1

echo ALL LLAMA IT QUANTIZATIONS COMPLETED SUCCESSFULLY
exit /b 0

:quantize
set "TYPE=%~1"
set "OUTPUT=%~2"
for %%D in ("%OUTPUT%") do if not exist "%%~dpD" mkdir "%%~dpD"
echo Starting %TYPE%
"%QUANTIZE%" "%SOURCE%" "%OUTPUT%" "%TYPE%" %THREADS%
if errorlevel 1 exit /b 1
echo Finished %TYPE%
exit /b 0
