#!/usr/bin/env python3
"""
改进的工具调用检测逻辑
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional

class ImprovedToolDetection:
    """改进的工具调用检测器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def has_executed_tools(self, result: str) -> bool:
        """
        改进的工具调用检测逻辑
        - 支持多种JSON格式
        - 更灵活的解析方式
        - 更好的错误处理
        """
        if not isinstance(result, str):
            return False
        
        # 清理结果字符串
        cleaned_result = self._clean_result_string(result)
        
        # 方法1: 直接JSON解析
        if self._try_direct_json_parse(cleaned_result):
            return True
        
        # 方法2: 从代码块中提取JSON
        if self._try_extract_from_code_blocks(result):
            return True
        
        # 方法3: 使用正则表达式查找工具调用模式
        if self._try_regex_tool_detection(result):
            return True
        
        return False
    
    def _clean_result_string(self, result: str) -> str:
        """清理结果字符串，移除多余的空白和格式字符"""
        return result.strip()
    
    def _try_direct_json_parse(self, result: str) -> bool:
        """尝试直接解析JSON"""
        if not result.startswith('{'):
            return False
        
        try:
            data = json.loads(result)
            return self._validate_tool_calls_structure(data)
        except json.JSONDecodeError:
            return False
    
    def _try_extract_from_code_blocks(self, result: str) -> bool:
        """从代码块中提取JSON并解析"""
        # 查找JSON代码块
        json_blocks = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', result, re.DOTALL)
        
        for block in json_blocks:
            try:
                data = json.loads(block)
                if self._validate_tool_calls_structure(data):
                    return True
            except json.JSONDecodeError:
                continue
        
        return False
    
    def _try_regex_tool_detection(self, result: str) -> bool:
        """使用正则表达式检测工具调用模式"""
        # 检查是否包含tool_calls关键字
        if 'tool_calls' not in result:
            return False
        
        # 检查是否包含工具名称
        tool_patterns = [
            r'"tool_name":\s*"[^"]+',
            r'"parameters":\s*\{',
            r'assign_task_to_agent',
            r'identify_task_type',
            r'analyze_agent_result'
        ]
        
        for pattern in tool_patterns:
            if re.search(pattern, result):
                return True
        
        return False
    
    def _validate_tool_calls_structure(self, data: Dict[str, Any]) -> bool:
        """验证工具调用数据结构"""
        if not isinstance(data, dict):
            return False
        
        if "tool_calls" not in data:
            return False
        
        tool_calls = data["tool_calls"]
        if not isinstance(tool_calls, list) or len(tool_calls) == 0:
            return False
        
        # 验证第一个工具调用的结构
        first_call = tool_calls[0]
        if not isinstance(first_call, dict):
            return False
        
        if "tool_name" not in first_call or "parameters" not in first_call:
            return False
        
        return True
    
    def extract_tool_calls(self, result: str) -> Optional[List[Dict[str, Any]]]:
        """提取工具调用列表"""
        # 尝试多种方法提取工具调用
        methods = [
            self._extract_direct_json,
            self._extract_from_code_blocks,
            self._extract_with_regex
        ]
        
        for method in methods:
            try:
                tool_calls = method(result)
                if tool_calls:
                    return tool_calls
            except Exception as e:
                self.logger.warning(f"工具调用提取方法失败: {e}")
                continue
        
        return None
    
    def _extract_direct_json(self, result: str) -> Optional[List[Dict[str, Any]]]:
        """直接从JSON中提取工具调用"""
        try:
            data = json.loads(result.strip())
            if self._validate_tool_calls_structure(data):
                return data["tool_calls"]
        except json.JSONDecodeError:
            pass
        return None
    
    def _extract_from_code_blocks(self, result: str) -> Optional[List[Dict[str, Any]]]:
        """从代码块中提取工具调用"""
        json_blocks = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', result, re.DOTALL)
        
        for block in json_blocks:
            try:
                data = json.loads(block)
                if self._validate_tool_calls_structure(data):
                    return data["tool_calls"]
            except json.JSONDecodeError:
                continue
        
        return None
    
    def _extract_with_regex(self, result: str) -> Optional[List[Dict[str, Any]]]:
        """使用正则表达式提取工具调用（最后的尝试）"""
        # 这是一个备用方法，用于处理格式不标准的情况
        tool_name_match = re.search(r'"tool_name":\s*"([^"]+)"', result)
        if not tool_name_match:
            return None
        
        tool_name = tool_name_match.group(1)
        
        # 尝试提取参数
        params_match = re.search(r'"parameters":\s*(\{[^}]*\})', result)
        parameters = {}
        if params_match:
            try:
                parameters = json.loads(params_match.group(1))
            except json.JSONDecodeError:
                parameters = {}
        
        return [{
            "tool_name": tool_name,
            "parameters": parameters
        }]


# 使用示例
def demonstrate_usage():
    """演示改进的工具检测器使用方法"""
    detector = ImprovedToolDetection()
    
    # 测试用例1: 标准JSON格式
    test1 = '''{"tool_calls": [{"tool_name": "identify_task_type", "parameters": {"user_request": "设计计数器"}}]}'''
    print(f"测试1 - 标准JSON: {detector.has_executed_tools(test1)}")
    
    # 测试用例2: 代码块格式
    test2 = '''```json
    {
        "tool_calls": [
            {
                "tool_name": "assign_task_to_agent",
                "parameters": {
                    "agent_id": "enhanced_real_verilog_agent",
                    "task_description": "设计计数器"
                }
            }
        ]
    }
    ```'''
    print(f"测试2 - 代码块格式: {detector.has_executed_tools(test2)}")
    
    # 测试用例3: 混合文本
    test3 = '''我需要调用工具来完成任务。

    ```json
    {
        "tool_calls": [
            {
                "tool_name": "identify_task_type",
                "parameters": {
                    "user_request": "设计一个计数器模块"
                }
            }
        ]
    }
    ```
    
    这是我的工具调用方案。'''
    print(f"测试3 - 混合文本: {detector.has_executed_tools(test3)}")

if __name__ == "__main__":
    demonstrate_usage()