@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
python test_llm_coordinator_enhanced.py --design counter --iterations 3 > counter_test_utf8_fixed-5.txt 2>&1 