# PowerShell脚本：运行TDD测试并自动添加时间戳
param(
    [string]$Design = "counter",
    [int]$Iterations = 6
)

# 设置控制台编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# 生成时间戳
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# 生成输出文件名
$outputFile = "${Design}_test_utf8_fixed_${timestamp}.txt"

Write-Host "开始执行测试..." -ForegroundColor Green
Write-Host "设计类型: $Design" -ForegroundColor Cyan
Write-Host "迭代次数: $Iterations" -ForegroundColor Cyan
Write-Host "输出文件: $outputFile" -ForegroundColor Cyan
Write-Host "时间戳: $timestamp" -ForegroundColor Yellow
Write-Host ""

# 执行命令并保存到带时间戳的文件
try {
    python test_llm_coordinator_enhanced.py --design $Design --iterations $Iterations 2>&1 | Tee-Object -FilePath $outputFile
    
    Write-Host ""
    Write-Host "执行完成，日志已保存到: $outputFile" -ForegroundColor Green
    Write-Host "时间戳: $timestamp" -ForegroundColor Yellow
    
    # 显示文件大小
    if (Test-Path $outputFile) {
        $fileSize = (Get-Item $outputFile).Length
        $fileSizeKB = [math]::Round($fileSize / 1KB, 2)
        Write-Host "文件大小: $fileSizeKB KB" -ForegroundColor Gray
    }
} catch {
    Write-Host "执行过程中出现错误: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} 