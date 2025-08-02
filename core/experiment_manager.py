#!/usr/bin/env python3
"""
实验文件夹管理系统
Experiment Folder Management System
"""

import os
import shutil
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

class ExperimentManager:
    """实验管理器 - 为每次TDD实验创建独立的文件夹"""
    
    def __init__(self, base_workspace: str = None):
        """
        初始化实验管理器
        
        Args:
            base_workspace: 基础工作空间路径，默认为项目根目录/experiments
        """
        self.project_root = Path(__file__).parent.parent
        if base_workspace:
            self.base_workspace = Path(base_workspace)
        else:
            self.base_workspace = self.project_root / "experiments"
        
        self.base_workspace.mkdir(exist_ok=True)
        self.logger = logging.getLogger(f"{__name__}.ExperimentManager")
        
        # 当前实验信息
        self.current_experiment = None
        self.current_experiment_path = None
        
    def create_new_experiment(self, experiment_name: str = None, description: str = "") -> Path:
        """
        创建新的实验文件夹
        
        Args:
            experiment_name: 实验名称，如果为None则自动生成
            description: 实验描述
            
        Returns:
            实验文件夹路径
        """
        # 生成实验名称
        if experiment_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            experiment_name = f"tdd_experiment_{timestamp}"
        
        # 确保实验名称唯一
        experiment_path = self.base_workspace / experiment_name
        counter = 1
        while experiment_path.exists():
            experiment_path = self.base_workspace / f"{experiment_name}_{counter}"
            counter += 1
        
        # 创建实验文件夹结构
        experiment_path.mkdir(parents=True)
        
        # 创建子文件夹
        subdirs = [
            "designs",      # 设计文件
            "testbenches",  # 测试台文件
            "outputs",      # 仿真输出
            "logs",         # 日志文件
            "artifacts",    # 其他产物
            "dependencies"  # 依赖文件
        ]
        
        for subdir in subdirs:
            (experiment_path / subdir).mkdir()
        
        # 创建实验元数据
        metadata = {
            "experiment_name": experiment_name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "iterations": 0,
            "files_created": 0,
            "last_updated": datetime.now().isoformat()
        }
        
        metadata_file = experiment_path / "experiment_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # 设置为当前实验
        self.current_experiment = experiment_name
        self.current_experiment_path = experiment_path
        
        self.logger.info(f"🆕 创建实验文件夹: {experiment_path}")
        return experiment_path
    
    def set_current_experiment(self, experiment_name: str) -> bool:
        """
        设置当前实验
        
        Args:
            experiment_name: 实验名称
            
        Returns:
            是否设置成功
        """
        experiment_path = self.base_workspace / experiment_name
        if experiment_path.exists():
            self.current_experiment = experiment_name
            self.current_experiment_path = experiment_path
            self.logger.info(f"🎯 切换到实验: {experiment_name}")
            return True
        else:
            self.logger.error(f"❌ 实验不存在: {experiment_name}")
            return False
    
    def get_experiment_path(self, subdir: str = None) -> Optional[Path]:
        """
        获取当前实验的文件夹路径
        
        Args:
            subdir: 子文件夹名称（designs, testbenches, outputs, logs, artifacts, dependencies）
            
        Returns:
            文件夹路径
        """
        if not self.current_experiment_path:
            self.logger.warning("⚠️ 没有活跃的实验")
            return None
        
        if subdir:
            return self.current_experiment_path / subdir
        else:
            return self.current_experiment_path
    
    def save_file(self, content: str, filename: str, subdir: str = "artifacts", 
                 description: str = "") -> Optional[Path]:
        """
        在当前实验文件夹中保存文件
        
        Args:
            content: 文件内容
            filename: 文件名
            subdir: 子文件夹（designs, testbenches, outputs, logs, artifacts, dependencies）
            description: 文件描述
            
        Returns:
            保存的文件路径
        """
        if not self.current_experiment_path:
            self.logger.error("❌ 没有活跃的实验，无法保存文件")
            return None
        
        # 确定保存路径
        save_dir = self.current_experiment_path / subdir
        save_dir.mkdir(exist_ok=True)
        
        file_path = save_dir / filename
        
        # 如果文件已存在，创建备份或版本号
        if file_path.exists():
            base_name = file_path.stem
            suffix = file_path.suffix
            counter = 1
            while file_path.exists():
                new_name = f"{base_name}_v{counter}{suffix}"
                file_path = save_dir / new_name
                counter += 1
        
        # 保存文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 更新实验元数据
            self._update_experiment_metadata(files_created_delta=1)
            
            # 记录文件信息
            self._log_file_creation(file_path, description, subdir)
            
            self.logger.info(f"💾 保存文件: {file_path.relative_to(self.current_experiment_path)}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"❌ 保存文件失败 {filename}: {str(e)}")
            return None
    
    def copy_dependency(self, source_path: str, description: str = "") -> Optional[Path]:
        """
        复制依赖文件到当前实验的dependencies文件夹
        
        Args:
            source_path: 源文件路径
            description: 文件描述
            
        Returns:
            复制后的文件路径
        """
        if not self.current_experiment_path:
            self.logger.error("❌ 没有活跃的实验，无法复制依赖")
            return None
        
        source = Path(source_path)
        if not source.exists():
            self.logger.error(f"❌ 源文件不存在: {source_path}")
            return None
        
        # 复制到dependencies文件夹
        deps_dir = self.current_experiment_path / "dependencies"
        deps_dir.mkdir(exist_ok=True)
        
        dest_path = deps_dir / source.name
        
        try:
            shutil.copy2(source, dest_path)
            self._log_file_creation(dest_path, f"依赖文件: {description}", "dependencies")
            self.logger.info(f"📋 复制依赖: {source.name}")
            return dest_path
        except Exception as e:
            self.logger.error(f"❌ 复制依赖失败: {str(e)}")
            return None
    
    def start_iteration(self, iteration_number: int):
        """开始新的迭代"""
        if self.current_experiment_path:
            self._update_experiment_metadata(iterations_delta=1)
            iteration_log = self.current_experiment_path / "logs" / f"iteration_{iteration_number}.log"
            self.logger.info(f"🔄 开始第 {iteration_number} 次迭代")
    
    def finish_experiment(self, success: bool = False, final_notes: str = ""):
        """结束当前实验"""
        if not self.current_experiment_path:
            return
        
        # 更新最终状态
        try:
            metadata_file = self.current_experiment_path / "experiment_metadata.json"
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            metadata.update({
                "status": "completed" if success else "failed",
                "completed_at": datetime.now().isoformat(),
                "final_notes": final_notes,
                "last_updated": datetime.now().isoformat()
            })
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"🏁 实验结束: {self.current_experiment} ({'成功' if success else '失败'})")
            
        except Exception as e:
            self.logger.error(f"❌ 更新实验状态失败: {str(e)}")
    
    def list_experiments(self) -> List[Dict[str, Any]]:
        """列出所有实验"""
        experiments = []
        
        for exp_dir in self.base_workspace.iterdir():
            if exp_dir.is_dir():
                metadata_file = exp_dir / "experiment_metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        metadata['path'] = str(exp_dir)
                        experiments.append(metadata)
                    except Exception as e:
                        self.logger.warning(f"⚠️ 读取实验元数据失败 {exp_dir.name}: {e}")
        
        # 按创建时间排序
        experiments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return experiments
    
    def cleanup_old_experiments(self, keep_days: int = 7):
        """清理旧的实验文件夹"""
        cutoff_time = time.time() - (keep_days * 24 * 3600)
        
        for exp_dir in self.base_workspace.iterdir():
            if exp_dir.is_dir() and exp_dir.stat().st_mtime < cutoff_time:
                try:
                    shutil.rmtree(exp_dir)
                    self.logger.info(f"🗑️ 清理旧实验: {exp_dir.name}")
                except Exception as e:
                    self.logger.error(f"❌ 清理失败 {exp_dir.name}: {e}")
    
    def get_experiment_summary(self) -> Dict[str, Any]:
        """获取当前实验的摘要信息"""
        if not self.current_experiment_path:
            return {"error": "没有活跃的实验"}
        
        try:
            metadata_file = self.current_experiment_path / "experiment_metadata.json"
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 统计文件数量
            file_counts = {}
            for subdir in ["designs", "testbenches", "outputs", "logs", "artifacts", "dependencies"]:
                subdir_path = self.current_experiment_path / subdir
                if subdir_path.exists():
                    file_counts[subdir] = len(list(subdir_path.glob("*")))
                else:
                    file_counts[subdir] = 0
            
            metadata["file_counts"] = file_counts
            metadata["total_files"] = sum(file_counts.values())
            
            return metadata
            
        except Exception as e:
            return {"error": f"读取实验摘要失败: {str(e)}"}
    
    def _update_experiment_metadata(self, iterations_delta: int = 0, files_created_delta: int = 0):
        """更新实验元数据"""
        if not self.current_experiment_path:
            return
        
        try:
            metadata_file = self.current_experiment_path / "experiment_metadata.json"
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            metadata["iterations"] += iterations_delta
            metadata["files_created"] += files_created_delta
            metadata["last_updated"] = datetime.now().isoformat()
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"❌ 更新元数据失败: {str(e)}")
    
    def _log_file_creation(self, file_path: Path, description: str, category: str):
        """记录文件创建日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "file_path": str(file_path.relative_to(self.current_experiment_path)),
            "filename": file_path.name,
            "category": category,
            "description": description,
            "size_bytes": file_path.stat().st_size if file_path.exists() else 0
        }
        
        # 添加到文件创建日志
        files_log = self.current_experiment_path / "logs" / "files_created.jsonl"
        files_log.parent.mkdir(exist_ok=True)
        
        with open(files_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


# 全局实验管理器实例
_experiment_manager = None

def get_experiment_manager() -> ExperimentManager:
    """获取全局实验管理器实例"""
    global _experiment_manager
    if _experiment_manager is None:
        _experiment_manager = ExperimentManager()
    return _experiment_manager

def create_experiment(name: str = None, description: str = "") -> Path:
    """便捷函数：创建新实验"""
    return get_experiment_manager().create_new_experiment(name, description)

def save_experiment_file(content: str, filename: str, subdir: str = "artifacts", description: str = "") -> Optional[Path]:
    """便捷函数：保存实验文件"""
    return get_experiment_manager().save_file(content, filename, subdir, description)