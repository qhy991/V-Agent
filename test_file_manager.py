#!/usr/bin/env python3

from core.file_manager import get_file_manager
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

try:
    fm = get_file_manager()
    print('✅ 文件管理器可用')
    print('📊 工作空间信息:')
    info = fm.get_workspace_info()
    for key, value in info.items():
        if key != 'recent_files':
            print(f'  {key}: {value}')
    
    verilog_files = fm.get_files_by_type('verilog')
    print(f'🔍 找到 {len(verilog_files)} 个Verilog文件')
    
    if verilog_files:
        print('📁 最新的Verilog文件:')
        for i, file_ref in enumerate(verilog_files[-3:], 1):
            print(f'  {i}. {Path(file_ref.file_path).name} (ID: {file_ref.file_id})')
    
except Exception as e:
    print(f'❌ 文件管理器测试失败: {e}')
    import traceback
    traceback.print_exc()