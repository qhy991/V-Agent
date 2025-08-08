#!/usr/bin/env python3
"""
增强的构建脚本生成器
解决Makefile和构建脚本生成后执行失败的问题
"""

import os
import logging
import stat
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field

from core.path_manager import get_path_manager, PathSearchResult

logger = logging.getLogger(__name__)

@dataclass
class BuildTarget:
    """构建目标定义"""
    name: str
    target_type: str  # "simulation", "synthesis", "lint"
    source_files: List[Path] = field(default_factory=list)
    testbench_files: List[Path] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    compiler_options: List[str] = field(default_factory=list)
    output_files: List[str] = field(default_factory=list)

@dataclass
class BuildConfiguration:
    """构建配置"""
    simulator: str = "iverilog"
    working_directory: Path = None
    output_directory: Path = None
    targets: List[BuildTarget] = field(default_factory=list)
    global_options: Dict[str, Any] = field(default_factory=dict)

class EnhancedBuildScriptGenerator:
    """增强的构建脚本生成器"""
    
    def __init__(self, working_directory: Union[str, Path] = None):
        self.working_dir = Path(working_directory) if working_directory else Path.cwd()
        self.path_manager = get_path_manager(self.working_dir)
        self.logger = logger
        
        # 支持的仿真器配置
        self.simulator_configs = {
            "iverilog": {
                "compile_cmd": "iverilog",
                "compile_flags": ["-g2012", "-Wall"],
                "output_flag": "-o",
                "run_cmd": "vvp",
                "extensions": [".v", ".sv"]
            },
            "verilator": {
                "compile_cmd": "verilator",
                "compile_flags": ["--cc", "--exe", "--build"],
                "output_flag": "-Mdir",
                "run_cmd": None,
                "extensions": [".v", ".sv"]
            },
            "modelsim": {
                "compile_cmd": "vlog",
                "compile_flags": ["-work", "work"],
                "output_flag": None,
                "run_cmd": "vsim",
                "extensions": [".v", ".sv"]
            }
        }
    
    def generate_makefile(self, config: BuildConfiguration) -> str:
        """生成增强的Makefile"""
        makefile_content = self._generate_makefile_header(config)
        makefile_content += self._generate_makefile_variables(config)
        makefile_content += self._generate_makefile_targets(config)
        makefile_content += self._generate_makefile_utilities(config)
        
        return makefile_content
    
    def generate_bash_script(self, config: BuildConfiguration) -> str:
        """生成增强的Bash脚本"""
        script_content = self._generate_bash_header(config)
        script_content += self._generate_bash_functions(config)
        script_content += self._generate_bash_main(config)
        
        return script_content
    
    def create_build_files(self, config: BuildConfiguration, 
                          generate_makefile: bool = True,
                          generate_bash: bool = True) -> Dict[str, Path]:
        """创建构建文件"""
        created_files = {}
        
        # 确保输出目录存在
        output_dir = config.output_directory or self.working_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if generate_makefile:
            makefile_path = output_dir / "Makefile"
            makefile_content = self.generate_makefile(config)
            
            with open(makefile_path, 'w', encoding='utf-8') as f:
                f.write(makefile_content)
            
            created_files["makefile"] = makefile_path
            self.logger.info(f"✅ 创建Makefile: {makefile_path}")
        
        if generate_bash:
            script_path = output_dir / "build_and_run.sh"
            script_content = self.generate_bash_script(config)
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # 设置执行权限
            script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
            
            created_files["bash_script"] = script_path
            self.logger.info(f"✅ 创建Bash脚本: {script_path}")
        
        return created_files
    
    def validate_build_files(self, config: BuildConfiguration) -> Dict[str, Any]:
        """验证构建文件的有效性"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "file_checks": {}
        }
        
        # 检查源文件存在性
        all_files = []
        for target in config.targets:
            all_files.extend(target.source_files)
            all_files.extend(target.testbench_files)
        
        file_validation = self.path_manager.validate_file_existence(all_files)
        
        if not file_validation["all_exist"]:
            validation_result["valid"] = False
            validation_result["errors"].extend([
                f"缺失文件: {f}" for f in file_validation["missing_files"]
            ])
            validation_result["errors"].extend([
                f"无效文件: {f}" for f in file_validation["invalid_files"]
            ])
        
        validation_result["file_checks"] = file_validation
        
        # 检查仿真器可用性
        simulator = config.simulator
        if simulator not in self.simulator_configs:
            validation_result["warnings"].append(f"未知的仿真器: {simulator}")
        
        return validation_result
    
    def _generate_makefile_header(self, config: BuildConfiguration) -> str:
        """生成Makefile头部"""
        simulator_info = self.simulator_configs.get(config.simulator, {})
        
        return f"""# Enhanced Makefile for Verilog Simulation
