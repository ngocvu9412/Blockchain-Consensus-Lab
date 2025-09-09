@echo off
set SEED=%1
if "%SEED%"=="" set SEED=42
call scripts\start_network.bat pow delays %SEED%
