#!/usr/bin/env python3
"""
脚本工具 - 支持写脚本、保存脚本、执行脚本
Script Tools - Support writing, saving and executing scripts
"""

import os
import stat
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ScriptManager:
    """脚本管理器"""
    
    def __init__(self, work_dir: Path = None):
        self.work_dir = work_dir or Path.cwd()
        self.scripts_dir = self.work_dir / "scripts"
        self.scripts_dir.mkdir(exist_ok=True)
        
        # 支持的脚本类型
        self.script_types = {
            'bash': {'extension': '.sh', 'shebang': '#!/bin/bash'},
            'make': {'extension': '.mk', 'shebang': '# Makefile'},
            'python': {'extension': '.py', 'shebang': '#!/usr/bin/env python3'},
            'tcl': {'extension': '.tcl', 'shebang': '#!/usr/bin/tclsh'}
        }
    
    def write_script(self, script_name: str, script_content: str, 
                    script_type: str = 'bash', make_executable: bool = True) -> Dict[str, Any]:
        """写入脚本文件"""
        try:
            # 验证脚本类型
            if script_type not in self.script_types:
                return {
                    "success": False,
                    "error": f"不支持的脚本类型: {script_type}. 支持的类型: {list(self.script_types.keys())}",
                    "script_path": None
                }
            
            # 构建脚本文件路径
            script_info = self.script_types[script_type]
            if not script_name.endswith(script_info['extension']):
                script_name += script_info['extension']
            
            script_path = self.scripts_dir / script_name
            
            # 添加shebang（如果需要）
            if script_type != 'make' and not script_content.startswith('#!'):
                script_content = script_info['shebang'] + '\n\n' + script_content
            
            # 写入脚本文件
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # 设置可执行权限
            if make_executable and script_type in ['bash', 'python', 'tcl']:
                script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
            
            logger.info(f"✅ 脚本已保存: {script_path}")
            
            return {
                "success": True,
                "script_path": str(script_path),
                "script_name": script_name,
                "script_type": script_type,
                "is_executable": make_executable,
                "message": f"脚本已成功保存到: {script_path}"
            }
            
        except Exception as e:
            logger.error(f"❌ 脚本写入失败: {str(e)}")
            return {
                "success": False,
                "error": f"脚本写入异常: {str(e)}",
                "script_path": None
            }
    
    def execute_script(self, script_path: str, arguments: List[str] = None, 
                      working_directory: str = None, timeout: int = 300) -> Dict[str, Any]:
        """执行脚本"""
        try:
            script_path = Path(script_path)
            
            # 如果是相对路径，在scripts目录中查找
            if not script_path.is_absolute():
                script_path = self.scripts_dir / script_path
            
            if not script_path.exists():
                return {
                    "success": False,
                    "error": f"脚本文件不存在: {script_path}",
                    "return_code": -1,
                    "stdout": "",
                    "stderr": ""
                }
            
            # 确定工作目录
            work_dir = Path(working_directory) if working_directory else self.work_dir
            
            # 构建执行命令 - 使用绝对路径
            abs_script_path = script_path.resolve()
            if script_path.suffix == '.mk':
                # Makefile执行
                cmd = ['make', '-f', str(abs_script_path)]
            elif script_path.suffix == '.py':
                # Python脚本执行
                cmd = ['python3', str(abs_script_path)]
            elif script_path.suffix == '.tcl':
                # TCL脚本执行
                cmd = ['tclsh', str(abs_script_path)]
            else:
                # Bash脚本执行
                cmd = ['bash', str(abs_script_path)]
            
            # 添加参数
            if arguments:
                cmd.extend(arguments)
            
            logger.info(f"🚀 执行脚本: {' '.join(cmd)}")
            logger.info(f"📁 工作目录: {work_dir}")
            
            # 执行脚本
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            
            if success:
                logger.info(f"✅ 脚本执行成功: {script_path}")
            else:
                logger.warning(f"⚠️ 脚本执行失败: {script_path}, 返回码: {result.returncode}")
            
            return {
                "success": success,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "script_path": str(script_path),
                "command": ' '.join(cmd),
                "working_directory": str(work_dir),
                "execution_time": timeout,
                "message": "脚本执行成功" if success else f"脚本执行失败，返回码: {result.returncode}"
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"脚本执行超时 (>{timeout}s)",
                "return_code": -1,
                "stdout": "",
                "stderr": ""
            }
        except Exception as e:
            logger.error(f"❌ 脚本执行异常: {str(e)}")
            return {
                "success": False,
                "error": f"脚本执行异常: {str(e)}",
                "return_code": -1,
                "stdout": "",
                "stderr": ""
            }
    
    def generate_makefile(self, verilog_files: List[str], testbench_files: List[str], 
                         target_name: str = "simulation", top_module: str = None) -> str:
        """生成Makefile内容"""
        
        # 检测顶层模块
        if not top_module:
            # 尝试从testbench文件中推断
            for tb_file in testbench_files:
                if 'tb' in tb_file.lower() or 'testbench' in tb_file.lower():
                    top_module = Path(tb_file).stem
                    break
            if not top_module:
                top_module = "testbench"
        
        makefile_content = f"""# Auto-generated Makefile for Verilog simulation
# Generated by CentralizedAgentFramework ScriptManager

# 变量定义
VERILOG_FILES = {' '.join(verilog_files)}
TESTBENCH_FILES = {' '.join(testbench_files)}
ALL_FILES = $(VERILOG_FILES) $(TESTBENCH_FILES)
TARGET = {target_name}
TOP_MODULE = {top_module}

# 工具配置
IVERILOG = iverilog
VVP = vvp
GTKWAVE = gtkwave

# 默认目标
all: compile simulate

# 编译目标
compile: $(TARGET)

$(TARGET): $(ALL_FILES)
\t@echo "🔨 编译Verilog文件..."
\t$(IVERILOG) -o $(TARGET) $(ALL_FILES)
\t@echo "✅ 编译完成"

# 仿真目标
simulate: $(TARGET)
\t@echo "▶️ 运行仿真..."
\t$(VVP) $(TARGET)
\t@echo "✅ 仿真完成"

# 波形查看
wave: $(TARGET).vcd
\t$(GTKWAVE) $(TARGET).vcd

# 清理目标
clean:
\t@echo "🧹 清理文件..."
\trm -f $(TARGET) *.vcd *.lxt2
\t@echo "✅ 清理完成"

# 显示帮助
help:
\t@echo "可用目标:"
\t@echo "  all      - 编译并运行仿真"
\t@echo "  compile  - 仅编译"
\t@echo "  simulate - 仅运行仿真"
\t@echo "  wave     - 查看波形"
\t@echo "  clean    - 清理生成的文件"
\t@echo "  help     - 显示此帮助信息"

# 检查文件
check:
\t@echo "📋 检查文件存在性:"
\t@for file in $(ALL_FILES); do \\
\t\tif [ -f $$file ]; then \\
\t\t\techo "  ✅ $$file"; \\
\t\telse \\
\t\t\techo "  ❌ $$file (不存在)"; \\
\t\tfi; \\
\tdone

.PHONY: all compile simulate wave clean help check
"""
        return makefile_content
    
    def generate_build_script(self, verilog_files: List[str], testbench_files: List[str],
                            target_name: str = "simulation", 
                            include_wave_generation: bool = True) -> str:
        """生成构建脚本内容"""
        
        script_content = f"""#!/bin/bash
# Auto-generated build script for Verilog simulation
# Generated by CentralizedAgentFramework ScriptManager

# 设置颜色输出
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

# 配置变量
VERILOG_FILES="{' '.join(verilog_files)}"
TESTBENCH_FILES="{' '.join(testbench_files)}"
TARGET="{target_name}"

# 函数定义
log_info() {{
    echo -e "${{BLUE}}[INFO]${{NC}} $1"
}}

log_success() {{
    echo -e "${{GREEN}}[SUCCESS]${{NC}} $1"
}}

log_error() {{
    echo -e "${{RED}}[ERROR]${{NC}} $1"
}}

log_warning() {{
    echo -e "${{YELLOW}}[WARNING]${{NC}} $1"
}}

# 检查文件存在性
check_files() {{
    log_info "检查源文件..."
    local missing_files=0
    
    for file in $VERILOG_FILES $TESTBENCH_FILES; do
        if [ -f "$file" ]; then
            log_success "✅ $file"
        else
            log_error "❌ $file (文件不存在)"
            missing_files=$((missing_files + 1))
        fi
    done
    
    if [ $missing_files -gt 0 ]; then
        log_error "发现 $missing_files 个缺失文件，无法继续"
        exit 1
    fi
}}

# 编译功能
compile() {{
    log_info "🔨 开始编译..."
    
    # 使用iverilog编译
    if iverilog -o "$TARGET" $VERILOG_FILES $TESTBENCH_FILES; then
        log_success "✅ 编译成功: $TARGET"
        return 0
    else
        log_error "❌ 编译失败"
        return 1
    fi
}}

# 仿真功能
simulate() {{
    log_info "▶️ 开始仿真..."
    
    if [ ! -f "$TARGET" ]; then
        log_error "可执行文件不存在: $TARGET"
        return 1
    fi
    
    # 运行仿真
    if vvp "$TARGET"; then
        log_success "✅ 仿真完成"
        
        # 检查是否生成了VCD文件
        if [ -f "${{TARGET}}.vcd" ]; then
            log_success "📊 波形文件已生成: ${{TARGET}}.vcd"
        fi
        
        return 0
    else
        log_error "❌ 仿真失败"
        return 1
    fi
}}

# 清理功能
clean() {{
    log_info "🧹 清理文件..."
    rm -f "$TARGET" *.vcd *.lxt2
    log_success "✅ 清理完成"
}}

# 主逻辑
case "$1" in
    "compile")
        check_files
        compile
        ;;
    "simulate")
        if [ ! -f "$TARGET" ]; then
            log_warning "可执行文件不存在，先进行编译..."
            check_files
            compile || exit 1
        fi
        simulate
        ;;
    "clean")
        clean
        ;;
    "all"|"")
        check_files
        compile || exit 1
        simulate
        ;;
    "help")
        echo "用法: $0 [compile|simulate|clean|all|help]"
        echo "  compile  - 仅编译"
        echo "  simulate - 仅仿真（如需要会先编译）"
        echo "  clean    - 清理生成的文件"
        echo "  all      - 编译并仿真（默认）"
        echo "  help     - 显示帮助信息"
        ;;
    *)
        log_error "未知参数: $1"
        echo "使用 '$0 help' 查看帮助"
        exit 1
        ;;
esac
"""
        return script_content
    
    def list_scripts(self) -> Dict[str, Any]:
        """列出所有脚本"""
        try:
            scripts = []
            
            for script_file in self.scripts_dir.glob("*"):
                if script_file.is_file():
                    stat_info = script_file.stat()
                    scripts.append({
                        "name": script_file.name,
                        "path": str(script_file),
                        "size": stat_info.st_size,
                        "is_executable": bool(stat_info.st_mode & stat.S_IEXEC),
                        "modified_time": stat_info.st_mtime,
                        "extension": script_file.suffix
                    })
            
            return {
                "success": True,
                "scripts": scripts,
                "total_count": len(scripts),
                "scripts_directory": str(self.scripts_dir)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"列出脚本失败: {str(e)}",
                "scripts": []
            }