# Generated by EnhancedBuildScriptGenerator
# Simulator: {config.simulator}
# Working Directory: {config.working_directory or self.working_dir}

# Disable built-in rules and variables for better performance
MAKEFLAGS += --no-builtin-rules
.SUFFIXES:

"""
    
    def _generate_makefile_variables(self, config: BuildConfiguration) -> str:
        """生成Makefile变量"""
        simulator_info = self.simulator_configs.get(config.simulator, self.simulator_configs["iverilog"])
        
        # 收集所有源文件和测试台文件
        all_source_files = []
        all_testbench_files = []
        
        for target in config.targets:
            all_source_files.extend([self.path_manager.get_relative_path(f) for f in target.source_files])
            all_testbench_files.extend([self.path_manager.get_relative_path(f) for f in target.testbench_files])
        
        # 去重
        all_source_files = list(set(all_source_files))
        all_testbench_files = list(set(all_testbench_files))
        
        content = f"""# Compiler and flags
SIMULATOR = {config.simulator}
COMPILE_CMD = {simulator_info['compile_cmd']}
COMPILE_FLAGS = {' '.join(simulator_info.get('compile_flags', []))}
OUTPUT_FLAG = {simulator_info.get('output_flag', '-o')}

# Source files
VERILOG_SOURCES = {' '.join(all_source_files) if all_source_files else ''}
TESTBENCH_SOURCES = {' '.join(all_testbench_files) if all_testbench_files else ''}
ALL_SOURCES = $(VERILOG_SOURCES) $(TESTBENCH_SOURCES)

# Output directory
OUTPUT_DIR = {config.output_directory or '.'}
BUILD_DIR = $(OUTPUT_DIR)/build

# Check if all source files exist
define check_files
\t@echo "Checking source files..."
\t@missing_files=""; \\
\tfor file in $(ALL_SOURCES); do \\
\t\tif [ ! -f "$$file" ]; then \\
\t\t\techo "❌ Missing file: $$file"; \\
\t\t\tmissing_files="$$missing_files $$file"; \\
\t\tfi; \\
\tdone; \\
\tif [ -n "$$missing_files" ]; then \\
\t\techo "❌ Build cannot proceed due to missing files"; \\
\t\texit 1; \\
\telse \\
\t\techo "✅ All source files found"; \\
\tfi
endef

"""
        return content
    
    def _generate_makefile_targets(self, config: BuildConfiguration) -> str:
        """生成Makefile目标"""
        content = """# Default target
.PHONY: all clean check-files setup

all: check-files setup """
        
        # 添加所有目标
        target_names = []
        for target in config.targets:
            target_names.append(target.name)
            content += f"{target.name} "
        
        content += "\n\n"
        
        # 生成setup目标
        content += """# Setup build directory
setup:
\t@mkdir -p $(BUILD_DIR)
\t@echo "✅ Build directory ready: $(BUILD_DIR)"

# Check files target
check-files:
$(check_files)

