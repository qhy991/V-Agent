#!/usr/bin/env python3
"""
统一Schema定义系统
Unified Schema Definitions for Framework Consistency
"""

from typing import Dict, Any

class UnifiedSchemas:
    """统一的Schema定义，确保所有工具使用一致的参数结构"""
    
    # 🎯 核心参数定义 - 统一字段名和验证规则
    CORE_PARAMETERS = {
        # Verilog代码参数 - 支持多种别名
        "verilog_code": {
            "type": "string",
            "minLength": 10,
            "maxLength": 100000,
            "description": "Verilog代码内容",
            "aliases": ["code", "module_code", "design_code"]  # 支持的别名
        },
        
        # 需求描述参数
        "requirements": {
            "type": "string", 
            "minLength": 10,
            "maxLength": 10000,
            "description": "设计需求和功能描述",
            "aliases": ["design_requirements", "specification"]
        },
        
        # 模块名称参数
        "module_name": {
            "type": "string",
            "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
            "minLength": 1,
            "maxLength": 100,
            "description": "Verilog模块名称，必须以字母开头",
            "aliases": ["name", "module"]
        },
        
        # 文件路径参数
        "file_path": {
            "type": "string",
            "minLength": 1,
            "maxLength": 500,
            "description": "文件路径",
            "aliases": ["path", "filename", "file"]
        },
        
        # 文件列表参数
        "verilog_files": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1,
                "maxLength": 500
            },
            "minItems": 1,
            "maxItems": 50,
            "description": "Verilog文件路径列表",
            "aliases": ["files", "design_files", "module_files"]
        },
        
        # 端口定义参数 (支持灵活格式)
        "input_ports": {
            "type": "array",
            "items": {
                "oneOf": [
                    # 字符串格式: "port_name [width]"
                    {"type": "string", "pattern": r"^\s*\w+(\s*\[\d+:\d+\])?\s*$"},
                    # 对象格式
                    {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$"
                            },
                            "width": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 1024,
                                "default": 1
                            },
                            "description": {
                                "type": "string",
                                "maxLength": 200
                            }
                        },
                        "required": ["name"],
                        "additionalProperties": False
                    }
                ]
            },
            "maxItems": 100,
            "description": "输入端口定义，支持字符串或对象格式",
            "aliases": ["inputs", "input_signals"]
        },
        
        "output_ports": {
            "type": "array", 
            "items": {
                "oneOf": [
                    # 字符串格式: "port_name [width]"
                    {"type": "string", "pattern": r"^\s*\w+(\s*\[\d+:\d+\])?\s*$"},
                    # 对象格式
                    {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$"
                            },
                            "width": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 1024,
                                "default": 1
                            },
                            "description": {
                                "type": "string",
                                "maxLength": 200
                            }
                        },
                        "required": ["name"],
                        "additionalProperties": False
                    }
                ]
            },
            "maxItems": 100,
            "description": "输出端口定义，支持字符串或对象格式",
            "aliases": ["outputs", "output_signals"]
        }
    }
    
    # 🎯 工具特定Schema定义
    TOOL_SCHEMAS = {
        "analyze_design_requirements": {
            "type": "object",
            "properties": {
                "requirements": CORE_PARAMETERS["requirements"],
                "design_type": {
                    "type": "string",
                    "enum": ["combinational", "sequential", "mixed", "custom"],
                    "default": "mixed",
                    "description": "设计类型分类"
                },
                "complexity_level": {
                    "type": "string",
                    "enum": ["simple", "medium", "complex", "advanced"],
                    "default": "medium",
                    "description": "设计复杂度级别"
                }
            },
            "required": ["requirements"],
            "additionalProperties": False
        },
        
        "generate_verilog_code": {
            "type": "object",
            "properties": {
                "module_name": CORE_PARAMETERS["module_name"],
                "requirements": CORE_PARAMETERS["requirements"],
                "input_ports": CORE_PARAMETERS["input_ports"],
                "output_ports": CORE_PARAMETERS["output_ports"],
                "clock_domain": {
                    "type": "object",
                    "properties": {
                        "clock_name": {
                            "type": "string",
                            "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                            "default": "clk"
                        },
                        "reset_name": {
                            "type": "string", 
                            "pattern": r"^[a-zA-Z][a-zA-Z0-9_]*$",
                            "default": "rst"
                        },
                        "reset_active": {
                            "type": "string",
                            "enum": ["high", "low"],
                            "default": "high"
                        }
                    },
                    "additionalProperties": False,
                    "description": "时钟域配置"
                },
                "coding_style": {
                    "type": "string",
                    "enum": ["behavioral", "structural", "rtl", "mixed"],
                    "default": "rtl",
                    "description": "Verilog编码风格"
                }
            },
            "required": ["module_name", "requirements"],
            "additionalProperties": False
        },
        
        "analyze_code_quality": {
            "type": "object",
            "properties": {
                "verilog_code": CORE_PARAMETERS["verilog_code"],
                "analysis_scope": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["syntax", "style", "timing", "synthesis", "simulation", "coverage"]
                    },
                    "default": ["syntax", "style"],
                    "description": "分析范围选择"
                },
                "coding_standard": {
                    "type": "string",
                    "enum": ["ieee1800", "custom", "industry"],
                    "default": "ieee1800",
                    "description": "编码标准规范"
                }
            },
            "required": ["verilog_code"],
            "additionalProperties": False
        },
        
        "generate_testbench": {
            "type": "object",
            "properties": {
                "module_name": CORE_PARAMETERS["module_name"],
                "verilog_code": CORE_PARAMETERS["verilog_code"],
                "test_scenarios": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "maxLength": 1000
                    },
                    "maxItems": 20,
                    "description": "测试场景描述列表",
                    "aliases": ["test_cases", "scenarios"]
                },
                "clock_period": {
                    "type": "number",
                    "minimum": 0.1,
                    "maximum": 1000.0,
                    "default": 10.0,
                    "description": "时钟周期(ns)"
                },
                "simulation_time": {
                    "type": "integer",
                    "minimum": 100,
                    "maximum": 1000000,
                    "default": 10000,
                    "description": "仿真时间(时钟周期数)"
                }
            },
            "required": ["module_name", "verilog_code"],
            "additionalProperties": False
        },
        
        "run_simulation": {
            "type": "object",
            "properties": {
                "module_file": CORE_PARAMETERS["file_path"],
                "testbench_file": CORE_PARAMETERS["file_path"],
                "module_code": CORE_PARAMETERS["verilog_code"],
                "testbench_code": CORE_PARAMETERS["verilog_code"],
                "simulator": {
                    "type": "string",
                    "enum": ["iverilog", "modelsim", "vcs", "vivado"],
                    "default": "iverilog",
                    "description": "仿真器选择"
                },
                "simulation_options": {
                    "type": "object",
                    "properties": {
                        "compile_flags": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "runtime_flags": {
                            "type": "array", 
                            "items": {"type": "string"}
                        },
                        "timeout": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 3600,
                            "default": 30
                        }
                    },
                    "additionalProperties": False,
                    "description": "仿真选项配置"
                }
            },
            "additionalProperties": False
        },
        
        "search_existing_modules": {
            "type": "object",
            "properties": {
                "module_type": {
                    "type": "string",
                    "enum": ["arithmetic", "memory", "interface", "controller", "dsp", "custom"],
                    "description": "模块类型分类"
                },
                "functionality": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 500,
                    "description": "功能关键词描述"
                },
                "complexity_filter": {
                    "type": "string",
                    "enum": ["simple", "medium", "complex", "any"],
                    "default": "any",
                    "description": "复杂度过滤条件"
                },
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 10,
                    "description": "最大返回结果数"
                }
            },
            "additionalProperties": False
        }
    }
    
    @classmethod
    def get_unified_schema(cls, tool_name: str) -> Dict[str, Any]:
        """获取指定工具的统一Schema定义"""
        if tool_name in cls.TOOL_SCHEMAS:
            return cls.TOOL_SCHEMAS[tool_name].copy()
        
        # 如果没有预定义Schema，返回通用Schema
        return {
            "type": "object",
            "additionalProperties": True,
            "description": f"通用Schema for {tool_name}"
        }
    
    @classmethod
    def resolve_parameter_aliases(cls, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """解析参数别名，将别名映射到标准参数名"""
        resolved = {}
        
        # 创建别名映射表
        alias_map = {}
        for standard_name, param_def in cls.CORE_PARAMETERS.items():
            if "aliases" in param_def:
                for alias in param_def["aliases"]:
                    alias_map[alias] = standard_name
        
        # 解析参数
        for key, value in parameters.items():
            # 如果是别名，映射到标准名称
            standard_key = alias_map.get(key, key)
            resolved[standard_key] = value
        
        return resolved
    
    @classmethod
    def normalize_port_definitions(cls, ports: list) -> list:
        """标准化端口定义，支持字符串和对象格式"""
        if not isinstance(ports, list):
            return []
        
        normalized = []
        for port in ports:
            if isinstance(port, str):
                # 解析字符串格式: "port_name [width]" 或 "port_name"
                port = port.strip()
                if '[' in port and ']' in port:
                    # 带宽度的端口: "data [7:0]"
                    parts = port.split('[')
                    name = parts[0].strip()
                    width_part = parts[1].split(']')[0]
                    if ':' in width_part:
                        # [7:0] 格式
                        high, low = width_part.split(':')
                        width = int(high.strip()) - int(low.strip()) + 1
                    else:
                        # [7] 格式
                        width = int(width_part.strip()) + 1
                    normalized.append({
                        "name": name,
                        "width": width,
                        "description": f"{name} signal ({width} bits)"
                    })
                else:
                    # 简单端口: "clk"
                    normalized.append({
                        "name": port,
                        "width": 1,
                        "description": f"{port} signal"
                    })
            elif isinstance(port, dict) and "name" in port:
                # 已经是对象格式，直接使用
                normalized.append(port)
        
        return normalized
    
    @classmethod
    def validate_and_normalize_parameters(cls, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证并标准化参数"""
        # 步骤1: 解析别名
        resolved_params = cls.resolve_parameter_aliases(parameters)
        
        # 步骤2: 标准化端口定义
        for port_key in ["input_ports", "output_ports"]:
            if port_key in resolved_params:
                resolved_params[port_key] = cls.normalize_port_definitions(
                    resolved_params[port_key]
                )
        
        # 步骤3: 应用默认值
        schema = cls.get_unified_schema(tool_name)
        if "properties" in schema:
            for prop_name, prop_def in schema["properties"].items():
                if prop_name not in resolved_params and "default" in prop_def:
                    resolved_params[prop_name] = prop_def["default"]
        
        return resolved_params
    
    @classmethod
    def get_parameter_mapping_info(cls) -> Dict[str, Any]:
        """获取参数映射信息，用于调试和文档"""
        mapping_info = {
            "standard_parameters": list(cls.CORE_PARAMETERS.keys()),
            "alias_mappings": {},
            "supported_tools": list(cls.TOOL_SCHEMAS.keys())
        }
        
        for standard_name, param_def in cls.CORE_PARAMETERS.items():
            if "aliases" in param_def:
                mapping_info["alias_mappings"][standard_name] = param_def["aliases"]
        
        return mapping_info


# 🎯 便捷函数
def get_tool_schema(tool_name: str) -> Dict[str, Any]:
    """获取工具Schema的便捷函数"""
    return UnifiedSchemas.get_unified_schema(tool_name)

def normalize_tool_parameters(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """标准化工具参数的便捷函数"""
    return UnifiedSchemas.validate_and_normalize_parameters(tool_name, parameters)

def resolve_aliases(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """解析参数别名的便捷函数"""
    return UnifiedSchemas.resolve_parameter_aliases(parameters)