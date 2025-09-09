@echo off
set CONS=%1
set SCN=%2
set SEED=%3

if "%CONS%"=="" set CONS=pow
if "%SCN%"=="" set SCN=delays
if "%SEED%"=="" set SEED=42

for %%i in (0 1 2 3 4) do (
    start "node%%i" cmd /k "cd /d %~dp0\.. && .venv\Scripts\python main.py --node-id %%i --consensus %CONS% --scenario %SCN% --seed %SEED% --target-blocks 10"
)

