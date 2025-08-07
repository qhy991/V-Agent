"""
统一任务文件上下文管理系统

解决智能体间文件内容传递和上下文丢失问题
"""

import json
import hashlib
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from enum import Enum
import time

class FileType(Enum):
    """文件类型枚举"""
    VERILOG = "verilog"
    SYSTEMVERILOG = "systemverilog"
    TESTBENCH = "testbench"
    CONSTRAINT = "constraint"
    OTHER = "other"

@dataclass
class FileContent:
    """单个文件内容数据类"""
    file_path: str
    content: str
    file_type: FileType
    checksum: str
    timestamp: float
    metadata: Dict[str, Any]
    
    @classmethod
    def from_file(cls, file_path: str, content: str = None, file_type: FileType = None, **metadata):
        """从文件路径创建FileContent实例"""
        if content is None:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                raise ValueError(f"无法读取文件 {file_path}: {e}")
        
        # 自动检测文件类型
        if file_type is None:
            file_type = cls._detect_file_type(file_path, content)
        
        # 计算校验和
        checksum = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        return cls(
            file_path=file_path,
            content=content,
            file_type=file_type,
            checksum=checksum,
            timestamp=time.time(),
            metadata=metadata
        )
    
    @staticmethod
    def _detect_file_type(file_path: str, content: str) -> FileType:
        """自动检测文件类型"""
        file_path_lower = file_path.lower()
        
        if file_path_lower.endswith('.v'):
            # 检查是否是测试台
            if 'testbench' in content.lower() or 'tb_' in file_path_lower or '_tb' in file_path_lower:
                return FileType.TESTBENCH
            return FileType.VERILOG
        elif file_path_lower.endswith('.sv'):
            if 'testbench' in content.lower() or 'tb_' in file_path_lower or '_tb' in file_path_lower:
                return FileType.TESTBENCH
            return FileType.SYSTEMVERILOG
        elif file_path_lower.endswith(('.xdc', '.sdc', '.ucf')):
            return FileType.CONSTRAINT
        else:
            return FileType.OTHER
    
    def validate_content(self) -> bool:
        """验证内容完整性"""
        current_checksum = hashlib.md5(self.content.encode('utf-8')).hexdigest()
        return current_checksum == self.checksum
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['file_type'] = self.file_type.value
        return result

