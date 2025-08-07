@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

REM 生成时间戳
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"

REM 执行命令并保存到带时间戳的文件
python test_llm_coordinator_enhanced.py --design counter --iterations 4 > counter_test_utf8_fixed_%timestamp%.txt 2>&1

echo 执行完成，日志已保存到: counter_test_utf8_fixed_%timestamp%.txt 