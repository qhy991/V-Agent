#!/usr/bin/env python3
"""
中央文件管理器 - 统一管理所有生成的文件
==================================================

这个模块解决了多智能体协作中的文件管理和上下文传递问题：
✅ 统一的文件保存和获取接口
✅ 自动的文件类型识别和分类
✅ 跨智能体的文件引用追踪
✅ 工作目录隔离和管理
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class FileReference:
    """文件引用信息"""
    file_id: str
    file_path: str
    file_type: str  # "verilog", "testbench", "report", "config", etc.
    content_hash: str
    created_by: str  # 创建该文件的智能体ID
    created_at: str
    description: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CentralFileManager:
    """中央文件管理器"""
    
    def __init__(self, workspace_root: Path = None):
        self.logger = logging.getLogger(__name__)
        
        # 设置工作空间根目录
        if workspace_root is None:
            workspace_root = Path.cwd() / "file_workspace"
        
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        self.design_dir = self.workspace_root / "designs"
        self.testbench_dir = self.workspace_root / "testbenches"
        self.report_dir = self.workspace_root / "reports"
        self.temp_dir = self.workspace_root / "temp"
        
        for dir_path in [self.design_dir, self.testbench_dir, self.report_dir, self.temp_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # 文件注册表
        self.file_registry: Dict[str, FileReference] = {}
        self.registry_file = self.workspace_root / "file_registry.json"
        
        # 加载现有注册表
        self._load_registry()
        
        self.logger.info(f"🗂️ 中央文件管理器已初始化，工作空间: {self.workspace_root}")
    
    def save_file(self, content: str, filename: str, file_type: str, 
                 created_by: str, description: str = "") -> FileReference:
        """
        保存文件并返回文件引用
        
        Args:
            content: 文件内容
            filename: 文件名
            file_type: 文件类型 (verilog, testbench, report, etc.)
            created_by: 创建者ID
            description: 文件描述
            
        Returns:
            文件引用对象
        """
        # 生成唯一的文件ID
        file_id = str(uuid.uuid4())[:8]
        
        # 确定保存目录
        target_dir = self._get_target_directory(file_type)
        
        # 生成唯一的文件路径
        file_extension = self._get_file_extension(file_type)
        if not filename.endswith(file_extension):
            filename = f"{filename}{file_extension}"
        
        # 避免文件名冲突
        base_name = Path(filename).stem
        extension = Path(filename).suffix
        counter = 1
        while (target_dir / filename).exists():
            filename = f"{base_name}_{counter}{extension}"
            counter += 1
        
        file_path = target_dir / filename
        
        # 保存文件
        file_path.write_text(content, encoding='utf-8')
        
        # 计算内容哈希
        content_hash = str(hash(content))
        
        # 创建文件引用
        file_ref = FileReference(
            file_id=file_id,
            file_path=str(file_path),
            file_type=file_type,
            content_hash=content_hash,
            created_by=created_by,
            created_at=datetime.now().isoformat(),
            description=description
        )
        
        # 注册文件
        self.file_registry[file_id] = file_ref
        self._save_registry()
        
        self.logger.info(f"💾 文件已保存: {filename} (ID: {file_id}, 类型: {file_type})")
        return file_ref
    
    def get_file(self, file_id: str) -> Optional[FileReference]:
        """根据文件ID获取文件引用"""
        return self.file_registry.get(file_id)
    
    def get_files_by_type(self, file_type: str) -> List[FileReference]:
        """根据文件类型获取所有文件引用"""
        return [ref for ref in self.file_registry.values() if ref.file_type == file_type]
    
    def get_files_by_creator(self, creator_id: str) -> List[FileReference]:
        """根据创建者获取所有文件引用"""
        return [ref for ref in self.file_registry.values() if ref.created_by == creator_id]
    
    def get_latest_files_by_type(self, file_type: str, limit: int = 5) -> List[FileReference]:
        """获取指定类型的最新文件"""
        files = self.get_files_by_type(file_type)
        return sorted(files, key=lambda x: x.created_at, reverse=True)[:limit]
    
    def read_file_content(self, file_ref: Union[str, FileReference]) -> str:
        """读取文件内容"""
        if isinstance(file_ref, str):
            file_ref = self.get_file(file_ref)
            if not file_ref:
                raise FileNotFoundError(f"文件ID {file_ref} 不存在")
        
        file_path = Path(file_ref.file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件 {file_path} 不存在")
        
        return file_path.read_text(encoding='utf-8')
    
    def update_file_metadata(self, file_id: str, metadata: Dict[str, Any]) -> bool:
        """更新文件元数据"""
        if file_id not in self.file_registry:
            return False
        
        self.file_registry[file_id].metadata.update(metadata)
        self._save_registry()
        return True
    
    def list_all_files(self) -> List[FileReference]:
        """列出所有文件"""
        return list(self.file_registry.values())
    
    def cleanup_old_files(self, keep_latest: int = 10):
        """清理旧文件，保留最新的几个文件"""
        all_files = sorted(self.file_registry.values(), 
                          key=lambda x: x.created_at, reverse=True)
        
        if len(all_files) <= keep_latest:
            return
        
        files_to_remove = all_files[keep_latest:]
        for file_ref in files_to_remove:
            try:
                Path(file_ref.file_path).unlink(missing_ok=True)
                del self.file_registry[file_ref.file_id]
                self.logger.info(f"🗑️ 清理旧文件: {file_ref.file_path}")
            except Exception as e:
                self.logger.warning(f"清理文件失败: {e}")
        
        self._save_registry()
    
    def get_workspace_info(self) -> Dict[str, Any]:
        """获取工作空间信息"""
        return {
            "workspace_root": str(self.workspace_root),
            "total_files": len(self.file_registry),
            "file_types": list(set(ref.file_type for ref in self.file_registry.values())),
            "recent_files": [
                {
                    "file_id": ref.file_id,
                    "filename": Path(ref.file_path).name,
                    "file_type": ref.file_type,
                    "created_by": ref.created_by,
                    "created_at": ref.created_at
                }
                for ref in sorted(self.file_registry.values(), 
                                key=lambda x: x.created_at, reverse=True)[:5]
            ]
        }
    
    def _get_target_directory(self, file_type: str) -> Path:
        """根据文件类型确定目标目录"""
        type_mapping = {
            "verilog": self.design_dir,
            "design": self.design_dir,
            "testbench": self.testbench_dir,
            "tb": self.testbench_dir,
            "report": self.report_dir,
            "analysis": self.report_dir,
            "temp": self.temp_dir
        }
        return type_mapping.get(file_type.lower(), self.temp_dir)
    
    def _get_file_extension(self, file_type: str) -> str:
        """根据文件类型确定文件扩展名"""
        type_mapping = {
            "verilog": ".v",
            "design": ".v",
            "testbench": ".v",
            "tb": ".v",
            "report": ".txt",
            "analysis": ".json",
            "temp": ".tmp"
        }
        return type_mapping.get(file_type.lower(), ".txt")
    
    def _load_registry(self):
        """加载文件注册表"""
        if not self.registry_file.exists():
            return
        
        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                registry_data = json.load(f)
            
            for file_id, data in registry_data.items():
                self.file_registry[file_id] = FileReference(**data)
            
            self.logger.debug(f"📋 加载文件注册表: {len(self.file_registry)} 个文件")
        except Exception as e:
            self.logger.warning(f"加载文件注册表失败: {e}")
    
    def _save_registry(self):
        """保存文件注册表"""
        try:
            registry_data = {
                file_id: asdict(file_ref) 
                for file_id, file_ref in self.file_registry.items()
            }
            
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存文件注册表失败: {e}")


# 全局文件管理器实例（单例模式）
_global_file_manager: Optional[CentralFileManager] = None

def get_file_manager() -> CentralFileManager:
    """获取全局文件管理器实例"""
    global _global_file_manager
    if _global_file_manager is None:
        _global_file_manager = CentralFileManager()
    return _global_file_manager

def initialize_file_manager(workspace_root: Path = None) -> CentralFileManager:
    """初始化全局文件管理器"""
    global _global_file_manager
    _global_file_manager = CentralFileManager(workspace_root)
    return _global_file_manager