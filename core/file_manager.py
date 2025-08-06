#!/usr/bin/env python3
"""
中央文件管理器 - 统一管理所有生成的文件
==================================================

这个模块解决了多智能体协作中的文件管理和上下文传递问题：
✅ 统一的文件保存和获取接口
✅ 自动的文件类型识别和分类
✅ 跨智能体的文件引用追踪
✅ 工作目录隔离和管理
✅ 端口信息验证和一致性检查
✅ 版本管理和回滚机制
"""

import json
import logging
import uuid
import hashlib
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
    # 🎯 新增：端口信息验证
    port_info: Dict[str, Any] = None  # 存储模块端口信息
    version: int = 1  # 文件版本号

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.port_info is None:
            self.port_info = {}


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
        
        # 🎯 新增：端口信息缓存
        self.port_info_cache: Dict[str, Dict[str, Any]] = {}
        
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
        # 🎯 新增：提取和验证端口信息
        port_info = self._extract_port_info(content, file_type)
        
        # 检查是否已存在同名文件
        existing_file_id = None
        for file_id, file_ref in self.file_registry.items():
            if file_ref.filename == filename and file_ref.file_type == file_type:
                existing_file_id = file_id
                break
        
        # 如果存在同名文件，进行版本管理
        if existing_file_id:
            old_file_ref = self.file_registry[existing_file_id]
            
            # 🎯 新增：端口一致性验证
            if file_type == "verilog" and old_file_ref.port_info:
                if not self._validate_port_consistency(old_file_ref.port_info, port_info):
                    self.logger.warning(f"⚠️ 端口信息不一致: {filename}")
            
            # 创建新版本
            new_version = old_file_ref.version + 1
            versioned_filename = f"{filename}_v{new_version}"
            self.logger.info(f"📝 创建新版本: {versioned_filename}")
        else:
            versioned_filename = filename
            new_version = 1
        
        # 确定目标目录
        target_dir = self._get_target_directory(file_type)
        file_path = target_dir / versioned_filename
        
        # 添加文件扩展名
        if not file_path.suffix:
            extension = self._get_file_extension(file_type)
            file_path = file_path.with_suffix(extension)
        
        # 保存文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 计算内容哈希
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # 创建文件引用
            file_id = str(uuid.uuid4())
            file_ref = FileReference(
                file_id=file_id,
                file_path=str(file_path),
                file_type=file_type,
                content_hash=content_hash,
                created_by=created_by,
                created_at=datetime.now().isoformat(),
                description=description,
                port_info=port_info,
                version=new_version
            )
            
            # 注册文件
            self.file_registry[file_id] = file_ref
            self._save_registry()
            
            self.logger.info(f"💾 文件已保存: {file_path} (ID: {file_id})")
            
            # 🆕 记录到TaskContext（如果可用）
            if hasattr(self, 'task_context') and self.task_context and hasattr(self.task_context, 'add_file_operation'):
                self.task_context.add_file_operation(
                    operation_type="create",
                    file_path=str(file_path),
                    agent_id=created_by,
                    success=True,
                    file_size=len(content.encode('utf-8'))
                )
            
            return file_ref
            
        except Exception as e:
            self.logger.error(f"❌ 保存文件失败: {file_path} - {str(e)}")
            
            # 🆕 记录失败到TaskContext（如果可用）
            if hasattr(self, 'task_context') and self.task_context and hasattr(self.task_context, 'add_file_operation'):
                self.task_context.add_file_operation(
                    operation_type="create",
                    file_path=str(file_path),
                    agent_id=created_by,
                    success=False,
                    error=str(e)
                )
            
            raise
    
    def _extract_port_info(self, content: str, file_type: str) -> Dict[str, Any]:
        """提取Verilog模块的端口信息"""
        if file_type != "verilog":
            return {}
        
        import re
        
        # 提取模块定义
        module_pattern = r'module\s+(\w+)\s*\(([^)]+)\);'
        match = re.search(module_pattern, content, re.DOTALL)
        
        if not match:
            return {}
        
        module_name = match.group(1)
        port_declarations = match.group(2)
        
        # 解析端口
        ports = []
        port_lines = [line.strip() for line in port_declarations.split(',')]
        
        for line in port_lines:
            if not line:
                continue
            
            # 匹配端口声明
            port_match = re.search(r'(input|output|inout)\s*(?:\[(\d+):(\d+)\])?\s*(\w+)', line)
            if port_match:
                direction = port_match.group(1)
                msb = port_match.group(2)
                lsb = port_match.group(3)
                port_name = port_match.group(4)
                
                width = 1
                if msb and lsb:
                    width = int(msb) - int(lsb) + 1
                
                ports.append({
                    "name": port_name,
                    "direction": direction,
                    "width": width,
                    "msb": int(msb) if msb else None,
                    "lsb": int(lsb) if lsb else None
                })
        
        return {
            "module_name": module_name,
            "ports": ports,
            "port_count": len(ports)
        }
    
    def _validate_port_consistency(self, old_ports: Dict[str, Any], new_ports: Dict[str, Any]) -> bool:
        """验证端口信息一致性"""
        if not old_ports or not new_ports:
            return True
        
        old_port_names = {port["name"] for port in old_ports.get("ports", [])}
        new_port_names = {port["name"] for port in new_ports.get("ports", [])}
        
        return old_port_names == new_port_names
    
    def get_latest_design_file(self, module_name: str = None) -> Optional[FileReference]:
        """获取最新的设计文件"""
        design_files = self.get_files_by_type("verilog")
        
        if not design_files:
            return None
        
        # 按创建时间排序
        design_files.sort(key=lambda x: x.created_at, reverse=True)
        
        if module_name:
            # 查找指定模块的最新版本
            for file_ref in design_files:
                if file_ref.port_info and file_ref.port_info.get("module_name") == module_name:
                    return file_ref
            return None
        
        return design_files[0]
    
    def get_design_port_info(self, module_name: str) -> Optional[Dict[str, Any]]:
        """获取设计文件的端口信息"""
        design_file = self.get_latest_design_file(module_name)
        if design_file:
            return design_file.port_info
        return None
    
    def validate_testbench_ports(self, testbench_content: str, design_module_name: str) -> Dict[str, Any]:
        """验证测试台端口与设计端口的一致性"""
        design_ports = self.get_design_port_info(design_module_name)
        if not design_ports:
            return {"valid": False, "error": f"未找到模块 {design_module_name} 的端口信息"}
        
        # 提取测试台中的模块实例化
        import re
        instance_pattern = rf'{design_module_name}\s+\w+\s*\(([^)]+)\);'
        match = re.search(instance_pattern, testbench_content, re.DOTALL)
        
        if not match:
            return {"valid": False, "error": f"未找到模块 {design_module_name} 的实例化"}
        
        instance_ports = match.group(1)
        port_connections = []
        
        # 解析端口连接
        for line in instance_ports.split(','):
            line = line.strip()
            if not line:
                continue
            
            port_match = re.search(r'\.(\w+)\s*\(\s*(\w+)\s*\)', line)
            if port_match:
                port_name = port_match.group(1)
                signal_name = port_match.group(2)
                port_connections.append({"port": port_name, "signal": signal_name})
        
        # 验证端口连接
        design_port_names = {port["name"] for port in design_ports["ports"]}
        testbench_port_names = {conn["port"] for conn in port_connections}
        
        missing_ports = design_port_names - testbench_port_names
        extra_ports = testbench_port_names - design_port_names
        
        return {
            "valid": len(missing_ports) == 0 and len(extra_ports) == 0,
            "missing_ports": list(missing_ports),
            "extra_ports": list(extra_ports),
            "design_ports": design_ports,
            "testbench_connections": port_connections
        }
    
    def save_file_to_path(self, content: str, filename: str, target_path: Path, 
                         file_type: str, created_by: str, description: str = "") -> FileReference:
        """
        保存文件到指定路径并返回文件引用
        
        Args:
            content: 文件内容
            filename: 文件名
            target_path: 目标保存路径
            file_type: 文件类型 (verilog, testbench, report, etc.)
            created_by: 创建者ID
            description: 文件描述
            
        Returns:
            文件引用对象
        """
        # 确保目标目录存在
        target_path.mkdir(parents=True, exist_ok=True)
        
        # 检查是否已存在同名文件
        existing_file_id = None
        for fid, file_ref in self.file_registry.items():
            if Path(file_ref.file_path).name == filename and file_ref.file_type == file_type:
                existing_file_id = fid
                break
        
        # 如果存在同名文件，使用相同ID；否则生成新ID
        if existing_file_id:
            file_id = existing_file_id
            self.logger.info(f"🔄 使用现有文件ID: {file_id}")
        else:
            file_id = str(uuid.uuid4())[:8]
            self.logger.info(f"🆔 生成新文件ID: {file_id}")
        
        # 生成完整的文件路径
        file_extension = self._get_file_extension(file_type)
        if not filename.endswith(file_extension):
            filename = f"{filename}{file_extension}"
        
        file_path = target_path / filename
        
        # 直接覆盖同名文件，不创建新文件
        if file_path.exists():
            self.logger.info(f"🔄 覆盖现有文件: {filename}")
        
        # 保存文件
        file_path.write_text(content, encoding='utf-8')
        
        # 计算内容哈希
        content_hash = str(hash(content))
        
        # 创建或更新文件引用
        if existing_file_id:
            # 更新现有文件引用
            file_ref = self.file_registry[file_id]
            file_ref.file_path = str(file_path)
            file_ref.content_hash = content_hash
            file_ref.created_by = created_by
            file_ref.created_at = datetime.now().isoformat()
            file_ref.description = description
            self.logger.info(f"🔄 更新现有文件引用: {file_id}")
        else:
            # 创建新文件引用
            file_ref = FileReference(
                file_id=file_id,
                file_path=str(file_path),
                file_type=file_type,
                content_hash=content_hash,
                created_by=created_by,
                created_at=datetime.now().isoformat(),
                description=description
            )
            self.file_registry[file_id] = file_ref
            self.logger.info(f"🆕 创建新文件引用: {file_id}")
        self._save_registry()
        
        self.logger.info(f"💾 文件已保存到指定路径: {file_path} (ID: {file_id}, 类型: {file_type})")
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