"""
        
        # 为每个目标生成规则
        for target in config.targets:
            content += self._generate_target_rules(target, config)
        
        return content
    
    def _generate_target_rules(self, target: BuildTarget, config: BuildConfiguration) -> str:
        """为单个目标生成规则"""
        simulator_info = self.simulator_configs.get(config.simulator, self.simulator_configs["iverilog"])
        
        target_files = ([self.path_manager.get_relative_path(f) for f in target.source_files] + 
                       [self.path_manager.get_relative_path(f) for f in target.testbench_files])
        
        if target.target_type == "simulation":
            executable = f"$(BUILD_DIR)/{target.name}"
            
            content = f"""# Target: {target.name} ({target.target_type})
{target.name}: {executable}
\t@echo "🚀 Running simulation: {target.name}"
"""
            
            if config.simulator == "iverilog":
                content += f"\t@cd $(BUILD_DIR) && ./{target.name}\n"
            else:
                content += f"\t@cd $(BUILD_DIR) && {simulator_info.get('run_cmd', './')}{target.name}\n"
            
            content += f"""
{executable}: {' '.join(target_files)}
\t@echo "🔨 Compiling {target.name}..."
\t@mkdir -p $(BUILD_DIR)
"""
            
            if config.simulator == "iverilog":
                content += f"\t@$(COMPILE_CMD) $(COMPILE_FLAGS) $(OUTPUT_FLAG) $@ $^\n"
            else:
                # 对于其他仿真器，可能需要不同的编译命令
                content += f"\t@$(COMPILE_CMD) $(COMPILE_FLAGS) $(OUTPUT_FLAG) $(BUILD_DIR) $^\n"
            
            content += f"\t@echo \"✅ Compilation successful: $@\"\n\n"
            
        elif target.target_type == "lint":
            content = f"""# Target: {target.name} (lint check)
{target.name}:
\t@echo "🔍 Running lint check: {target.name}"
\t@verilator --lint-only --Wall {' '.join(target_files)} || echo "⚠️ Lint warnings found"
\t@echo "✅ Lint check completed"

"""
        
        return content
    
    def _generate_makefile_utilities(self, config: BuildConfiguration) -> str:
        """生成Makefile实用工具目标"""
        return """# Utility targets
clean:
\t@echo "🧹 Cleaning build artifacts..."
\t@rm -rf $(BUILD_DIR)
\t@rm -f *.vcd *.fst *.ghw
\t@echo "✅ Clean completed"

info:
\t@echo "📋 Build Configuration:"
\t@echo "  Simulator: $(SIMULATOR)"
\t@echo "  Sources: $(VERILOG_SOURCES)"
\t@echo "  Testbenches: $(TESTBENCH_SOURCES)"
\t@echo "  Output Directory: $(OUTPUT_DIR)"

help:
\t@echo "Available targets:"
\t@echo "  all       - Build all targets"
\t@echo "  clean     - Remove build artifacts"
\t@echo "  info      - Show build configuration"
\t@echo "  help      - Show this help message"
\t@echo "  check-files - Verify all source files exist"

# Prevent make from deleting intermediate files
.SECONDARY:
"""
    
    def _generate_bash_header(self, config: BuildConfiguration) -> str:
        """生成Bash脚本头部"""
        return f"""#!/bin/bash
# Enhanced Build Script for Verilog Simulation
# Generated by EnhancedBuildScriptGenerator
# Simulator: {config.simulator}

set -e  # Exit on any error
set -u  # Exit on undefined variables

# Color output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
WORKING_DIR="{config.working_directory or self.working_dir}"
OUTPUT_DIR="{config.output_directory or self.working_dir}"
BUILD_DIR="$OUTPUT_DIR/build"
SIMULATOR="{config.simulator}"

"""
    
    def _generate_bash_functions(self, config: BuildConfiguration) -> str:
        """生成Bash脚本函数"""
        return """# Utility functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_simulator() {
    if ! command -v "$SIMULATOR" &> /dev/null; then
        log_error "Simulator '$SIMULATOR' not found in PATH"
        log_info "Please install $SIMULATOR or update PATH"
        exit 1
    fi
    log_success "Simulator '$SIMULATOR' found"
}

