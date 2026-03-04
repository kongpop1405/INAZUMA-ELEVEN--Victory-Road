@echo off
chcp 65001 > nul

:loop
python main.py
echo บอทหลุด! กำลังเริ่มใหม่ใน 5 วินาที...
timeout /t 5
goto loop