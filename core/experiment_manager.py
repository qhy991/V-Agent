#!/usr/bin/env python3
"""
实验管理器 - 实现实验数据隔离
==================================================

这个模块为每个实验创建独立的工作环境：
✅ 每个实验有独立的工作目录
✅ 实验间数据完全隔离
✅ 自动清理实验数据
✅ 实验元数据管理
"""

import json
import logging
import shutil
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import time


@dataclass
class ExperimentInfo:
    """实验信息"""
    experiment_id: str
    experiment_name: str
    created_at: str
    status: str  # "running", "completed", "failed", "cancelled"
    task_description: str
    workspace_path: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ExperimentManager:
    """实验管理器"""
    
    def __init__(self, base_workspace: Path = None):
        self.logger = logging.getLogger(__name__)
        
        # 设置基础工作空间
        if base_workspace is None:
            base_workspace = Path.cwd() / "experiments"
        
        self.base_workspace = Path(base_workspace)
        self.base_workspace.mkdir(parents=True, exist_ok=True)
        
        # 实验注册表
        self.experiments: Dict[str, ExperimentInfo] = {}
        self.registry_file = self.base_workspace / "experiment_registry.json"
        
        # 🎯 修复：添加当前实验路径属性
        self.current_experiment_path: Optional[Path] = None
        self.current_experiment_id: Optional[str] = None
        
        # 加载现有实验注册表
        self._load_registry()
        
        self.logger.info(f"🧪 实验管理器已初始化，基础工作空间: {self.base_workspace}")
    
    def create_experiment(self, experiment_name: str, task_description: str, 
                         metadata: Dict[str, Any] = None) -> ExperimentInfo:
        """创建新实验"""
        # 生成实验ID
        experiment_id = f"{experiment_name}_{int(time.time())}"
        
        # 创建实验工作目录
        workspace_path = self.base_workspace / experiment_id
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        subdirs = ["designs", "testbenches", "reports", "logs", "temp"]
        for subdir in subdirs:
            (workspace_path / subdir).mkdir(exist_ok=True)
        
        # 创建实验信息
        experiment_info = ExperimentInfo(
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            created_at=datetime.now().isoformat(),
            status="running",
            task_description=task_description,
            workspace_path=str(workspace_path),
            metadata=metadata or {}
        )
        
        # 保存到注册表
        self.experiments[experiment_id] = experiment_info
        self._save_registry()
        
        # 🎯 修复：设置当前实验路径
        self.current_experiment_path = workspace_path
        self.current_experiment_id = experiment_id
        
        self.logger.info(f"🧪 创建实验: {experiment_id}")
        self.logger.info(f"   工作目录: {workspace_path}")
        self.logger.info(f"   任务描述: {task_description[:100]}...")
        
        return experiment_info
    
    def get_experiment_workspace(self, experiment_id: str) -> Optional[Path]:
        """获取实验工作目录"""
        if experiment_id in self.experiments:
            return Path(self.experiments[experiment_id].workspace_path)
        return None
    
    def get_experiment_info(self, experiment_id: str) -> Optional[ExperimentInfo]:
        """获取实验信息"""
        return self.experiments.get(experiment_id)
    
    def update_experiment_status(self, experiment_id: str, status: str, 
                                metadata: Dict[str, Any] = None) -> bool:
        """更新实验状态"""
        if experiment_id not in self.experiments:
            return False
        
        experiment = self.experiments[experiment_id]
        experiment.status = status
        
        if metadata:
            experiment.metadata.update(metadata)
        
        self._save_registry()
        self.logger.info(f"🧪 更新实验状态: {experiment_id} -> {status}")
        
        return True
    
    def list_experiments(self, status_filter: str = None) -> List[ExperimentInfo]:
        """列出实验"""
        experiments = list(self.experiments.values())
        
        if status_filter:
            experiments = [exp for exp in experiments if exp.status == status_filter]
        
        return sorted(experiments, key=lambda x: x.created_at, reverse=True)
    
    def cleanup_experiment(self, experiment_id: str, keep_logs: bool = True) -> bool:
        """清理实验数据"""
        if experiment_id not in self.experiments:
            return False
        
        experiment = self.experiments[experiment_id]
        workspace_path = Path(experiment.workspace_path)
        
        try:
            if keep_logs:
                # 保留日志目录
                logs_dir = workspace_path / "logs"
                if logs_dir.exists():
                    # 只删除临时文件，保留日志
                    temp_dir = workspace_path / "temp"
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir)
                    
                    # 清理其他临时文件
                    for file in workspace_path.glob("*.tmp"):
                        file.unlink()
            else:
                # 完全删除工作目录
                if workspace_path.exists():
                    shutil.rmtree(workspace_path)
            
            # 从注册表中移除
            del self.experiments[experiment_id]
            self._save_registry()
            
            self.logger.info(f"🧪 清理实验: {experiment_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 清理实验失败 {experiment_id}: {str(e)}")
            return False
    
    def cleanup_old_experiments(self, keep_days: int = 7) -> int:
        """清理旧实验"""
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 3600)
        cleaned_count = 0
        
        for experiment_id, experiment in list(self.experiments.items()):
            try:
                created_time = datetime.fromisoformat(experiment.created_at).timestamp()
                if created_time < cutoff_time:
                    if self.cleanup_experiment(experiment_id):
                        cleaned_count += 1
            except Exception as e:
                self.logger.warning(f"⚠️ 处理旧实验失败 {experiment_id}: {str(e)}")
        
        self.logger.info(f"🧪 清理了 {cleaned_count} 个旧实验")
        return cleaned_count
    
    def get_experiment_file_manager(self, experiment_id: str):
        """获取实验专用的文件管理器"""
        workspace = self.get_experiment_workspace(experiment_id)
        if not workspace:
            return None
        
        from core.file_manager import CentralFileManager
        return CentralFileManager(workspace)
    
    def get_experiment_context_manager(self, experiment_id: str):
        """获取实验专用的上下文管理器"""
        from core.context_manager import FullContextManager
        return FullContextManager(experiment_id)
    
    def save_experiment_metadata(self, experiment_id: str, metadata: Dict[str, Any]) -> bool:
        """保存实验元数据"""
        if experiment_id not in self.experiments:
            return False
        
        experiment = self.experiments[experiment_id]
        experiment.metadata.update(metadata)
        
        # 保存到元数据文件
        workspace = self.get_experiment_workspace(experiment_id)
        if workspace:
            metadata_file = workspace / "experiment_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        self._save_registry()
        return True
    
    def load_experiment_metadata(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """加载实验元数据"""
        workspace = self.get_experiment_workspace(experiment_id)
        if not workspace:
            return None
        
        metadata_file = workspace / "experiment_metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"❌ 加载实验元数据失败: {str(e)}")
        
        return None
    
    def _load_registry(self):
        """加载实验注册表"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for exp_data in data.get("experiments", []):
                        experiment = ExperimentInfo(**exp_data)
                        self.experiments[experiment.experiment_id] = experiment
                self.logger.info(f"📋 加载了 {len(self.experiments)} 个实验")
            except Exception as e:
                self.logger.error(f"❌ 加载实验注册表失败: {str(e)}")
    
    def _save_registry(self):
        """保存实验注册表"""
        try:
            data = {
                "experiments": [asdict(exp) for exp in self.experiments.values()],
                "last_updated": datetime.now().isoformat()
            }
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"❌ 保存实验注册表失败: {str(e)}")


# 全局实验管理器实例
_experiment_manager = None


def get_experiment_manager() -> ExperimentManager:
    """获取全局实验管理器实例"""
    global _experiment_manager
    if _experiment_manager is None:
        _experiment_manager = ExperimentManager()
    return _experiment_manager


def create_experiment_session(experiment_name: str, task_description: str, 
                            metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """创建实验会话"""
    manager = get_experiment_manager()
    experiment_info = manager.create_experiment(experiment_name, task_description, metadata)
    
    # 获取实验专用的组件
    file_manager = manager.get_experiment_file_manager(experiment_info.experiment_id)
    context_manager = manager.get_experiment_context_manager(experiment_info.experiment_id)
    
    return {
        "experiment_id": experiment_info.experiment_id,
        "experiment_info": experiment_info,
        "file_manager": file_manager,
        "context_manager": context_manager,
        "workspace_path": experiment_info.workspace_path
    }