check_files() {
    log_info "Checking source files..."
    local missing_files=()
    
    # Add your file list here based on configuration
    # This will be populated by the generator
    
    if [ ${#missing_files[@]} -ne 0 ]; then
        log_error "Missing files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        exit 1
    fi
    
    log_success "All source files found"
}

setup_build_dir() {
    log_info "Setting up build directory..."
    mkdir -p "$BUILD_DIR"
    log_success "Build directory ready: $BUILD_DIR"
}

cleanup() {
    log_info "Cleaning up build artifacts..."
    rm -rf "$BUILD_DIR"
    rm -f *.vcd *.fst *.ghw
    log_success "Cleanup completed"
}

"""
    
    def _generate_bash_main(self, config: BuildConfiguration) -> str:
        """生成Bash脚本主体"""
        content = """# Main script logic
main() {
    log_info "Starting enhanced build script..."
    
    # Parse command line arguments
    case "${1:-all}" in
        "clean")
            cleanup
            exit 0
            ;;
        "help")
            echo "Usage: $0 [target]"
            echo "Available targets:"
            echo "  all (default) - Build and run all targets"
            echo "  clean        - Clean build artifacts"
            echo "  help         - Show this help"
            exit 0
            ;;
        "all"|*)
            # Default build and run
            ;;
    esac
    
    # Setup
    check_simulator
    check_files
    setup_build_dir
    
    # Change to working directory
    cd "$WORKING_DIR"
    
"""
        
        # 为每个目标生成构建逻辑
        for target in config.targets:
            content += self._generate_bash_target_logic(target, config)
        
        content += """
    log_success "All operations completed successfully!"
}

# Run main function with all arguments
main "$@"
"""
        
        return content
    
    def _generate_bash_target_logic(self, target: BuildTarget, config: BuildConfiguration) -> str:
        """为单个目标生成Bash脚本逻辑"""
        simulator_info = self.simulator_configs.get(config.simulator, self.simulator_configs["iverilog"])
        
        target_files = ([self.path_manager.get_relative_path(f) for f in target.source_files] + 
                       [self.path_manager.get_relative_path(f) for f in target.testbench_files])
        
        executable = f"$BUILD_DIR/{target.name}"
        
        content = f"""    # Build target: {target.name}
    log_info "Building target: {target.name}"
    
"""
        
        if config.simulator == "iverilog":
            content += f"""    if iverilog -g2012 -Wall -o "{executable}" {' '.join(target_files)}; then
        log_success "Compilation successful: {target.name}"
        
        log_info "Running simulation: {target.name}"
        if cd "$BUILD_DIR" && ./{target.name}; then
            log_success "Simulation completed: {target.name}"
        else
            log_error "Simulation failed: {target.name}"
            exit 1
        fi
        cd "$WORKING_DIR"
    else
        log_error "Compilation failed: {target.name}"
        exit 1
    fi
    
"""
        
        return content


def create_build_configuration(module_name: str, design_files: List[Path], 
                              testbench_files: List[Path], simulator: str = "iverilog",
                              working_dir: Path = None) -> BuildConfiguration:
    """创建构建配置的便捷函数"""
    
    # 创建仿真目标
    sim_target = BuildTarget(
        name=f"{module_name}_sim",
        target_type="simulation",
        source_files=design_files,
        testbench_files=testbench_files
    )
    
    # 创建lint目标
    lint_target = BuildTarget(
        name=f"{module_name}_lint",
        target_type="lint",
        source_files=design_files,
        testbench_files=testbench_files
    )
    
    return BuildConfiguration(
        simulator=simulator,
        working_directory=working_dir or Path.cwd(),
        output_directory=working_dir or Path.cwd(),
        targets=[sim_target, lint_target]
    )