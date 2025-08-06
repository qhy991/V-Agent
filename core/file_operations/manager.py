#!/usr/bin/env python3
"""
File Operation Manager - 文件操作管理器
=====================================

从BaseAgent中提取的文件操作功能，负责文件读写、内容清理和验证。
"""

import os
import re
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

from ..types import FileReference


@dataclass
class FileOperationConfig:
    """文件操作配置"""
    default_artifacts_dir: str = "./output"
    enable_cache: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: List[str] = None
    backup_enabled: bool = True
    encoding: str = "utf-8"


class FileOperationManager:
    """文件操作管理器"""
    
    def __init__(self, config: FileOperationConfig = None, logger: Optional[logging.Logger] = None):
        self.config = config or FileOperationConfig()
        self.logger = logger or logging.getLogger(__name__)
        
        # 文件缓存
        self.file_cache: Dict[str, str] = {}
        self.file_metadata_cache: Dict[str, Dict] = {}
        
        # 操作统计
        self.operation_stats = {
            'total_reads': 0,
            'total_writes': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0
        }
        
        # 初始化默认目录
        self._ensure_default_directories()
    
    def _ensure_default_directories(self):
        """确保默认目录存在"""
        try:
            Path(self.config.default_artifacts_dir).mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"确保目录存在: {self.config.default_artifacts_dir}")
        except Exception as e:
            self.logger.warning(f"创建默认目录失败: {e}")
    
    async def read_file(self, file_path: str, use_cache: bool = True) -> Optional[str]:
        """读取文件内容"""
        try:
            # 检查缓存
            if use_cache and self.config.enable_cache and file_path in self.file_cache:
                self.operation_stats['cache_hits'] += 1
                self.logger.debug(f"📋 使用缓存文件: {file_path}")
                return self.file_cache[file_path]
            
            self.operation_stats['cache_misses'] += 1
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.logger.warning(f"⚠️ 文件不存在: {file_path}")
                return None
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size > self.config.max_file_size:
                self.logger.warning(f"⚠️ 文件过大: {file_path} ({file_size} bytes)")
                return None
            
            # 读取文件
            with open(file_path, 'r', encoding=self.config.encoding) as f:
                content = f.read()
            
            # 缓存内容
            if self.config.enable_cache:
                self.file_cache[file_path] = content
                self.file_metadata_cache[file_path] = {
                    "size": len(content),
                    "read_time": time.time(),
                    "file_size": file_size
                }
            
            self.operation_stats['total_reads'] += 1
            self.logger.info(f"✅ 成功读取文件: {file_path} ({len(content)} bytes)")
            return content
            
        except Exception as e:
            self.operation_stats['errors'] += 1
            self.logger.error(f"❌ 读取文件失败 {file_path}: {str(e)}")
            return None
    
    async def write_file(self, content: str, file_path: str = None, 
                        filename: str = None, directory: str = None, 
                        file_type: str = "text", backup: bool = None) -> Optional[FileReference]:
        """写入文件内容"""
        try:
            # 确定文件路径
            if file_path:
                target_path = Path(file_path)
            else:
                if not filename:
                    self.logger.error("❌ 必须提供filename或file_path")
                    return None
                
                dir_path = Path(directory) if directory else Path(self.config.default_artifacts_dir)
                target_path = dir_path / filename
            
            # 确保目录存在
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 备份现有文件
            if (backup or self.config.backup_enabled) and target_path.exists():
                backup_path = target_path.with_suffix(f"{target_path.suffix}.backup")
                target_path.rename(backup_path)
                self.logger.info(f"📦 备份文件: {backup_path}")
            
            # 清理内容
            cleaned_content = self.clean_file_content(content, file_type)
            
            # 写入文件
            with open(target_path, 'w', encoding=self.config.encoding) as f:
                f.write(cleaned_content)
            
            # 更新缓存
            if self.config.enable_cache:
                self.file_cache[str(target_path)] = cleaned_content
                self.file_metadata_cache[str(target_path)] = {
                    "size": len(cleaned_content),
                    "write_time": time.time(),
                    "file_type": file_type
                }
            
            # 创建文件引用
            file_ref = FileReference(
                file_path=str(target_path),
                file_type=file_type,
                description=f"写入的{file_type}文件",
                metadata={
                    "size": len(cleaned_content),
                    "creation_time": time.time(),
                    "file_type": file_type
                }
            )
            
            self.operation_stats['total_writes'] += 1
            self.logger.info(f"💾 成功写入文件: {target_path}")
            return file_ref
            
        except Exception as e:
            self.operation_stats['errors'] += 1
            self.logger.error(f"❌ 写入文件失败 {file_path or filename}: {str(e)}")
            return None
    
    def clean_file_content(self, content: str, file_type: str) -> str:
        """清理文件内容"""
        if not content:
            return ""
        
        cleaned_content = content.strip()
        
        # 根据文件类型进行特定清理
        if file_type in ["verilog", "systemverilog"]:
            return self._clean_verilog_content(cleaned_content)
        elif file_type in ["testbench", "tb"]:
            return self._clean_testbench_content(cleaned_content)
        elif file_type == "json":
            return self._clean_json_content(cleaned_content)
        else:
            return self._clean_general_content(cleaned_content)
    
    def _clean_verilog_content(self, content: str) -> str:
        """清理Verilog内容"""
        # 提取Verilog代码
        extracted_code = self.extract_verilog_code(content)
        
        if extracted_code and len(extracted_code.strip()) > 0:
            # 检查是否包含Verilog关键字
            verilog_keywords = ['module', 'endmodule', 'input', 'output', 'wire', 'reg', 'always', 'assign']
            if any(keyword in extracted_code.lower() for keyword in verilog_keywords):
                self.logger.info(f"🧹 使用提取的Verilog代码")
                return extracted_code
        
        # 如果提取失败，使用传统清理
        return self._traditional_clean_content(content)
    
    def _clean_testbench_content(self, content: str) -> str:
        """清理测试台内容"""
        # 移除markdown格式
        content = re.sub(r'```(?:verilog|systemverilog)?\s*\n', '', content)
        content = re.sub(r'\n```\s*$', '', content)
        
        # 移除代码块标记
        content = re.sub(r'^```.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'```$', '', content)
        
        return content.strip()
    
    def _clean_json_content(self, content: str) -> str:
        """清理JSON内容"""
        # 移除markdown代码块
        content = re.sub(r'```json\s*\n', '', content)
        content = re.sub(r'\n```\s*$', '', content)
        
        # 尝试解析JSON以验证格式
        try:
            import json
            json.loads(content)
            return content.strip()
        except json.JSONDecodeError:
            self.logger.warning("JSON格式无效，尝试修复...")
            return content.strip()
    
    def _clean_general_content(self, content: str) -> str:
        """清理通用内容"""
        return self._traditional_clean_content(content)
    
    def _traditional_clean_content(self, content: str) -> str:
        """传统内容清理方法"""
        # 移除markdown格式标记
        content = re.sub(r'```(?:[a-zA-Z]+)?\s*\n', '', content)
        content = re.sub(r'\n```\s*$', '', content)
        
        # 移除代码块标记
        content = re.sub(r'^```.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'```$', '', content)
        
        # 移除多余的空白行
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        return content.strip()
    
    def extract_verilog_code(self, content: str) -> str:
        """提取Verilog代码"""
        if not content:
            return ""
        
        # 方法1: 查找module...endmodule结构
        module_pattern = r'(module\s+\w+.*?endmodule)'
        matches = re.findall(module_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if matches:
            self.logger.debug(f"🔍 找到 {len(matches)} 个Verilog模块")
            return '\n\n'.join(matches)
        
        # 方法2: 查找代码块
        code_block_pattern = r'```(?:verilog|systemverilog)?\s*\n(.*?)\n```'
        matches = re.findall(code_block_pattern, content, re.DOTALL)
        
        if matches:
            self.logger.debug(f"🔍 找到 {len(matches)} 个代码块")
            return '\n\n'.join(matches)
        
        # 方法3: 查找包含Verilog关键字的内容
        verilog_keywords = ['module', 'endmodule', 'input', 'output', 'wire', 'reg', 'always', 'assign']
        lines = content.split('\n')
        verilog_lines = []
        in_verilog_block = False
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in verilog_keywords):
                in_verilog_block = True
            
            if in_verilog_block:
                verilog_lines.append(line)
            
            if 'endmodule' in line_lower:
                in_verilog_block = False
        
        if verilog_lines:
            self.logger.debug(f"🔍 提取到 {len(verilog_lines)} 行Verilog代码")
            return '\n'.join(verilog_lines)
        
        return content
    
    def is_valid_verilog_code(self, code: str) -> bool:
        """验证Verilog代码"""
        if not code or not code.strip():
            return False
        
        # 基本检查
        code_lower = code.lower()
        
        # 检查是否包含基本Verilog结构
        has_module = 'module' in code_lower
        has_endmodule = 'endmodule' in code_lower
        
        if not has_module or not has_endmodule:
            return False
        
        # 检查模块名格式
        module_match = re.search(r'module\s+(\w+)', code, re.IGNORECASE)
        if not module_match:
            return False
        
        module_name = module_match.group(1)
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', module_name):
            return False
        
        # 检查基本语法
        verilog_keywords = ['input', 'output', 'wire', 'reg', 'always', 'assign', 'begin', 'end']
        has_keywords = any(keyword in code_lower for keyword in verilog_keywords)
        
        if not has_keywords:
            return False
        
        # 检查括号匹配
        open_parens = code.count('(')
        close_parens = code.count(')')
        if open_parens != close_parens:
            return False
        
        return True
    
    def detect_file_type(self, file_path: str) -> str:
        """检测文件类型"""
        if not file_path:
            return "unknown"
        
        # 根据扩展名判断
        ext = Path(file_path).suffix.lower()
        
        type_mapping = {
            '.v': 'verilog',
            '.sv': 'systemverilog',
            '.tb': 'testbench',
            '.json': 'json',
            '.txt': 'text',
            '.md': 'markdown',
            '.py': 'python',
            '.sh': 'shell',
            '.tcl': 'tcl'
        }
        
        return type_mapping.get(ext, "unknown")
    
    def determine_file_type(self, filename: str, content: str) -> str:
        """根据文件名和内容确定文件类型"""
        # 首先根据文件名判断
        file_type = self.detect_file_type(filename)
        
        if file_type != "unknown":
            return file_type
        
        # 根据内容判断
        content_lower = content.lower()
        
        if 'module' in content_lower and 'endmodule' in content_lower:
            return 'verilog'
        elif 'testbench' in content_lower or 'tb' in content_lower:
            return 'testbench'
        elif content.strip().startswith('{') and content.strip().endswith('}'):
            return 'json'
        elif '```' in content:
            return 'markdown'
        
        return 'text'
    
    def clear_cache(self, file_path: str = None):
        """清除缓存"""
        if file_path:
            self.file_cache.pop(file_path, None)
            self.file_metadata_cache.pop(file_path, None)
            self.logger.debug(f"清除文件缓存: {file_path}")
        else:
            self.file_cache.clear()
            self.file_metadata_cache.clear()
            self.logger.debug("清除所有文件缓存")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return {
            'cache_size': len(self.file_cache),
            'metadata_size': len(self.file_metadata_cache),
            'total_size': sum(len(content) for content in self.file_cache.values()),
            'cache_hits': self.operation_stats['cache_hits'],
            'cache_misses': self.operation_stats['cache_misses']
        }
    
    def get_operation_stats(self) -> Dict[str, Any]:
        """获取操作统计"""
        stats = self.operation_stats.copy()
        
        # 计算缓存命中率
        total_cache_access = stats['cache_hits'] + stats['cache_misses']
        if total_cache_access > 0:
            stats['cache_hit_rate'] = stats['cache_hits'] / total_cache_access
        else:
            stats['cache_hit_rate'] = 0.0
        
        return stats
    
    def clear_stats(self):
        """清除统计"""
        self.operation_stats = {
            'total_reads': 0,
            'total_writes': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0
        }
    
    def list_files(self, directory: str = None, pattern: str = "*") -> List[str]:
        """列出文件"""
        try:
            dir_path = Path(directory) if directory else Path(self.config.default_artifacts_dir)
            files = list(dir_path.glob(pattern))
            return [str(f) for f in files if f.is_file()]
        except Exception as e:
            self.logger.error(f"列出文件失败: {e}")
            return []
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """获取文件信息"""
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            stat = path.stat()
            return {
                'path': str(path),
                'size': stat.st_size,
                'modified_time': stat.st_mtime,
                'created_time': stat.st_ctime,
                'file_type': self.detect_file_type(str(path)),
                'in_cache': str(path) in self.file_cache
            }
        except Exception as e:
            self.logger.error(f"获取文件信息失败: {e}")
            return None 