class TaskFileContext:
    """任务文件上下文管理器"""
    
    def __init__(self, task_id: str = None):
        self.task_id = task_id or f"task_{int(time.time())}"
        self.files: Dict[str, FileContent] = {}
        self.primary_design_file: Optional[str] = None
        self.primary_testbench_file: Optional[str] = None
        self.logger = logging.getLogger(f"{__name__}.{self.task_id}")
        self._creation_time = time.time()
        self._last_access_time = time.time()
        
    def add_file(self, file_path: str, content: str = None, file_type: FileType = None, 
                 is_primary_design: bool = False, is_primary_testbench: bool = False, **metadata) -> FileContent:
        """添加文件到上下文"""
        file_content = FileContent.from_file(file_path, content, file_type, **metadata)
        
        # 标准化文件路径
        normalized_path = str(Path(file_path).resolve())
        self.files[normalized_path] = file_content
        
        # 设置主要文件
        if is_primary_design or (file_content.file_type == FileType.VERILOG and not self.primary_design_file):
            self.primary_design_file = normalized_path
            self.logger.info(f"🎯 设置主要设计文件: {normalized_path}")
        
        if is_primary_testbench or (file_content.file_type == FileType.TESTBENCH and not self.primary_testbench_file):
            self.primary_testbench_file = normalized_path
            self.logger.info(f"🧪 设置主要测试台文件: {normalized_path}")
        
        self._last_access_time = time.time()
        self.logger.info(f"📁 添加文件到上下文: {file_path} ({file_content.file_type.value}, {len(content or '')} 字符)")
        
        return file_content
    
    def get_file(self, file_path: str) -> Optional[FileContent]:
        """获取文件内容"""
        normalized_path = str(Path(file_path).resolve())
        file_content = self.files.get(normalized_path)
        
        if file_content:
            self._last_access_time = time.time()
            # 验证内容完整性
            if not file_content.validate_content():
                self.logger.warning(f"⚠️ 文件内容校验失败: {file_path}")
        
        return file_content
    
    def get_primary_design_content(self) -> Optional[str]:
        """获取主要设计文件内容"""
        if not self.primary_design_file:
            self.logger.warning("⚠️ 没有设置主要设计文件")
            return None
        
        file_content = self.get_file(self.primary_design_file)
        return file_content.content if file_content else None
    
    def get_primary_testbench_content(self) -> Optional[str]:
        """获取主要测试台文件内容"""
        if not self.primary_testbench_file:
            self.logger.warning("⚠️ 没有设置主要测试台文件")
            return None
        
        file_content = self.get_file(self.primary_testbench_file)
        return file_content.content if file_content else None
    
    def get_files_by_type(self, file_type: FileType) -> List[FileContent]:
        """按类型获取文件列表"""
        return [fc for fc in self.files.values() if fc.file_type == file_type]
    
    def get_verilog_files(self) -> List[FileContent]:
        """获取所有Verilog文件"""
        return self.get_files_by_type(FileType.VERILOG) + self.get_files_by_type(FileType.SYSTEMVERILOG)
    
    def get_testbench_files(self) -> List[FileContent]:
        """获取所有测试台文件"""
        return self.get_files_by_type(FileType.TESTBENCH)
    
    def validate_all_files(self) -> Dict[str, bool]:
        """验证所有文件的完整性"""
        validation_results = {}
        for file_path, file_content in self.files.items():
            validation_results[file_path] = file_content.validate_content()
        return validation_results
    
    def get_context_summary(self) -> Dict[str, Any]:
        """获取上下文摘要"""
        file_summary = {}
        for file_path, file_content in self.files.items():
            file_summary[file_path] = {
                'type': file_content.file_type.value,
                'size': len(file_content.content),
                'checksum': file_content.checksum,
                'timestamp': file_content.timestamp
            }
        
        return {
            'task_id': self.task_id,
            'total_files': len(self.files),
            'primary_design_file': self.primary_design_file,
            'primary_testbench_file': self.primary_testbench_file,
            'files': file_summary,
            'creation_time': self._creation_time,
            'last_access_time': self._last_access_time
        }
    
    def export_for_agent(self, include_content: bool = True) -> Dict[str, Any]:
        """导出给智能体使用的格式"""
        exported_data = {
            'task_id': self.task_id,
            'primary_design_file': self.primary_design_file,
            'primary_testbench_file': self.primary_testbench_file,
            'files': {}
        }
        
        for file_path, file_content in self.files.items():
            file_data = {
                'file_path': file_path,
                'file_type': file_content.file_type.value,
                'checksum': file_content.checksum,
                'timestamp': file_content.timestamp,
                'metadata': file_content.metadata
            }
            
            if include_content:
                file_data['content'] = file_content.content
                
            exported_data['files'][file_path] = file_data
        
        return exported_data
    
    def merge_context(self, other_context: 'TaskFileContext', override: bool = False):
        """合并另一个上下文"""
        for file_path, file_content in other_context.files.items():
            if file_path not in self.files or override:
                self.files[file_path] = file_content
                self.logger.info(f"📄 合并文件: {file_path}")
            else:
                self.logger.warning(f"⚠️ 文件已存在，跳过合并: {file_path}")
        
        # 合并主要文件设置
        if other_context.primary_design_file and (not self.primary_design_file or override):
            self.primary_design_file = other_context.primary_design_file
        
        if other_context.primary_testbench_file and (not self.primary_testbench_file or override):
            self.primary_testbench_file = other_context.primary_testbench_file
    
    def to_json(self) -> str:
        """序列化为JSON"""
        data = {
            'task_id': self.task_id,
            'primary_design_file': self.primary_design_file,
            'primary_testbench_file': self.primary_testbench_file,
            'creation_time': self._creation_time,
            'last_access_time': self._last_access_time,
            'files': [file_content.to_dict() for file_content in self.files.values()]
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TaskFileContext':
        """从JSON反序列化"""
        data = json.loads(json_str)
        context = cls(data['task_id'])
        context.primary_design_file = data.get('primary_design_file')
        context.primary_testbench_file = data.get('primary_testbench_file')
        context._creation_time = data.get('creation_time', time.time())
        context._last_access_time = data.get('last_access_time', time.time())
        
        for file_data in data.get('files', []):
            file_content = FileContent(
                file_path=file_data['file_path'],
                content=file_data['content'],
                file_type=FileType(file_data['file_type']),
                checksum=file_data['checksum'],
                timestamp=file_data['timestamp'],
                metadata=file_data.get('metadata', {})
            )
            normalized_path = str(Path(file_data['file_path']).resolve())
            context.files[normalized_path] = file_content
        
        return context
    
    def __len__(self):
        return len(self.files)
    
    def __str__(self):
        return f"TaskFileContext(task_id={self.task_id}, files={len(self.files)}, primary_design={self.primary_design_file})"
    
    def __repr__(self):
        return self.__str__()


# 全局上下文管理器
_global_context_store: Dict[str, TaskFileContext] = {}

def get_task_context(task_id: str) -> Optional[TaskFileContext]:
    """获取任务上下文"""
    return _global_context_store.get(task_id)

def set_task_context(task_id: str, context: TaskFileContext):
    """设置任务上下文"""
    _global_context_store[task_id] = context

def clear_task_context(task_id: str):
    """清除任务上下文"""
    if task_id in _global_context_store:
        del _global_context_store[task_id]

def clear_all_contexts():
    """清除所有上下文"""
    _global_context_store.clear()

def list_active_contexts() -> List[str]:
    """列出所有活跃上下文的ID"""
    return list(_global_context_store.keys())