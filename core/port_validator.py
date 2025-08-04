#!/usr/bin/env python3
"""
端口验证器 - 专门处理端口一致性检查和自动修复
==================================================

这个模块解决了智能体间端口信息传递不一致的问题：
✅ 自动提取Verilog模块端口信息
✅ 验证测试台端口与设计端口的一致性
✅ 自动修复端口不匹配问题
✅ 提供详细的端口分析报告
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PortInfo:
    """端口信息"""
    name: str
    direction: str  # input, output, inout
    width: int
    msb: Optional[int] = None
    lsb: Optional[int] = None
    description: str = ""


@dataclass
class ModuleInfo:
    """模块信息"""
    name: str
    ports: List[PortInfo]
    port_count: int
    file_path: str = ""


class PortValidator:
    """端口验证器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_module_ports(self, verilog_content: str, file_path: str = "") -> Optional[ModuleInfo]:
        """从Verilog代码中提取模块端口信息"""
        try:
            # 提取模块定义
            module_pattern = r'module\s+(\w+)\s*\(([^)]+)\);'
            match = re.search(module_pattern, verilog_content, re.DOTALL)
            
            if not match:
                self.logger.warning("未找到模块定义")
                return None
            
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
                    msb_val = None
                    lsb_val = None
                    
                    if msb and lsb:
                        msb_val = int(msb)
                        lsb_val = int(lsb)
                        width = msb_val - lsb_val + 1
                    
                    port = PortInfo(
                        name=port_name,
                        direction=direction,
                        width=width,
                        msb=msb_val,
                        lsb=lsb_val
                    )
                    ports.append(port)
            
            return ModuleInfo(
                name=module_name,
                ports=ports,
                port_count=len(ports),
                file_path=file_path
            )
            
        except Exception as e:
            self.logger.error(f"提取模块端口信息失败: {str(e)}")
            return None
    
    def validate_testbench_ports(self, testbench_content: str, design_module: ModuleInfo) -> Dict[str, Any]:
        """验证测试台端口与设计端口的一致性"""
        try:
            # 提取测试台中的模块实例化
            instance_pattern = rf'{design_module.name}\s+\w+\s*\(([^)]+)\);'
            match = re.search(instance_pattern, testbench_content, re.DOTALL)
            
            if not match:
                return {
                    "valid": False,
                    "error": f"未找到模块 {design_module.name} 的实例化",
                    "design_ports": design_module,
                    "testbench_connections": []
                }
            
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
                    port_connections.append({
                        "port": port_name,
                        "signal": signal_name,
                        "line": line
                    })
            
            # 验证端口连接
            design_port_names = {port.name for port in design_module.ports}
            testbench_port_names = {conn["port"] for conn in port_connections}
            
            missing_ports = design_port_names - testbench_port_names
            extra_ports = testbench_port_names - design_port_names
            
            # 生成详细报告
            validation_report = {
                "valid": len(missing_ports) == 0 and len(extra_ports) == 0,
                "missing_ports": list(missing_ports),
                "extra_ports": list(extra_ports),
                "design_ports": design_module,
                "testbench_connections": port_connections,
                "port_count_match": len(design_port_names) == len(testbench_port_names),
                "detailed_analysis": self._generate_detailed_analysis(
                    design_module, port_connections, missing_ports, extra_ports
                )
            }
            
            return validation_report
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"验证失败: {str(e)}",
                "design_ports": design_module,
                "testbench_connections": []
            }
    
    def auto_fix_testbench_ports(self, testbench_content: str, design_module: ModuleInfo) -> Optional[str]:
        """自动修复测试台端口不匹配问题"""
        try:
            # 查找模块实例化
            instance_pattern = rf'{design_module.name}\s+\w+\s*\(([^)]+)\);'
            match = re.search(instance_pattern, testbench_content, re.DOTALL)
            
            if not match:
                self.logger.error(f"未找到模块 {design_module.name} 的实例化")
                return None
            
            instance_ports = match.group(1)
            
            # 构建正确的端口连接
            correct_connections = []
            existing_connections = {}
            
            # 先收集现有的连接
            for line in instance_ports.split(','):
                line = line.strip()
                if not line:
                    continue
                
                port_match = re.search(r'\.(\w+)\s*\(\s*(\w+)\s*\)', line)
                if port_match:
                    port_name = port_match.group(1)
                    signal_name = port_match.group(2)
                    existing_connections[port_name] = signal_name
            
            # 为每个设计端口构建连接
            for port in design_module.ports:
                port_name = port.name
                
                if port_name in existing_connections:
                    # 使用现有连接
                    signal_name = existing_connections[port_name]
                    correct_connections.append(f".{port_name}({signal_name})")
                else:
                    # 生成默认信号名
                    default_signal = f"{port_name}_signal"
                    correct_connections.append(f".{port_name}({default_signal})")
                    self.logger.info(f"为端口 {port_name} 生成默认信号: {default_signal}")
            
            # 替换端口连接
            new_instance_ports = ",\n        ".join(correct_connections)
            new_instance = f"{design_module.name} uut (\n        {new_instance_ports}\n    );"
            
            # 替换整个实例化
            fixed_content = re.sub(instance_pattern + r';', new_instance, testbench_content, flags=re.DOTALL)
            
            self.logger.info(f"自动修复完成: 模块 {design_module.name} 的端口连接")
            return fixed_content
            
        except Exception as e:
            self.logger.error(f"自动修复测试台端口失败: {str(e)}")
            return None
    
    def _generate_detailed_analysis(self, design_module: ModuleInfo, 
                                  port_connections: List[Dict[str, Any]],
                                  missing_ports: set, extra_ports: set) -> Dict[str, Any]:
        """生成详细的端口分析报告"""
        analysis = {
            "design_summary": {
                "module_name": design_module.name,
                "total_ports": design_module.port_count,
                "input_ports": [p.name for p in design_module.ports if p.direction == "input"],
                "output_ports": [p.name for p in design_module.ports if p.direction == "output"],
                "inout_ports": [p.name for p in design_module.ports if p.direction == "inout"]
            },
            "testbench_summary": {
                "connected_ports": len(port_connections),
                "port_connections": port_connections
            },
            "issues": {
                "missing_ports": list(missing_ports),
                "extra_ports": list(extra_ports),
                "total_issues": len(missing_ports) + len(extra_ports)
            },
            "recommendations": []
        }
        
        # 生成修复建议
        if missing_ports:
            analysis["recommendations"].append({
                "type": "missing_ports",
                "message": f"需要添加缺失的端口连接: {list(missing_ports)}",
                "suggestions": [f".{port}({port}_signal)" for port in missing_ports]
            })
        
        if extra_ports:
            analysis["recommendations"].append({
                "type": "extra_ports",
                "message": f"需要移除多余的端口连接: {list(extra_ports)}",
                "suggestions": [f"删除 .{port} 连接" for port in extra_ports]
            })
        
        return analysis
    
    def generate_port_report(self, validation_result: Dict[str, Any]) -> str:
        """生成端口验证报告"""
        if not validation_result.get("valid", False):
            report = f"""
🔍 端口验证报告
================

❌ 端口验证失败

设计模块: {validation_result.get('design_ports', {}).get('name', 'unknown')}
测试台连接数: {len(validation_result.get('testbench_connections', []))}

问题详情:
"""
            
            if validation_result.get("missing_ports"):
                report += f"- 缺失端口: {validation_result['missing_ports']}\n"
            
            if validation_result.get("extra_ports"):
                report += f"- 多余端口: {validation_result['extra_ports']}\n"
            
            if "detailed_analysis" in validation_result:
                analysis = validation_result["detailed_analysis"]
                report += f"""
详细分析:
- 设计端口总数: {analysis['design_summary']['total_ports']}
- 输入端口: {analysis['design_summary']['input_ports']}
- 输出端口: {analysis['design_summary']['output_ports']}
- 双向端口: {analysis['design_summary']['inout_ports']}

修复建议:
"""
                for rec in analysis.get("recommendations", []):
                    report += f"- {rec['message']}\n"
            
            return report
        else:
            return f"""
🔍 端口验证报告
================

✅ 端口验证通过

设计模块: {validation_result.get('design_ports', {}).get('name', 'unknown')}
端口连接数: {len(validation_result.get('testbench_connections', []))}
所有端口连接正确匹配！
"""


# 全局实例
port_validator = PortValidator() 