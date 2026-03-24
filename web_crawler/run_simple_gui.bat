@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 爬虫测试 - 极简版GUI

python gui_simple.py
pause
