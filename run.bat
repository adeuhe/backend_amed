@echo off
title ECL Audit & Benchmarking Workbench
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0run.ps1"
pause
