@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

REM 设置默认参数
set "design_type=counter"
set "iterations=6"

REM 检查命令行参数
if not "%1"=="" set "design_type=%1"
if not "%2"=="" set "iterations=%2"

REM 生成时间戳
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"

REM 生成输出文件名
set "output_file=%design_type%_test_utf8_fixed_%timestamp%.txt"

echo 开始执行测试...
echo 设计类型: %design_type%
echo 迭代次数: %iterations%
echo 输出文件: %output_file%
echo.

REM 执行命令并保存到带时间戳的文件
python test_llm_coordinator_enhanced.py --design %design_type% --iterations %iterations% > %output_file% 2>&1

echo.
echo 执行完成，日志已保存到: %output_file%
echo 时间戳: %timestamp% 