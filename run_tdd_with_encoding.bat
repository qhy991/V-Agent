@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
python unified_tdd_test.py --design alu > alu_test_utf8_fixed.txt 2>&1 