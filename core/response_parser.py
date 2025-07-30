#!/usr/bin/env python3
"""
智能体响应解析器

Agent Response Parser for Centralized Agent Framework
"""

import json
import xml.etree.ElementTree as ET
import re
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import logging

from .response_format import (
    StandardizedResponse, ResponseFormat, TaskStatus, ResponseType,
    FileReference, IssueReport, QualityMetrics, ResourceRequest
)

logger = logging.getLogger(__name__)

class ResponseParseError(Exception):
    """响应解析错误"""
    pass

class ResponseParser:
    """智能体响应解析器
    
    负责解析不同格式的智能体响应并提取关键信息
    """
    
    def __init__(self):
        self.supported_formats = [ResponseFormat.JSON, ResponseFormat.XML, ResponseFormat.MARKDOWN]
    
    def parse_response(self, response_content: str, expected_format: ResponseFormat = None) -> StandardizedResponse:
        """解析智能体响应
        
        Args:
            response_content: 响应内容
            expected_format: 期望的格式，如果为None则自动检测
            
        Returns:
            StandardizedResponse: 解析后的标准化响应
            
        Raises:
            ResponseParseError: 解析失败时抛出
        """
        if expected_format:
            return self._parse_by_format(response_content, expected_format)
        
        # 自动检测格式
        detected_format = self._detect_format(response_content)
        if detected_format:
            return self._parse_by_format(response_content, detected_format)
        
        raise ResponseParseError("无法检测响应格式，请指定格式或确保响应符合标准格式")
    
    def _detect_format(self, content: str) -> Optional[ResponseFormat]:
        """自动检测响应格式"""
        content_stripped = content.strip()
        
        # 检测JSON格式
        if content_stripped.startswith('{') and content_stripped.endswith('}'):
            try:
                json.loads(content_stripped)
                return ResponseFormat.JSON
            except json.JSONDecodeError:
                pass
        
        # 检测XML格式
        if content_stripped.startswith('<') and content_stripped.endswith('>'):
            try:
                ET.fromstring(content_stripped)
                return ResponseFormat.XML
            except ET.ParseError:
                pass
        
        # 检测Markdown格式
        if '# Agent Response:' in content or '## 📋 Basic Information' in content:
            return ResponseFormat.MARKDOWN
        
        return None
    
    def _parse_by_format(self, content: str, format_type: ResponseFormat) -> StandardizedResponse:
        """根据指定格式解析响应"""
        if format_type == ResponseFormat.JSON:
            return self._parse_json(content)
        elif format_type == ResponseFormat.XML:
            return self._parse_xml(content)
        elif format_type == ResponseFormat.MARKDOWN:
            return self._parse_markdown(content)
        else:
            raise ResponseParseError(f"不支持的格式类型: {format_type}")
    
    def _parse_json(self, content: str) -> StandardizedResponse:
        """解析JSON格式响应"""
        try:
            data = json.loads(content)
            
            # 解析基本信息
            agent_name = data.get('agent_name', 'Unknown')
            agent_id = data.get('agent_id', 'unknown')
            response_type = ResponseType(data.get('response_type', 'task_completion'))
            task_id = data.get('task_id', 'unknown')
            timestamp = data.get('timestamp', '')
            status = TaskStatus(data.get('status', 'success'))
            completion_percentage = float(data.get('completion_percentage', 0.0))
            message = data.get('message', '')
            
            # 解析文件引用
            generated_files = []
            for file_data in data.get('generated_files', []):
                generated_files.append(FileReference(
                    path=file_data.get('path', ''),
                    file_type=file_data.get('file_type', 'unknown'),
                    description=file_data.get('description', ''),
                    size_bytes=file_data.get('size_bytes'),
                    created_at=file_data.get('created_at')
                ))
            
            modified_files = []
            for file_data in data.get('modified_files', []):
                modified_files.append(FileReference(
                    path=file_data.get('path', ''),
                    file_type=file_data.get('file_type', 'unknown'),
                    description=file_data.get('description', ''),
                    size_bytes=file_data.get('size_bytes'),
                    created_at=file_data.get('created_at')
                ))
            
            reference_files = []
            for file_data in data.get('reference_files', []):
                reference_files.append(FileReference(
                    path=file_data.get('path', ''),
                    file_type=file_data.get('file_type', 'unknown'),
                    description=file_data.get('description', ''),
                    size_bytes=file_data.get('size_bytes'),
                    created_at=file_data.get('created_at')
                ))
            
            # 解析问题报告
            issues = []
            for issue_data in data.get('issues', []):
                issues.append(IssueReport(
                    issue_type=issue_data.get('issue_type', 'unknown'),
                    severity=issue_data.get('severity', 'medium'),
                    description=issue_data.get('description', ''),
                    location=issue_data.get('location'),
                    suggested_solution=issue_data.get('suggested_solution')
                ))
            
            # 解析质量指标
            quality_metrics = None
            if 'quality_metrics' in data:
                qm_data = data['quality_metrics']
                quality_metrics = QualityMetrics(
                    overall_score=float(qm_data.get('overall_score', 0.0)),
                    syntax_score=float(qm_data.get('syntax_score', 0.0)),
                    functionality_score=float(qm_data.get('functionality_score', 0.0)),
                    test_coverage=float(qm_data.get('test_coverage', 0.0)),
                    documentation_quality=float(qm_data.get('documentation_quality', 0.0)),
                    performance_score=qm_data.get('performance_score')
                )
            
            # 解析资源请求
            resource_requests = []
            for req_data in data.get('resource_requests', []):
                resource_requests.append(ResourceRequest(
                    resource_type=req_data.get('resource_type', 'unknown'),
                    description=req_data.get('description', ''),
                    parameters=req_data.get('parameters', {}),
                    priority=req_data.get('priority', 'medium')
                ))
            
            return StandardizedResponse(
                agent_name=agent_name,
                agent_id=agent_id,
                response_type=response_type,
                task_id=task_id,
                timestamp=timestamp,
                status=status,
                completion_percentage=completion_percentage,
                message=message,
                generated_files=generated_files,
                modified_files=modified_files,
                reference_files=reference_files,
                issues=issues,
                quality_metrics=quality_metrics,
                resource_requests=resource_requests,
                next_steps=data.get('next_steps', []),
                metadata=data.get('metadata', {})
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ResponseParseError(f"JSON解析失败: {str(e)}")
    
    def _parse_xml(self, content: str) -> StandardizedResponse:
        """解析XML格式响应"""
        try:
            root = ET.fromstring(content)
            
            # 解析基本信息
            agent_name = self._get_xml_text(root, 'agent_name', 'Unknown')
            agent_id = self._get_xml_text(root, 'agent_id', 'unknown')
            response_type = ResponseType(self._get_xml_text(root, 'response_type', 'task_completion'))
            task_id = self._get_xml_text(root, 'task_id', 'unknown')
            timestamp = self._get_xml_text(root, 'timestamp', '')
            status = TaskStatus(self._get_xml_text(root, 'status', 'success'))
            completion_percentage = float(self._get_xml_text(root, 'completion_percentage', '0.0'))
            message = self._get_xml_text(root, 'message', '')
            
            # 解析文件信息
            generated_files = []
            modified_files = []
            reference_files = []
            
            files_elem = root.find('files')
            if files_elem is not None:
                for file_type, file_list in [
                    ('generated_files', generated_files),
                    ('modified_files', modified_files),
                    ('reference_files', reference_files)
                ]:
                    type_elem = files_elem.find(file_type)
                    if type_elem is not None:
                        for file_elem in type_elem.findall('file'):
                            file_list.append(FileReference(
                                path=self._get_xml_text(file_elem, 'path', ''),
                                file_type=self._get_xml_text(file_elem, 'type', 'unknown'),
                                description=self._get_xml_text(file_elem, 'description', '')
                            ))
            
            # 解析问题报告
            issues = []
            issues_elem = root.find('issues')
            if issues_elem is not None:
                for issue_elem in issues_elem.findall('issue'):
                    issues.append(IssueReport(
                        issue_type=self._get_xml_text(issue_elem, 'type', 'unknown'),
                        severity=self._get_xml_text(issue_elem, 'severity', 'medium'),
                        description=self._get_xml_text(issue_elem, 'description', ''),
                        location=self._get_xml_text(issue_elem, 'location'),
                        suggested_solution=self._get_xml_text(issue_elem, 'suggested_solution')
                    ))
            
            # 解析质量指标
            quality_metrics = None
            quality_elem = root.find('quality_metrics')
            if quality_elem is not None:
                quality_metrics = QualityMetrics(
                    overall_score=float(self._get_xml_text(quality_elem, 'overall_score', '0.0')),
                    syntax_score=float(self._get_xml_text(quality_elem, 'syntax_score', '0.0')),
                    functionality_score=float(self._get_xml_text(quality_elem, 'functionality_score', '0.0')),
                    test_coverage=float(self._get_xml_text(quality_elem, 'test_coverage', '0.0')),
                    documentation_quality=float(self._get_xml_text(quality_elem, 'documentation_quality', '0.0'))
                )
            
            # 解析下一步建议
            next_steps = []
            steps_elem = root.find('next_steps')
            if steps_elem is not None:
                for step_elem in steps_elem.findall('step'):
                    if step_elem.text:
                        next_steps.append(step_elem.text)
            
            return StandardizedResponse(
                agent_name=agent_name,
                agent_id=agent_id,
                response_type=response_type,
                task_id=task_id,
                timestamp=timestamp,
                status=status,
                completion_percentage=completion_percentage,
                message=message,
                generated_files=generated_files,
                modified_files=modified_files,
                reference_files=reference_files,
                issues=issues,
                quality_metrics=quality_metrics,
                resource_requests=[],  # XML解析暂不支持资源请求
                next_steps=next_steps,
                metadata={}
            )
            
        except (ET.ParseError, ValueError) as e:
            raise ResponseParseError(f"XML解析失败: {str(e)}")
    
    def _parse_markdown(self, content: str) -> StandardizedResponse:
        """解析Markdown格式响应"""
        try:
            lines = content.split('\n')
            
            # 初始化解析结果
            agent_name = 'Unknown'
            agent_id = 'unknown'
            task_id = 'unknown'
            response_type = ResponseType.TASK_COMPLETION
            status = TaskStatus.SUCCESS
            completion_percentage = 0.0
            message = ''
            timestamp = ''
            
            generated_files = []
            modified_files = []
            reference_files = []
            issues = []
            next_steps = []
            metadata = {}
            quality_metrics = None
            
            current_section = None
            current_subsection = None
            
            for line in lines:
                line = line.strip()
                
                # 解析标题和基本信息
                if line.startswith('# Agent Response:'):
                    agent_name = line.replace('# Agent Response:', '').strip()
                elif line.startswith('## 📋 Basic Information'):
                    current_section = 'basic_info'
                elif line.startswith('## 💬 Message'):
                    current_section = 'message'
                elif line.startswith('## 📁 Files'):
                    current_section = 'files'
                elif line.startswith('## ⚠️ Issues'):
                    current_section = 'issues'
                elif line.startswith('## 📊 Quality Metrics'):
                    current_section = 'quality'
                elif line.startswith('## 🚀 Next Steps'):
                    current_section = 'next_steps'
                elif line.startswith('## 🔍 Metadata'):
                    current_section = 'metadata'
                
                # 解析子节
                elif line.startswith('### Generated Files'):
                    current_subsection = 'generated_files'
                elif line.startswith('### Modified Files'):
                    current_subsection = 'modified_files'
                elif line.startswith('### Reference Files'):
                    current_subsection = 'reference_files'
                
                # 解析具体内容
                elif current_section == 'basic_info' and line.startswith('- **'):
                    if 'Agent' in line and '`' in line:
                        match = re.search(r'\(`([^`]+)`\)', line)
                        if match:
                            agent_id = match.group(1)
                    elif 'Task ID' in line:
                        match = re.search(r'`([^`]+)`', line)
                        if match:
                            task_id = match.group(1)
                    elif 'Status' in line:
                        status_text = line.split(':')[-1].strip()
                        try:
                            status = TaskStatus(status_text)
                        except ValueError:
                            pass
                    elif 'Progress' in line:
                        match = re.search(r'(\d+\.?\d*)%', line)
                        if match:
                            completion_percentage = float(match.group(1))
                    elif 'Timestamp' in line:
                        timestamp = line.split(':', 1)[-1].strip()
                
                elif current_section == 'message' and line and not line.startswith('#'):
                    if message:
                        message += '\n' + line
                    else:
                        message = line
                
                elif current_section == 'files' and line.startswith('- **') and current_subsection:
                    # 解析文件信息: - **path** (type): description
                    match = re.match(r'- \*\*([^*]+)\*\* \(([^)]+)\): (.+)', line)
                    if match:
                        path, file_type, description = match.groups()
                        file_ref = FileReference(path, file_type, description)
                        
                        if current_subsection == 'generated_files':
                            generated_files.append(file_ref)
                        elif current_subsection == 'modified_files':
                            modified_files.append(file_ref)
                        elif current_subsection == 'reference_files':
                            reference_files.append(file_ref)
                
                elif current_section == 'next_steps' and re.match(r'^\d+\.', line):
                    step_text = re.sub(r'^\d+\.\s*', '', line)
                    next_steps.append(step_text)
                
                elif current_section == 'metadata' and line.startswith('- **'):
                    match = re.match(r'- \*\*([^*]+)\*\*: (.+)', line)
                    if match:
                        key, value = match.groups()
                        metadata[key] = value
            
            return StandardizedResponse(
                agent_name=agent_name,
                agent_id=agent_id,
                response_type=response_type,
                task_id=task_id,
                timestamp=timestamp,
                status=status,
                completion_percentage=completion_percentage,
                message=message,
                generated_files=generated_files,
                modified_files=modified_files,
                reference_files=reference_files,
                issues=issues,
                quality_metrics=quality_metrics,
                resource_requests=[],
                next_steps=next_steps,
                metadata=metadata
            )
            
        except Exception as e:
            raise ResponseParseError(f"Markdown解析失败: {str(e)}")
    
    def _get_xml_text(self, element, tag_name: str, default: str = None) -> str:
        """从XML元素中获取文本"""
        child = element.find(tag_name)
        if child is not None and child.text:
            return child.text
        return default
    
    def extract_key_information(self, response: StandardizedResponse) -> Dict[str, Any]:
        """提取关键信息用于协调者决策"""
        return {
            'agent_name': response.agent_name,
            'task_id': response.task_id,
            'status': response.status.value,
            'completion_percentage': response.completion_percentage,
            'has_errors': len([issue for issue in response.issues if issue.severity in ['critical', 'high']]) > 0,
            'generated_files_count': len(response.generated_files),
            'needs_retry': response.status == TaskStatus.REQUIRES_RETRY,
            'resource_requests': len(response.resource_requests),
            'next_steps_count': len(response.next_steps),
            'quality_score': response.quality_metrics.overall_score if response.quality_metrics else None
        }
    
    def validate_response(self, response: StandardizedResponse) -> List[str]:
        """验证响应的完整性和正确性"""
        validation_errors = []
        
        # 检查必需字段
        if not response.agent_name or response.agent_name == 'Unknown':
            validation_errors.append('agent_name 未正确设置')
        
        if not response.task_id or response.task_id == 'unknown':
            validation_errors.append('task_id 未正确设置')
        
        if not response.message:
            validation_errors.append('message 为空')
        
        # 检查完成百分比合理性
        if response.completion_percentage < 0 or response.completion_percentage > 100:
            validation_errors.append('completion_percentage 超出有效范围 (0-100)')
        
        # 检查状态一致性
        if response.status == TaskStatus.SUCCESS and response.completion_percentage < 100:
            validation_errors.append('状态为SUCCESS但完成度不是100%')
        
        if response.status == TaskStatus.FAILED and response.completion_percentage > 0:
            validation_errors.append('状态为FAILED但完成度大于0%')
        
        # 检查文件路径有效性
        for file_ref in response.generated_files + response.modified_files + response.reference_files:
            if not file_ref.path:
                validation_errors.append(f'文件路径为空: {file_ref.description}')
        
        return validation_errors

# 全局解析器实例
response_parser = ResponseParser()

def parse_agent_response(content: str, format_type: ResponseFormat = None) -> StandardizedResponse:
    """解析智能体响应的便捷函数"""
    return response_parser.parse_response(content, format_type)

def validate_agent_response(response: StandardizedResponse) -> List[str]:
    """验证智能体响应的便捷函数"""
    return response_parser.validate_response(response)