#!/usr/bin/env python3
"""
标准化智能体响应格式

Standardized Agent Response Format for Centralized Agent Framework
"""

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum

class ResponseFormat(Enum):
    """响应格式类型"""
    JSON = "json"
    XML = "xml"
    MARKDOWN = "markdown"

class TaskStatus(Enum):
    """任务状态"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    REQUIRES_RETRY = "requires_retry"

class ResponseType(Enum):
    """响应类型"""
    TASK_COMPLETION = "task_completion"
    PROGRESS_UPDATE = "progress_update"
    ERROR_REPORT = "error_report"
    RESOURCE_REQUEST = "resource_request"
    QUALITY_REPORT = "quality_report"

@dataclass
class FileReference:
    """文件引用信息"""
    path: str
    file_type: str  # verilog, testbench, documentation, etc.
    description: str
    size_bytes: Optional[int] = None
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class IssueReport:
    """问题报告"""
    issue_type: str  # error, warning, suggestion
    severity: str   # critical, high, medium, low
    description: str
    location: Optional[str] = None  # 文件路径或代码位置
    suggested_solution: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class QualityMetrics:
    """质量指标"""
    overall_score: float  # 0.0-1.0
    syntax_score: float
    functionality_score: float
    test_coverage: float
    documentation_quality: float
    performance_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ResourceRequest:
    """资源请求"""
    resource_type: str  # database_query, file_access, tool_call, etc.
    description: str
    parameters: Dict[str, Any]
    priority: str = "medium"  # low, medium, high, urgent
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class StandardizedResponse:
    """标准化智能体响应"""
    # 基本信息
    agent_name: str
    agent_id: str
    response_type: ResponseType
    task_id: str
    timestamp: str
    
    # 任务状态
    status: TaskStatus
    completion_percentage: float  # 0.0-100.0
    
    # 主要内容
    message: str  # 主要响应消息
    
    # 文件信息
    generated_files: List[FileReference]
    modified_files: List[FileReference]
    reference_files: List[FileReference]
    
    # 问题和错误
    issues: List[IssueReport]
    
    # 质量指标（可选）
    quality_metrics: Optional[QualityMetrics] = None
    
    # 资源请求（可选）
    resource_requests: List[ResourceRequest] = None
    
    # 下一步建议
    next_steps: List[str] = None
    
    # 额外数据
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """后初始化处理"""
        if self.resource_requests is None:
            self.resource_requests = []
        if self.next_steps is None:
            self.next_steps = []
        if self.metadata is None:
            self.metadata = {}
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "response_type": self.response_type.value,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "status": self.status.value,
            "completion_percentage": self.completion_percentage,
            "message": self.message,
            "generated_files": [f.to_dict() for f in self.generated_files],
            "modified_files": [f.to_dict() for f in self.modified_files],
            "reference_files": [f.to_dict() for f in self.reference_files],
            "issues": [i.to_dict() for i in self.issues],
            "resource_requests": [r.to_dict() for r in self.resource_requests],
            "next_steps": self.next_steps,
            "metadata": self.metadata
        }
        
        if self.quality_metrics:
            data["quality_metrics"] = self.quality_metrics.to_dict()
        
        return data
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON格式"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def to_xml(self) -> str:
        """转换为XML格式"""
        root = ET.Element("agent_response")
        
        # 基本信息
        ET.SubElement(root, "agent_name").text = self.agent_name
        ET.SubElement(root, "agent_id").text = self.agent_id
        ET.SubElement(root, "response_type").text = self.response_type.value
        ET.SubElement(root, "task_id").text = self.task_id
        ET.SubElement(root, "timestamp").text = self.timestamp
        ET.SubElement(root, "status").text = self.status.value
        ET.SubElement(root, "completion_percentage").text = str(self.completion_percentage)
        ET.SubElement(root, "message").text = self.message
        
        # 文件信息
        files_elem = ET.SubElement(root, "files")
        
        for file_list, list_name in [
            (self.generated_files, "generated"),
            (self.modified_files, "modified"),
            (self.reference_files, "reference")
        ]:
            if file_list:
                list_elem = ET.SubElement(files_elem, f"{list_name}_files")
                for file_ref in file_list:
                    file_elem = ET.SubElement(list_elem, "file")
                    ET.SubElement(file_elem, "path").text = file_ref.path
                    ET.SubElement(file_elem, "type").text = file_ref.file_type
                    ET.SubElement(file_elem, "description").text = file_ref.description
        
        # 问题报告
        if self.issues:
            issues_elem = ET.SubElement(root, "issues")
            for issue in self.issues:
                issue_elem = ET.SubElement(issues_elem, "issue")
                ET.SubElement(issue_elem, "type").text = issue.issue_type
                ET.SubElement(issue_elem, "severity").text = issue.severity
                ET.SubElement(issue_elem, "description").text = issue.description
                if issue.location:
                    ET.SubElement(issue_elem, "location").text = issue.location
                if issue.suggested_solution:
                    ET.SubElement(issue_elem, "suggested_solution").text = issue.suggested_solution
        
        # 质量指标
        if self.quality_metrics:
            quality_elem = ET.SubElement(root, "quality_metrics")
            ET.SubElement(quality_elem, "overall_score").text = str(self.quality_metrics.overall_score)
            ET.SubElement(quality_elem, "syntax_score").text = str(self.quality_metrics.syntax_score)
            ET.SubElement(quality_elem, "functionality_score").text = str(self.quality_metrics.functionality_score)
            ET.SubElement(quality_elem, "test_coverage").text = str(self.quality_metrics.test_coverage)
            ET.SubElement(quality_elem, "documentation_quality").text = str(self.quality_metrics.documentation_quality)
        
        # 下一步建议
        if self.next_steps:
            steps_elem = ET.SubElement(root, "next_steps")
            for step in self.next_steps:
                ET.SubElement(steps_elem, "step").text = step
        
        return ET.tostring(root, encoding='unicode')
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        md_content = []
        
        # 标题
        md_content.append(f"# Agent Response: {self.agent_name}")
        md_content.append("")
        
        # 基本信息
        md_content.append("## 📋 Basic Information")
        md_content.append(f"- **Agent**: {self.agent_name} (`{self.agent_id}`)")
        md_content.append(f"- **Task ID**: `{self.task_id}`")
        md_content.append(f"- **Response Type**: {self.response_type.value}")
        md_content.append(f"- **Status**: {self.status.value}")
        md_content.append(f"- **Progress**: {self.completion_percentage:.1f}%")
        md_content.append(f"- **Timestamp**: {self.timestamp}")
        md_content.append("")
        
        # 主要消息
        md_content.append("## 💬 Message")
        md_content.append(self.message)
        md_content.append("")
        
        # 文件信息
        if self.generated_files or self.modified_files or self.reference_files:
            md_content.append("## 📁 Files")
            
            if self.generated_files:
                md_content.append("### Generated Files")
                for file_ref in self.generated_files:
                    md_content.append(f"- **{file_ref.path}** ({file_ref.file_type}): {file_ref.description}")
                md_content.append("")
            
            if self.modified_files:
                md_content.append("### Modified Files")
                for file_ref in self.modified_files:
                    md_content.append(f"- **{file_ref.path}** ({file_ref.file_type}): {file_ref.description}")
                md_content.append("")
            
            if self.reference_files:
                md_content.append("### Reference Files")
                for file_ref in self.reference_files:
                    md_content.append(f"- **{file_ref.path}** ({file_ref.file_type}): {file_ref.description}")
                md_content.append("")
        
        # 问题报告
        if self.issues:
            md_content.append("## ⚠️ Issues")
            for issue in self.issues:
                severity_icon = {
                    "critical": "🔴",
                    "high": "🟠", 
                    "medium": "🟡",
                    "low": "🟢"
                }.get(issue.severity, "⚪")
                
                md_content.append(f"### {severity_icon} {issue.issue_type.title()} - {issue.severity.title()}")
                md_content.append(f"**Description**: {issue.description}")
                if issue.location:
                    md_content.append(f"**Location**: `{issue.location}`")
                if issue.suggested_solution:
                    md_content.append(f"**Suggested Solution**: {issue.suggested_solution}")
                md_content.append("")
        
        # 质量指标
        if self.quality_metrics:
            md_content.append("## 📊 Quality Metrics")
            metrics = self.quality_metrics
            md_content.append(f"- **Overall Score**: {metrics.overall_score:.2f}")
            md_content.append(f"- **Syntax Score**: {metrics.syntax_score:.2f}")
            md_content.append(f"- **Functionality Score**: {metrics.functionality_score:.2f}")
            md_content.append(f"- **Test Coverage**: {metrics.test_coverage:.2f}")
            md_content.append(f"- **Documentation Quality**: {metrics.documentation_quality:.2f}")
            if metrics.performance_score is not None:
                md_content.append(f"- **Performance Score**: {metrics.performance_score:.2f}")
            md_content.append("")
        
        # 资源请求
        if self.resource_requests:
            md_content.append("## 🔧 Resource Requests")
            for req in self.resource_requests:
                priority_icon = {
                    "urgent": "🔴",
                    "high": "🟠",
                    "medium": "🟡", 
                    "low": "🟢"
                }.get(req.priority, "⚪")
                
                md_content.append(f"### {priority_icon} {req.resource_type} - {req.priority}")
                md_content.append(f"**Description**: {req.description}")
                if req.parameters:
                    md_content.append("**Parameters**:")
                    for key, value in req.parameters.items():
                        md_content.append(f"  - `{key}`: {value}")
                md_content.append("")
        
        # 下一步建议
        if self.next_steps:
            md_content.append("## 🚀 Next Steps")
            for i, step in enumerate(self.next_steps, 1):
                md_content.append(f"{i}. {step}")
            md_content.append("")
        
        # 元数据
        if self.metadata:
            md_content.append("## 🔍 Metadata")
            for key, value in self.metadata.items():
                md_content.append(f"- **{key}**: {value}")
        
        return "\n".join(md_content)
    
    def format_response(self, format_type: ResponseFormat = ResponseFormat.JSON) -> str:
        """格式化响应"""
        if format_type == ResponseFormat.JSON:
            return self.to_json()
        elif format_type == ResponseFormat.XML:
            return self.to_xml()
        elif format_type == ResponseFormat.MARKDOWN:
            return self.to_markdown()
        else:
            raise ValueError(f"Unsupported format type: {format_type}")

class ResponseBuilder:
    """响应构建器"""
    
    def __init__(self, agent_name: str, agent_id: str, task_id: str):
        self.agent_name = agent_name
        self.agent_id = agent_id
        self.task_id = task_id
        self.generated_files = []
        self.modified_files = []
        self.reference_files = []
        self.issues = []
        self.resource_requests = []
        self.next_steps = []
        self.metadata = {}
    
    def add_generated_file(self, path: str, file_type: str, description: str) -> 'ResponseBuilder':
        """添加生成的文件"""
        self.generated_files.append(FileReference(path, file_type, description))
        return self
    
    def add_modified_file(self, path: str, file_type: str, description: str) -> 'ResponseBuilder':
        """添加修改的文件"""
        self.modified_files.append(FileReference(path, file_type, description))
        return self
    
    def add_reference_file(self, path: str, file_type: str, description: str) -> 'ResponseBuilder':
        """添加参考文件"""
        self.reference_files.append(FileReference(path, file_type, description))
        return self
    
    def add_issue(self, issue_type: str, severity: str, description: str, 
                  location: str = None, solution: str = None) -> 'ResponseBuilder':
        """添加问题报告"""
        self.issues.append(IssueReport(
            issue_type=issue_type,
            severity=severity,
            description=description,
            location=location,
            suggested_solution=solution
        ))
        return self
    
    def add_resource_request(self, resource_type: str, description: str, 
                           parameters: Dict[str, Any], priority: str = "medium") -> 'ResponseBuilder':
        """添加资源请求"""
        self.resource_requests.append(ResourceRequest(
            resource_type=resource_type,
            description=description,
            parameters=parameters,
            priority=priority
        ))
        return self
    
    def add_next_step(self, step: str) -> 'ResponseBuilder':
        """添加下一步建议"""
        self.next_steps.append(step)
        return self
    
    def add_metadata(self, key: str, value: Any) -> 'ResponseBuilder':
        """添加元数据"""
        self.metadata[key] = value
        return self
    
    def build(self, response_type: ResponseType, status: TaskStatus, 
              message: str, completion_percentage: float, 
              quality_metrics: QualityMetrics = None) -> StandardizedResponse:
        """构建标准化响应"""
        return StandardizedResponse(
            agent_name=self.agent_name,
            agent_id=self.agent_id,
            response_type=response_type,
            task_id=self.task_id,
            timestamp=datetime.now().isoformat(),
            status=status,
            completion_percentage=completion_percentage,
            message=message,
            generated_files=self.generated_files,
            modified_files=self.modified_files,
            reference_files=self.reference_files,
            issues=self.issues,
            quality_metrics=quality_metrics,
            resource_requests=self.resource_requests,
            next_steps=self.next_steps,
            metadata=self.metadata
        )

def create_success_response(agent_name: str, agent_id: str, task_id: str, 
                          message: str, generated_files: List[str] = None) -> StandardizedResponse:
    """创建成功响应的快捷方法"""
    builder = ResponseBuilder(agent_name, agent_id, task_id)
    
    if generated_files:
        for file_path in generated_files:
            file_type = "verilog" if file_path.endswith(".v") else "testbench" if file_path.endswith("_tb.v") else "other"
            builder.add_generated_file(file_path, file_type, f"Generated {file_type} file")
    
    return builder.build(
        response_type=ResponseType.TASK_COMPLETION,
        status=TaskStatus.SUCCESS,
        message=message,
        completion_percentage=100.0
    )

def create_error_response(agent_name: str, agent_id: str, task_id: str, 
                         error_message: str, error_details: str = None) -> StandardizedResponse:
    """创建错误响应的快捷方法"""
    builder = ResponseBuilder(agent_name, agent_id, task_id)
    
    builder.add_issue("error", "high", error_message, 
                     solution=error_details if error_details else "Contact system administrator")
    
    return builder.build(
        response_type=ResponseType.ERROR_REPORT,
        status=TaskStatus.FAILED,
        message=f"Task failed: {error_message}",
        completion_percentage=0.0
    )

def create_progress_response(agent_name: str, agent_id: str, task_id: str, 
                           message: str, completion_percentage: float, 
                           next_steps: List[str] = None) -> StandardizedResponse:
    """创建进度响应的快捷方法"""
    builder = ResponseBuilder(agent_name, agent_id, task_id)
    
    if next_steps:
        for step in next_steps:
            builder.add_next_step(step)
    
    return builder.build(
        response_type=ResponseType.PROGRESS_UPDATE,
        status=TaskStatus.IN_PROGRESS,
        message=message,
        completion_percentage=completion_percentage
    )