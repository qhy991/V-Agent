#!/usr/bin/env python3
"""
代码一致性检查器

用于检查智能体间传递的Verilog代码的一致性，确保代码版本匹配。
"""

import re
import logging
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VerilogModuleInfo:
    """Verilog模块信息"""
    module_name: str
    parameters: Dict[str, str]  # 参数名 -> 默认值
    input_ports: List[Dict[str, Any]]  # 输入端口信息
    output_ports: List[Dict[str, Any]]  # 输出端口信息
    code_hash: str  # 代码哈希值
    line_count: int  # 代码行数
    
    def get_signature(self) -> str:
        """获取模块签名（用于比较）"""
        sig_parts = [
            f"module:{self.module_name}",
            f"params:{len(self.parameters)}",
            f"inputs:{len(self.input_ports)}",
            f"outputs:{len(self.output_ports)}"
        ]
        return "|".join(sig_parts)


@dataclass
class ConsistencyCheckResult:
    """一致性检查结果"""
    is_consistent: bool
    confidence: float  # 一致性置信度 (0-1)
    issues: List[str]  # 发现的问题
    recommendations: List[str]  # 修复建议
    module_info1: Optional[VerilogModuleInfo]
    module_info2: Optional[VerilogModuleInfo]


class CodeConsistencyChecker:
    """代码一致性检查器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def extract_module_info(self, verilog_code: str) -> Optional[VerilogModuleInfo]:
        """从Verilog代码中提取模块信息"""
        try:
            # 清理代码（移除注释）
            cleaned_code = self._clean_verilog_code(verilog_code)
            
            # 提取模块名
            module_name = self._extract_module_name(cleaned_code)
            if not module_name:
                self.logger.warning("无法提取模块名称")
                return None
                
            # 提取参数
            parameters = self._extract_parameters(cleaned_code)
            
            # 提取端口信息
            input_ports = self._extract_input_ports(cleaned_code)
            output_ports = self._extract_output_ports(cleaned_code)
            
            # 计算代码哈希
            code_hash = hashlib.md5(verilog_code.encode()).hexdigest()
            line_count = len(verilog_code.split('\n'))
            
            return VerilogModuleInfo(
                module_name=module_name,
                parameters=parameters,
                input_ports=input_ports,
                output_ports=output_ports,
                code_hash=code_hash,
                line_count=line_count
            )
            
        except Exception as e:
            self.logger.error(f"提取模块信息失败: {str(e)}")
            return None
    
    def check_consistency(self, code1: str, code2: str) -> ConsistencyCheckResult:
        """检查两段代码的一致性"""
        # 提取模块信息
        info1 = self.extract_module_info(code1)
        info2 = self.extract_module_info(code2)
        
        issues = []
        recommendations = []
        confidence = 1.0
        
        if not info1 or not info2:
            issues.append("无法解析代码结构")
            recommendations.append("检查代码语法和格式")
            return ConsistencyCheckResult(
                is_consistent=False,
                confidence=0.0,
                issues=issues,
                recommendations=recommendations,
                module_info1=info1,
                module_info2=info2
            )
        
        # 检查模块名
        if info1.module_name != info2.module_name:
            issues.append(f"模块名不匹配: {info1.module_name} vs {info2.module_name}")
            recommendations.append("确保使用相同的模块名")
            confidence -= 0.3
        
        # 检查参数一致性
        param_issues = self._check_parameters_consistency(info1.parameters, info2.parameters)
        if param_issues:
            issues.extend(param_issues)
            recommendations.append("统一参数定义")
            confidence -= 0.2
        
        # 检查端口一致性
        port_issues = self._check_ports_consistency(info1.input_ports, info2.input_ports, "输入")
        port_issues.extend(self._check_ports_consistency(info1.output_ports, info2.output_ports, "输出"))
        if port_issues:
            issues.extend(port_issues)
            recommendations.append("确保端口定义一致")
            confidence -= 0.3
        
        # 检查代码相似性
        if info1.code_hash != info2.code_hash:
            similarity = self._calculate_code_similarity(code1, code2)
            if similarity < 0.8:
                issues.append(f"代码相似度较低: {similarity:.2%}")
                recommendations.append("检查代码版本是否正确")
                confidence -= 0.2
        
        confidence = max(0.0, confidence)
        is_consistent = len(issues) == 0 and confidence > 0.8
        
        return ConsistencyCheckResult(
            is_consistent=is_consistent,
            confidence=confidence,
            issues=issues,
            recommendations=recommendations,
            module_info1=info1,
            module_info2=info2
        )
    
    def validate_code_parameter(self, code_param: str, expected_features: List[str] = None) -> Dict[str, Any]:
        """验证代码参数的完整性"""
        info = self.extract_module_info(code_param)
        if not info:
            return {
                "valid": False,
                "reason": "无法解析代码结构",
                "module_info": None
            }
        
        validation_issues = []
        
        # 检查是否包含期望的特性
        if expected_features:
            for feature in expected_features:
                if not self._check_feature_exists(code_param, feature):
                    validation_issues.append(f"缺少期望特性: {feature}")
        
        # 基本完整性检查
        if len(info.input_ports) < 2:
            validation_issues.append("输入端口数量过少，可能是简化版本")
        
        if not info.parameters:
            validation_issues.append("缺少参数化定义")
        
        return {
            "valid": len(validation_issues) == 0,
            "issues": validation_issues,
            "module_info": info
        }
    
    def _clean_verilog_code(self, code: str) -> str:
        """清理Verilog代码，移除注释"""
        # 移除单行注释
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
        # 移除多行注释
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        return code
    
    def _extract_module_name(self, code: str) -> Optional[str]:
        """提取模块名"""
        pattern = r'module\s+(\w+)'
        match = re.search(pattern, code)
        return match.group(1) if match else None
    
    def _extract_parameters(self, code: str) -> Dict[str, str]:
        """提取参数定义"""
        parameters = {}
        # 匹配参数定义
        param_pattern = r'parameter\s+(\w+)\s*=\s*([^,\)\s]+)'
        matches = re.findall(param_pattern, code)
        
        for param_name, param_value in matches:
            parameters[param_name] = param_value.strip()
        
        return parameters
    
    def _extract_input_ports(self, code: str) -> List[Dict[str, Any]]:
        """提取输入端口"""
        ports = []
        # 匹配输入端口定义
        input_pattern = r'input\s+(?:wire\s+|reg\s+)?(?:\[([^\]]+)\]\s+)?(\w+)'
        matches = re.findall(input_pattern, code)
        
        for width, name in matches:
            ports.append({
                "name": name,
                "width": width if width else "1",
                "type": "input"
            })
        
        return ports
    
    def _extract_output_ports(self, code: str) -> List[Dict[str, Any]]:
        """提取输出端口"""
        ports = []
        # 匹配输出端口定义
        output_pattern = r'output\s+(?:wire\s+|reg\s+)?(?:\[([^\]]+)\]\s+)?(\w+)'
        matches = re.findall(output_pattern, code)
        
        for width, name in matches:
            ports.append({
                "name": name,
                "width": width if width else "1",
                "type": "output"
            })
        
        return ports
    
    def _check_parameters_consistency(self, params1: Dict[str, str], params2: Dict[str, str]) -> List[str]:
        """检查参数一致性"""
        issues = []
        
        # 检查参数数量
        if len(params1) != len(params2):
            issues.append(f"参数数量不匹配: {len(params1)} vs {len(params2)}")
        
        # 检查具体参数
        all_params = set(params1.keys()) | set(params2.keys())
        for param in all_params:
            if param in params1 and param in params2:
                if params1[param] != params2[param]:
                    issues.append(f"参数{param}值不匹配: {params1[param]} vs {params2[param]}")
            elif param in params1:
                issues.append(f"参数{param}在第二个代码中缺失")
            else:
                issues.append(f"参数{param}在第一个代码中缺失")
        
        return issues
    
    def _check_ports_consistency(self, ports1: List[Dict], ports2: List[Dict], port_type: str) -> List[str]:
        """检查端口一致性"""
        issues = []
        
        # 检查端口数量
        if len(ports1) != len(ports2):
            issues.append(f"{port_type}端口数量不匹配: {len(ports1)} vs {len(ports2)}")
        
        # 按名称创建端口字典
        ports1_dict = {p["name"]: p for p in ports1}
        ports2_dict = {p["name"]: p for p in ports2}
        
        # 检查具体端口
        all_ports = set(ports1_dict.keys()) | set(ports2_dict.keys())
        for port_name in all_ports:
            if port_name in ports1_dict and port_name in ports2_dict:
                p1, p2 = ports1_dict[port_name], ports2_dict[port_name]
                if p1["width"] != p2["width"]:
                    issues.append(f"{port_type}端口{port_name}位宽不匹配: {p1['width']} vs {p2['width']}")
            elif port_name in ports1_dict:
                issues.append(f"{port_type}端口{port_name}在第二个代码中缺失")
            else:
                issues.append(f"{port_type}端口{port_name}在第一个代码中缺失")
        
        return issues
    
    def _calculate_code_similarity(self, code1: str, code2: str) -> float:
        """计算代码相似度"""
        # 简单的基于行的相似度计算
        lines1 = set(line.strip() for line in code1.split('\n') if line.strip())
        lines2 = set(line.strip() for line in code2.split('\n') if line.strip())
        
        if not lines1 and not lines2:
            return 1.0
        if not lines1 or not lines2:
            return 0.0
        
        intersection = len(lines1 & lines2)
        union = len(lines1 | lines2)
        
        return intersection / union if union > 0 else 0.0
    
    def _check_feature_exists(self, code: str, feature: str) -> bool:
        """检查代码中是否存在特定特性"""
        feature_patterns = {
            "load_function": r"load",
            "rollover_output": r"rollover",
            "parameterized": r"parameter\s+\w+",
            "width_parameter": r"parameter\s+\w*WIDTH",
            "enable_input": r"input\s+.*\ben\b",
            "reset_input": r"input\s+.*\brst",
        }
        
        pattern = feature_patterns.get(feature, feature)
        return bool(re.search(pattern, code, re.IGNORECASE))


# 全局实例
_global_checker = None

def get_consistency_checker() -> CodeConsistencyChecker:
    """获取全局一致性检查器实例"""
    global _global_checker
    if _global_checker is None:
        _global_checker = CodeConsistencyChecker()
    return _global_checker