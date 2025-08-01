#!/bin/bash
echo "🎯 环境验证开始..."
echo "📁 工作目录: $(pwd)"
echo "🛠️ iverilog版本: $(iverilog -V 2>/dev/null || echo '未安装')"
echo "📅 测试时间: $(date)"
echo "✅ 环境验证完成！"
