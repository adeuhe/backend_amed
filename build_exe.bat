@echo off
title Build Executable — ECL Audit & Benchmarking Workbench
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0build_exe.ps1"
pause
