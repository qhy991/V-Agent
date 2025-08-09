#!/usr/bin/env python3
"""
统一的文件路径管理器
解决仿真执行中的文件路径问题
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PathSearchResult:
    """路径搜索结果"""
    found: bool
    path: Optional[Path] = None
    searched_paths: List[Path] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.searched_paths is None:
            self.searched_paths = []


class UnifiedPathManager:
    """统一路径管理器"""
    
    def __init__(self, base_workspace: Union[str, Path] = None, current_experiment_path: Optional[Union[str, Path]] = None):
        self.base_workspace = Path(base_workspace) if base_workspace else Path.cwd()
        # 🔧 新增：当前实验路径，用于优先级搜索
        self.current_experiment_path = Path(current_experiment_path) if current_experiment_path else None
        self.logger = logger
        
        # 标准目录结构
        self.standard_dirs = {
            "designs": ["designs", "src", "verilog", "hdl"],
            "testbenches": ["testbenches", "tests", "tb", "test"],
            "artifacts": ["artifacts", "output", "build", "generated"],
            "experiments": ["experiments", "exp"]
        }
    
    def resolve_design_file(self, module_name: str, filename: Optional[str] = None, 
                           existing_files: List[Path] = None) -> PathSearchResult:
        """解析设计文件路径"""
        return self._resolve_file(
            file_type="design",
            module_name=module_name,
            filename=filename,
            existing_files=existing_files
        )
    
    def resolve_testbench_file(self, module_name: str, filename: Optional[str] = None,
                              existing_files: List[Path] = None) -> PathSearchResult:
        """解析测试台文件路径"""
        return self._resolve_file(
            file_type="testbench", 
            module_name=module_name,
            filename=filename,
            existing_files=existing_files
        )
    
    def _resolve_file(self, file_type: str, module_name: str, filename: Optional[str] = None,
                     existing_files: List[Path] = None) -> PathSearchResult:
        """通用文件解析逻辑"""
        searched_paths = []
        
        # 1. 从existing_files中查找
        if existing_files:
            result = self._search_in_existing_files(file_type, module_name, filename, existing_files)
            if result.found:
                return result
            searched_paths.extend(result.searched_paths)
        
        # 2. 生成可能的文件名
        possible_names = self._generate_possible_filenames(file_type, module_name, filename)
        
        # 3. 生成搜索路径
        search_dirs = self._generate_search_directories(file_type)
        
        # 4. 执行搜索
        for search_dir in search_dirs:
            for name in possible_names:
                potential_path = search_dir / name
                searched_paths.append(potential_path)
                
                if potential_path.exists() and potential_path.is_file():
                    self.logger.info(f"✅ 找到{file_type}文件: {potential_path}")
                    return PathSearchResult(
                        found=True,
                        path=potential_path,
                        searched_paths=searched_paths
                    )
        
        return PathSearchResult(
            found=False,
            searched_paths=searched_paths,
            error=f"未找到{file_type}文件: 模块={module_name}, 文件名={filename}"
        )
    
    def _search_in_existing_files(self, file_type: str, module_name: str, 
                                 filename: Optional[str], existing_files: List[Path]) -> PathSearchResult:
        """在已有文件列表中搜索"""
        searched_paths = []
        
        # 按优先级搜索
        if filename:
            # 1. 精确匹配文件名
            for file_path in existing_files:
                searched_paths.append(file_path)
                if file_path.name == filename:
                    return PathSearchResult(found=True, path=file_path, searched_paths=searched_paths)
        
        # 2. 根据模块名和文件类型匹配
        possible_names = self._generate_possible_filenames(file_type, module_name, filename)
        for name in possible_names:
            for file_path in existing_files:
                searched_paths.append(file_path)
                if file_path.name == name:
                    return PathSearchResult(found=True, path=file_path, searched_paths=searched_paths)
        
        return PathSearchResult(found=False, searched_paths=searched_paths)
    
    def _generate_possible_filenames(self, file_type: str, module_name: str, 
                                   filename: Optional[str]) -> List[str]:
        """生成可能的文件名列表"""
        names = []
        
        if file_type == "design":
            names.extend([
                f"{module_name}.v",
                f"{module_name}_design.v",
                f"{module_name}.sv",
                f"design_{module_name}.v"
            ])
        elif file_type == "testbench":
            names.extend([
                f"testbench_{module_name}.v",
                f"{module_name}_testbench.v", 
                f"tb_{module_name}.v",
                f"{module_name}_tb.v",
                f"test_{module_name}.v"
            ])
        
        # 如果提供了具体文件名，优先使用
        if filename and filename not in names:
            names.insert(0, filename)
        
        return names
    
    def _generate_search_directories(self, file_type: str) -> List[Path]:
        """生成搜索目录列表，优先搜索当前实验目录"""
        search_dirs = []
        
        # 🎯 优先级 1：当前实验目录（最高优先级）
        if self.current_experiment_path and self.current_experiment_path.exists():
            self.logger.info(f"🎯 优先搜索当前实验目录: {self.current_experiment_path}")
            # 直接在当前实验目录中搜索
            search_dirs.append(self.current_experiment_path)
            # 根据文件类型搜索相应子目录
            if file_type == "design":
                search_dirs.append(self.current_experiment_path / "designs")
            elif file_type == "testbench":
                search_dirs.append(self.current_experiment_path / "testbenches")
        
        # 基础搜索路径（优先级较低）
        base_paths = [
            self.base_workspace,
            Path.cwd(),
            self.base_workspace.parent if self.base_workspace.parent else Path.cwd()
        ]
        
        # 根据文件类型选择子目录
        if file_type == "design":
            subdirs = self.standard_dirs["designs"]
        elif file_type == "testbench":
            subdirs = self.standard_dirs["testbenches"]
        else:
            subdirs = []
        
        # 为每个基础路径添加子目录
        for base_path in base_paths:
            # 1. 直接在基础目录中搜索
            search_dirs.append(base_path)
            
            # 2. 搜索标准子目录
            for subdir in subdirs:
                search_dirs.append(base_path / subdir)
            
            # 3. 🔧 智能搜索实验目录结构 (experiments/design_*/designs)，按时间戳排序
            experiments_dir = base_path / "experiments"
            if experiments_dir.exists():
                try:
                    # 获取所有实验目录并按时间戳排序（最新的优先）
                    exp_dirs = []
                    for exp_item in experiments_dir.iterdir():
                        if exp_item.is_dir() and (exp_item.name.startswith('design_') or exp_item.name.startswith('experiment_')):
                            exp_dirs.append(exp_item)
                    
                    # 按修改时间排序（最新的优先）
                    exp_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    
                    # 如果存在当前实验路径，确保它排在最前面
                    if self.current_experiment_path and self.current_experiment_path in exp_dirs:
                        exp_dirs.remove(self.current_experiment_path)
                        exp_dirs.insert(0, self.current_experiment_path)
                        self.logger.info(f"🎯 当前实验目录优先: {self.current_experiment_path}")
                    
                    # 添加排序后的实验目录到搜索路径
                    for exp_item in exp_dirs:
                        # 跳过当前实验（已在优先级1处理）
                        if self.current_experiment_path and exp_item == self.current_experiment_path:
                            continue
                        
                        # 直接搜索实验目录
                        search_dirs.append(exp_item)
                        # 搜索实验目录下的特定子目录
                        for subdir in subdirs:
                            search_dirs.append(exp_item / subdir)
                        # 添加其他标准目录
                        search_dirs.append(exp_item / "testbenches")
                        search_dirs.append(exp_item / "reports")
                        search_dirs.append(exp_item / "temp")
                        
                except PermissionError:
                    continue
            
            # 4. 搜索传统file_workspace目录
            file_workspace = base_path / "file_workspace"
            if file_workspace.exists():
                search_dirs.append(file_workspace)
                for subdir in subdirs:
                    search_dirs.append(file_workspace / subdir)
                search_dirs.append(file_workspace / "testbenches")
            
            # 5. 搜索logs目录结构 (向后兼容)
            logs_dir = base_path / "logs"
            if logs_dir.exists():
                try:
                    for log_item in logs_dir.iterdir():
                        if log_item.is_dir():
                            search_dirs.append(log_item / "artifacts")
                except PermissionError:
                    continue
        
        # 去重并返回存在的目录
        unique_dirs = []
        seen = set()
        for dir_path in search_dirs:
            if dir_path not in seen and dir_path.exists():
                seen.add(dir_path)
                unique_dirs.append(dir_path)
        
        return unique_dirs
    
    def create_unified_workspace(self, experiment_id: str = None) -> Dict[str, Path]:
        """创建统一的工作空间结构"""
        if experiment_id:
            workspace_root = self.base_workspace / "experiments" / experiment_id
        else:
            workspace_root = self.base_workspace / "temp_workspace"
        
        # 创建标准目录结构
        directories = {}
        for dir_type, dir_names in self.standard_dirs.items():
            dir_path = workspace_root / dir_names[0]  # 使用第一个名称作为默认
            dir_path.mkdir(parents=True, exist_ok=True)
            directories[dir_type] = dir_path
        
        self.logger.info(f"✅ 创建统一工作空间: {workspace_root}")
        return directories
    
    def get_relative_path(self, file_path: Path, base_path: Path = None) -> str:
        """获取相对路径，用于生成构建脚本"""
        if base_path is None:
            base_path = self.base_workspace
        
        try:
            return str(file_path.relative_to(base_path))
        except ValueError:
            # 如果无法生成相对路径，返回绝对路径
            return str(file_path)
    
    def validate_file_existence(self, files: List[Path]) -> Dict[str, Any]:
        """验证文件存在性"""
        result = {
            "all_exist": True,
            "existing_files": [],
            "missing_files": [],
            "invalid_files": []
        }
        
        for file_path in files:
            if not file_path.exists():
                result["missing_files"].append(str(file_path))
                result["all_exist"] = False
            elif not file_path.is_file():
                result["invalid_files"].append(str(file_path))
                result["all_exist"] = False
            else:
                result["existing_files"].append(str(file_path))
        
        return result


# 全局实例
_path_manager_instance = None

def get_path_manager(base_workspace: Union[str, Path] = None, current_experiment_path: Optional[Union[str, Path]] = None) -> UnifiedPathManager:
    """获取路径管理器实例"""
    global _path_manager_instance
    if _path_manager_instance is None:
        _path_manager_instance = UnifiedPathManager(base_workspace, current_experiment_path)
    elif current_experiment_path is not None:
        # 如果提供了新的当前实验路径，更新实例
        _path_manager_instance.current_experiment_path = Path(current_experiment_path) if current_experiment_path else None
    return _path_manager_instance

def reset_path_manager():
    """重置路径管理器实例"""
    global _path_manager_instance
    _path_manager_instance = None