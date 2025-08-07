#!/usr/bin/env python3
"""
Tool Call Parser - 工具调用解析器
============================================

从BaseAgent中提取的工具调用解析功能，用于解析LLM响应中的工具调用。
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional

# 为了避免循环导入，在这里重新定义数据类
from dataclasses import dataclass
from typing import Any as AnyType

@dataclass
class ToolCall:
    """工具调用请求"""
    tool_name: str
    parameters: Dict[str, Any]
    call_id: Optional[str] = None

@dataclass
class ToolResult:
    """工具调用结果"""
    call_id: str = ""
    success: bool = True
    result: AnyType = None
    error: Optional[str] = None
    tool_specification: Optional[str] = None
    suggested_fix: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ToolCallParser:
    """工具调用解析器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def parse_tool_calls_from_response(self, response: str) -> List[ToolCall]:
        """解析LLM响应中的工具调用"""
        tool_calls = []
        
        self.logger.debug(f"🔍 [TOOL_CALL_DEBUG] 开始解析工具调用 - 响应长度: {len(response)}")
        self.logger.debug(f"🔍 [TOOL_CALL_DEBUG] 响应前500字: {response[:500]}...")
        
        # 基础检查
        has_tool_calls_key = "tool_calls" in response
        has_json_structure = response.strip().startswith('{') and response.strip().endswith('}')
        has_json_block = "```json" in response
        self.logger.debug(f"🔍 [TOOL_CALL_DEBUG] 初步检查 - tool_calls关键字: {has_tool_calls_key}, JSON结构: {has_json_structure}, JSON代码块: {has_json_block}")
        
        try:
            # 方法1: 直接解析JSON格式
            tool_calls.extend(self._parse_direct_json(response))
            
            # 方法2: 查找JSON代码块
            if not tool_calls:
                tool_calls.extend(self._parse_json_blocks(response))
            
            # 方法3: 文本模式匹配备用方案
            if not tool_calls:
                tool_calls.extend(self._parse_text_patterns(response))
            
            # 最终结果
            self.logger.debug(f"✅ [TOOL_CALL_DEBUG] 解析完成 - 总计找到 {len(tool_calls)} 个工具调用")
            if not tool_calls:
                self._log_debug_info(response)
            
            return tool_calls
            
        except Exception as e:
            self.logger.error(f"❌ [TOOL_CALL_DEBUG] 工具调用解析异常: {str(e)}")
            return []
    
    def _parse_direct_json(self, response: str) -> List[ToolCall]:
        """方法1: 直接解析JSON格式"""
        tool_calls = []
        cleaned_response = response.strip()
        
        if cleaned_response.startswith('{') and cleaned_response.endswith('}'):
            self.logger.debug(f"🔍 [TOOL_CALL_DEBUG] 方法1: 尝试直接解析JSON")
            try:
                data = json.loads(cleaned_response)
                self.logger.debug(f"🔍 [TOOL_CALL_DEBUG] JSON解析成功 - 顶级键: {list(data.keys())}")
                
                # 检查是否为tool_calls数组格式
                if 'tool_calls' in data and isinstance(data['tool_calls'], list):
                    self.logger.debug(f"🔍 [TOOL_CALL_DEBUG] 找到tool_calls数组 - 长度: {len(data['tool_calls'])}")
                    
                    for i, tool_call_data in enumerate(data['tool_calls']):
                        if isinstance(tool_call_data, dict) and 'tool_name' in tool_call_data:
                            tool_call = ToolCall(
                                tool_name=tool_call_data['tool_name'],
                                parameters=tool_call_data.get('parameters', {}),
                                call_id=tool_call_data.get('call_id', f"call_{len(tool_calls)}")
                            )
                            tool_calls.append(tool_call)
                            self.logger.debug(f"🔧 [TOOL_CALL_DEBUG] 解析到工具调用 {i}: {tool_call.tool_name}")
                            self.logger.debug(f"🔧 [TOOL_CALL_DEBUG] 参数: {list(tool_call.parameters.keys())}")
                        else:
                            self.logger.warning(f"⚠️ [TOOL_CALL_DEBUG] 工具调用 {i} 格式错误: {tool_call_data}")
                
                # 检查是否为单工具调用格式
                elif 'tool_name' in data and isinstance(data.get('parameters'), dict):
                    self.logger.debug(f"🔍 [TOOL_CALL_DEBUG] 找到单工具调用格式")
                    tool_call = ToolCall(
                        tool_name=data['tool_name'],
                        parameters=data.get('parameters', {}),
                        call_id=data.get('call_id', f"call_{len(tool_calls)}")
                    )
                    tool_calls.append(tool_call)
                    self.logger.debug(f"🔧 [TOOL_CALL_DEBUG] 解析到单工具调用: {tool_call.tool_name}")
                    self.logger.debug(f"🔧 [TOOL_CALL_DEBUG] 参数: {list(tool_call.parameters.keys())}")
                else:
                    self.logger.debug(f"⚠️ [TOOL_CALL_DEBUG] 没有找到有效的工具调用格式")
                    
            except json.JSONDecodeError as e:
                self.logger.debug(f"⚠️ [TOOL_CALL_DEBUG] JSON解析失败: {str(e)}")
        
        return tool_calls
    
    def _parse_json_blocks(self, response: str) -> List[ToolCall]:
        """方法2: 查找JSON代码块"""
        tool_calls = []
        self.logger.debug(f"🔍 [TOOL_CALL_DEBUG] 方法2: 查找JSON代码块")
        
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, response, re.DOTALL)
        self.logger.debug(f"🔍 [TOOL_CALL_DEBUG] 找到 {len(matches)} 个JSON代码块")
        
        for i, match in enumerate(matches):
            try:
                # 🆕 修复：处理JSON中的控制字符
                cleaned_match = self._clean_json_string(match)
                data = json.loads(cleaned_match)
                
                # 检查是否为tool_calls数组格式
                if 'tool_calls' in data and isinstance(data['tool_calls'], list):
                    self.logger.debug(f"🔍 [TOOL_CALL_DEBUG] JSON代码块 {i} 包含tool_calls数组")
                    for tool_call_data in data['tool_calls']:
                        tool_call = ToolCall(
                            tool_name=tool_call_data['tool_name'],
                            parameters=tool_call_data.get('parameters', {}),
                            call_id=tool_call_data.get('call_id', f"call_{len(tool_calls)}")
                        )
                        tool_calls.append(tool_call)
                        self.logger.debug(f"🔧 [TOOL_CALL_DEBUG] 从代码块解析到工具调用: {tool_call.tool_name}")
                
                # 检查是否为单工具调用格式
                elif 'tool_name' in data and isinstance(data.get('parameters'), dict):
                    self.logger.debug(f"🔍 [TOOL_CALL_DEBUG] JSON代码块 {i} 包含单工具调用")
                    tool_call = ToolCall(
                        tool_name=data['tool_name'],
                        parameters=data.get('parameters', {}),
                        call_id=data.get('call_id', f"call_{len(tool_calls)}")
                    )
                    tool_calls.append(tool_call)
                    self.logger.debug(f"🔧 [TOOL_CALL_DEBUG] 从代码块解析到单工具调用: {tool_call.tool_name}")
            except json.JSONDecodeError as e:
                self.logger.debug(f"⚠️ [TOOL_CALL_DEBUG] JSON代码块 {i} 解析失败: {str(e)}")
                # 🆕 新增：尝试更宽松的解析
                try:
                    self.logger.debug(f"🔍 [TOOL_CALL_DEBUG] 尝试宽松解析JSON代码块 {i}")
                    data = self._parse_json_relaxed(match)
                    if data and 'tool_name' in data:
                        tool_call = ToolCall(
                            tool_name=data['tool_name'],
                            parameters=data.get('parameters', {}),
                            call_id=data.get('call_id', f"call_{len(tool_calls)}")
                        )
                        tool_calls.append(tool_call)
                        self.logger.debug(f"🔧 [TOOL_CALL_DEBUG] 宽松解析成功: {tool_call.tool_name}")
                except Exception as e2:
                    self.logger.debug(f"⚠️ [TOOL_CALL_DEBUG] 宽松解析也失败: {str(e2)}")
                continue
        
        return tool_calls
    
    def _clean_json_string(self, json_str: str) -> str:
        """清理JSON字符串中的控制字符"""
        # 处理常见的控制字符问题
        cleaned = json_str
        
        # 处理换行符：将字符串中的\n替换为\\n
        # 但只处理在字符串值中的换行符，不处理JSON结构中的换行符
        import re
        
        # 匹配字符串值中的换行符
        def replace_newlines_in_strings(match):
            content = match.group(1)
            # 将内容中的换行符替换为转义的换行符
            content = content.replace('\n', '\\n')
            content = content.replace('\r', '\\r')
            content = content.replace('\t', '\\t')
            return f'"{content}"'
        
        # 使用正则表达式找到所有字符串值并处理其中的换行符
        pattern = r'"([^"\\]*(?:\\.[^"\\]*)*)"'
        cleaned = re.sub(pattern, replace_newlines_in_strings, cleaned)
        
        return cleaned
    
    def _parse_json_relaxed(self, json_str: str) -> Dict[str, Any]:
        """宽松的JSON解析，处理各种格式问题"""
        try:
            # 首先尝试清理后的解析
            cleaned = self._clean_json_string(json_str)
            return json.loads(cleaned)
        except:
            try:
                # 如果还是失败，尝试更激进的清理
                # 移除所有控制字符
                import string
                printable = set(string.printable)
                cleaned = ''.join(filter(lambda x: x in printable, json_str))
                return json.loads(cleaned)
            except:
                # 最后的尝试：手动解析关键字段
                self.logger.debug(f"🔍 [TOOL_CALL_DEBUG] 尝试手动解析关键字段")
                return self._parse_json_manually(json_str)
    
    def _parse_json_manually(self, json_str: str) -> Dict[str, Any]:
        """手动解析JSON的关键字段"""
        result = {}
        
        # 提取tool_name
        tool_name_match = re.search(r'"tool_name"\s*:\s*"([^"]+)"', json_str)
        if tool_name_match:
            result['tool_name'] = tool_name_match.group(1)
        
        # 提取parameters（简化版本）
        parameters = {}
        # 查找file_path
        file_path_match = re.search(r'"file_path"\s*:\s*"([^"]+)"', json_str)
        if file_path_match:
            parameters['file_path'] = file_path_match.group(1)
        
        # 查找content（处理多行内容）
        content_match = re.search(r'"content"\s*:\s*"([^"]*(?:\\n[^"]*)*)"', json_str, re.DOTALL)
        if content_match:
            content = content_match.group(1)
            # 处理转义的换行符
            content = content.replace('\\n', '\n')
            parameters['content'] = content
        
        if parameters:
            result['parameters'] = parameters
        
        return result
    
    def _parse_text_patterns(self, response: str) -> List[ToolCall]:
        """方法3: 文本模式匹配备用方案"""
        tool_calls = []
        self.logger.debug(f"🔍 [TOOL_CALL_DEBUG] 方法3: 文本模式匹配")
        
        tool_patterns = [
            r'调用工具\s*[：:]\s*(\w+)',
            r'使用工具\s*[：:]\s*(\w+)',
            r'tool[：:]\s*(\w+)',
            r'function[：:]\s*(\w+)'
        ]
        
        for pattern in tool_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            if matches:
                self.logger.debug(f"🔍 [TOOL_CALL_DEBUG] 模式 '{pattern}' 匹配到 {len(matches)} 个工具")
            for match in matches:
                tool_call = ToolCall(
                    tool_name=match,
                    parameters={},
                    call_id=f"call_{len(tool_calls)}"
                )
                tool_calls.append(tool_call)
                self.logger.debug(f"🔧 [TOOL_CALL_DEBUG] 从文本中解析到工具调用: {tool_call.tool_name}")
        
        return tool_calls
    
    def _log_debug_info(self, response: str):
        """记录调试信息"""
        self.logger.debug(f"⚠️ [TOOL_CALL_DEBUG] 没有解析到任何工具调用！")
        # 提供调试信息
        if "write_file" in response.lower():
            self.logger.debug(f"🔍 [TOOL_CALL_DEBUG] 响应中包含'write_file'但没有被解析为工具调用")
        if "generate_verilog" in response.lower():
            self.logger.debug(f"🔍 [TOOL_CALL_DEBUG] 响应中包含'generate_verilog'但没有被解析为工具调用")
    
    def normalize_tool_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """标准化工具参数"""
        if not parameters:
            return {}
        
        # 获取实际参数键
        actual_param_keys = list(parameters.keys())
        self.logger.debug(f"🔧 [PARAM_NORM] 工具 {tool_name} - 实际参数: {actual_param_keys}")
        
        # 构建参数映射
        mappings = self._build_parameter_mappings(tool_name, actual_param_keys)
        
        if mappings:
            self.logger.debug(f"🔧 [PARAM_NORM] 应用映射: {mappings}")
            normalized_params = {}
            for original_key, mapped_key in mappings.items():
                if original_key in parameters:
                    normalized_params[mapped_key] = parameters[original_key]
                    self.logger.debug(f"🔧 [PARAM_NORM] {original_key} -> {mapped_key}: {str(parameters[original_key])[:100]}...")
            
            # 保留未映射的参数
            for key, value in parameters.items():
                if key not in mappings and key not in normalized_params:
                    normalized_params[key] = value
            
            self.logger.debug(f"🔧 [PARAM_NORM] 标准化后参数: {list(normalized_params.keys())}")
            return normalized_params
        else:
            # 应用基本参数映射
            return self._apply_basic_parameter_mapping(parameters)
    
    def _build_parameter_mappings(self, tool_name: str, actual_params: List[str]) -> Dict[str, str]:
        """构建参数映射字典"""
        mappings = {}
        
        # 工具特定的参数映射规则
        tool_param_rules = {
            'write_file': {
                'expected_params': ['filename', 'content', 'directory', 'file_path'],
                'mappings': {
                    'file': 'filename',
                    'filepath': 'file_path', 
                    'file_name': 'filename',
                    'path': 'file_path',
                    'text': 'content',
                    'data': 'content',
                    'body': 'content',
                    'dir': 'directory',
                    'folder': 'directory',
                    'output_dir': 'directory'
                }
            },
            'read_file': {
                'expected_params': ['filepath', 'file_path'],
                'mappings': {
                    'file': 'filepath',
                    'filename': 'filepath',
                    'path': 'filepath'
                }
            },
            'generate_verilog_code': {
                'expected_params': ['module_name', 'description', 'requirements'],
                'mappings': {
                    'name': 'module_name',
                    'module': 'module_name',
                    'desc': 'description',
                    'requirement': 'requirements',
                    'spec': 'requirements',
                    'specification': 'requirements'
                }
            },
            'generate_testbench': {
                'expected_params': ['module_name', 'verilog_code', 'test_cases'],
                'mappings': {
                    'name': 'module_name',
                    'module': 'module_name', 
                    'code': 'verilog_code',
                    'verilog': 'verilog_code',
                    'design': 'verilog_code',
                    'tests': 'test_cases',
                    'test': 'test_cases',
                    'cases': 'test_cases'
                }
            }
        }
        
        if tool_name in tool_param_rules:
            rules = tool_param_rules[tool_name]
            
            for actual_param in actual_params:
                # 精确匹配
                if actual_param in rules['expected_params']:
                    continue
                
                # 映射匹配
                if actual_param in rules['mappings']:
                    target_param = rules['mappings'][actual_param]
                    if target_param in rules['expected_params']:
                        mappings[actual_param] = target_param
                        self.logger.debug(f"🔧 [PARAM_MAP] {tool_name}: {actual_param} -> {target_param}")
                        continue
                
                # 模糊匹配
                for expected in rules['expected_params']:
                    if self._fuzzy_match(actual_param, expected):
                        mappings[actual_param] = expected
                        self.logger.debug(f"🔧 [PARAM_MAP] {tool_name}: {actual_param} ~> {expected} (模糊匹配)")
                        break
        
        return mappings
    
    def _fuzzy_match(self, actual: str, expected: str) -> bool:
        """模糊参数匹配"""
        actual_lower = actual.lower()
        expected_lower = expected.lower()
        
        # 包含关系匹配
        if actual_lower in expected_lower or expected_lower in actual_lower:
            return True
        
        # 去掉分隔符后的匹配
        actual_clean = re.sub(r'[_-]', '', actual_lower)
        expected_clean = re.sub(r'[_-]', '', expected_lower)
        
        return actual_clean == expected_clean
    
    def _apply_basic_parameter_mapping(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """应用基本参数映射"""
        basic_mappings = {
            'file': 'filename',
            'path': 'file_path',
            'dir': 'directory',
            'text': 'content',
            'data': 'content'
        }
        
        normalized = {}
        for key, value in parameters.items():
            mapped_key = basic_mappings.get(key.lower(), key)
            normalized[mapped_key] = value
        
        return normalized