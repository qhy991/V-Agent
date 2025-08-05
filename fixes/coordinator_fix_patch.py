#!/usr/bin/env python3
"""
LLM协调智能体修复补丁
直接修复现有代码中的问题
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional

class CoordinatorFixPatch:
    """协调智能体修复补丁"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def apply_improved_tool_detection(self, coordinator_instance):
        """应用改进的工具检测逻辑"""
        
        def improved_has_executed_tools(result: str) -> bool:
            """改进的工具执行检测方法"""
            if not isinstance(result, str):
                return False
            
            # 方法1: 直接JSON解析
            try:
                # 去除前后空白
                cleaned_result = result.strip()
                if cleaned_result.startswith('{'):
                    data = json.loads(cleaned_result)
                    if self._validate_tool_calls_structure(data):
                        return True
            except json.JSONDecodeError:
                pass
            
            # 方法2: 从代码块中提取JSON
            json_blocks = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', result, re.DOTALL)
            for block in json_blocks:
                try:
                    data = json.loads(block)
                    if self._validate_tool_calls_structure(data):
                        return True
                except json.JSONDecodeError:
                    continue
            
            # 方法3: 检查关键词和模式
            if 'tool_calls' in result and ('"tool_name"' in result or '"parameters"' in result):
                return True
            
            return False
        
        def _validate_tool_calls_structure(data: Dict[str, Any]) -> bool:
            """验证工具调用数据结构"""
            if not isinstance(data, dict) or "tool_calls" not in data:
                return False
            
            tool_calls = data["tool_calls"]
            if not isinstance(tool_calls, list) or len(tool_calls) == 0:
                return False
            
            first_call = tool_calls[0]
            return (isinstance(first_call, dict) and 
                   "tool_name" in first_call and 
                   "parameters" in first_call)
        
        # 替换原有方法
        coordinator_instance._has_executed_tools = improved_has_executed_tools
        coordinator_instance._validate_tool_calls_structure = _validate_tool_calls_structure
        
        self.logger.info("✅ 已应用改进的工具检测逻辑")
    
    def apply_enhanced_tool_call_parsing(self, coordinator_instance):
        """应用增强的工具调用解析"""
        
        def extract_tool_calls_from_response(response: str) -> Optional[List[Dict[str, Any]]]:
            """从LLM响应中提取工具调用"""
            
            # 方法1: 直接JSON解析
            try:
                data = json.loads(response.strip())
                if self._validate_tool_calls_structure(data):
                    return data["tool_calls"]
            except json.JSONDecodeError:
                pass
            
            # 方法2: 从代码块提取
            json_blocks = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            for block in json_blocks:
                try:
                    data = json.loads(block)
                    if self._validate_tool_calls_structure(data):
                        return data["tool_calls"]
                except json.JSONDecodeError:
                    continue
            
            # 方法3: 正则表达式备用方案
            tool_name_match = re.search(r'"tool_name":\s*"([^"]+)"', response)
            if tool_name_match:
                tool_name = tool_name_match.group(1)
                
                # 尝试提取参数
                params_match = re.search(r'"parameters":\s*(\{[^}]*\})', response)
                parameters = {}
                if params_match:
                    try:
                        parameters = json.loads(params_match.group(1))
                    except json.JSONDecodeError:
                        # 如果JSON解析失败，尝试提取简单的键值对
                        param_content = params_match.group(1)
                        simple_params = re.findall(r'"([^"]+)":\s*"([^"]*)"', param_content)
                        parameters = dict(simple_params)
                
                return [{
                    "tool_name": tool_name,
                    "parameters": parameters
                }]
            
            return None
        
        # 添加到协调器实例
        coordinator_instance.extract_tool_calls_from_response = extract_tool_calls_from_response
        
        self.logger.info("✅ 已应用增强的工具调用解析")
    
    def apply_better_error_handling(self, coordinator_instance):
        """应用更好的错误处理机制"""
        
        original_coordinate_task = coordinator_instance.coordinate_task
        
        async def enhanced_coordinate_task(self, user_request: str, **kwargs):
            """增强的任务协调方法"""
            max_retries = kwargs.get('max_retries', 2)
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        self.logger.info(f"🔄 重试任务协调 (第{attempt}次重试)")
                    
                    result = await original_coordinate_task(user_request, **kwargs)
                    
                    # 检查结果质量
                    if result.get("success", False):
                        return result
                    
                    # 如果失败但还有重试机会，继续
                    if attempt < max_retries:
                        error_msg = result.get("error", "未知错误")
                        self.logger.warning(f"⚠️ 任务执行失败，准备重试: {error_msg}")
                        
                        # 根据错误类型调整策略
                        if "工具调用" in error_msg:
                            kwargs["force_simple_tools"] = True
                        
                        continue
                    
                    return result
                    
                except Exception as e:
                    if attempt < max_retries:
                        self.logger.warning(f"⚠️ 协调异常，准备重试: {str(e)}")
                        continue
                    else:
                        self.logger.error(f"❌ 最终失败: {str(e)}")
                        return {
                            "success": False,
                            "error": f"协调失败 (重试{max_retries}次): {str(e)}",
                            "attempts": attempt + 1
                        }
            
            return {
                "success": False,
                "error": "达到最大重试次数",
                "attempts": max_retries + 1
            }
        
        # 替换原有方法 (需要绑定到实例)
        import types
        coordinator_instance.coordinate_task = types.MethodType(enhanced_coordinate_task, coordinator_instance)
        
        self.logger.info("✅ 已应用更好的错误处理机制")
    
    def apply_robust_system_prompt_generation(self, coordinator_instance):
        """应用健壮的System Prompt生成"""
        
        def generate_robust_system_prompt(self, tools_json: str) -> str:
            """生成健壮的System Prompt"""
            
            # 解析可用工具
            try:
                tools_list = json.loads(tools_json) if isinstance(tools_json, str) else tools_json
                available_tool_names = [tool.get("name", "") for tool in tools_list if isinstance(tool, dict)]
            except:
                available_tool_names = ["identify_task_type", "assign_task_to_agent", "provide_final_answer"]
            
            # 构建工具特定的指导
            tool_guidance = self._build_tool_specific_guidance(available_tool_names)
            
            base_prompt = f"""
# 角色
你是一个智能协调器，负责协调多个智能体完成复杂任务。

# 🚨 强制规则 (必须严格遵守)
1. **禁止直接回答**: 绝对禁止直接回答用户的任何问题或请求。
2. **必须调用工具**: 你的所有回复都必须是JSON格式的工具调用。
3. **禁止生成描述性文本**: 绝对禁止生成任何解释、分析、策略描述或其他文本内容。
4. **🚨 只能使用可用工具**: 只能调用以下列出的工具: {', '.join(available_tool_names)}

{tool_guidance}

# 输出格式 (严格要求)
你的回复必须严格按照以下JSON格式：
```json
{{
    "tool_calls": [
        {{
            "tool_name": "工具名称",
            "parameters": {{
                "参数名": "参数值"
            }}
        }}
    ]
}}
```

# 可用工具
{tools_json}

立即开始分析用户请求并调用第一个工具。不要回复任何其他内容。
"""
            return base_prompt
        
        def _build_tool_specific_guidance(self, tool_names: List[str]) -> str:
            """构建工具特定的指导"""
            guidance = []
            
            if "identify_task_type" in tool_names:
                guidance.append("5. **首先识别任务**: 总是先调用 `identify_task_type` 分析任务类型")
            
            if "assign_task_to_agent" in tool_names:
                guidance.append("6. **正确分配任务**: 使用 `assign_task_to_agent` 分配任务给智能体")
                guidance.append("7. **禁止直接调用智能体**: 绝对不能直接调用智能体名称作为工具名")
            
            if "provide_final_answer" in tool_names:
                guidance.append("8. **提供最终答案**: 任务完成后使用 `provide_final_answer`")
            
            return "\n".join(guidance)
        
        # 添加到协调器实例
        import types
        coordinator_instance.generate_robust_system_prompt = types.MethodType(generate_robust_system_prompt, coordinator_instance)
        coordinator_instance._build_tool_specific_guidance = types.MethodType(_build_tool_specific_guidance, coordinator_instance)
        
        self.logger.info("✅ 已应用健壮的System Prompt生成")
    
    def apply_all_fixes(self, coordinator_instance):
        """应用所有修复"""
        self.logger.info("🔧 开始应用所有修复...")
        
        self.apply_improved_tool_detection(coordinator_instance)
        self.apply_enhanced_tool_call_parsing(coordinator_instance)
        self.apply_better_error_handling(coordinator_instance)
        self.apply_robust_system_prompt_generation(coordinator_instance)
        
        self.logger.info("✅ 所有修复已应用完成")
        
        return {
            "fixes_applied": [
                "improved_tool_detection",
                "enhanced_tool_call_parsing", 
                "better_error_handling",
                "robust_system_prompt_generation"
            ],
            "status": "success"
        }


def create_fixed_coordinator_class():
    """创建修复后的协调器类"""
    
    class FixedLLMCoordinator:
        """修复后的LLM协调智能体"""
        
        def __init__(self, original_coordinator):
            """基于原有协调器创建修复版本"""
            self.__dict__.update(original_coordinator.__dict__)
            
            # 应用修复
            patch = CoordinatorFixPatch()
            patch.apply_all_fixes(self)
            
            self.logger.info("🚀 修复后的协调智能体初始化完成")
        
        def get_fix_status(self) -> Dict[str, Any]:
            """获取修复状态"""
            return {
                "fixes_applied": True,
                "version": "fixed_v1.0",
                "improvements": [
                    "更robust的工具调用检测",
                    "增强的JSON解析能力",
                    "更好的错误恢复机制",
                    "动态System Prompt生成",
                    "多重试策略"
                ]
            }
    
    return FixedLLMCoordinator


# 使用示例
def demonstrate_fix_application():
    """演示修复应用过程"""
    
    # 模拟原有协调器
    class MockOriginalCoordinator:
        def __init__(self):
            self.logger = logging.getLogger(__name__)
            self.registered_agents = {}
            self.available_tools = {}
        
        def _has_executed_tools(self, result: str) -> bool:
            # 原有的简单检测逻辑
            return result.strip().startswith('{')
        
        async def coordinate_task(self, user_request: str, **kwargs):
            # 原有的协调逻辑（简化版）
            return {"success": False, "error": "原始逻辑存在问题"}
    
    # 创建原有协调器实例
    original = MockOriginalCoordinator()
    
    # 应用修复
    patch = CoordinatorFixPatch()
    fix_result = patch.apply_all_fixes(original)
    
    print("修复应用结果:")
    print(json.dumps(fix_result, indent=2, ensure_ascii=False))
    
    # 测试修复后的功能
    test_cases = [
        '{"tool_calls": [{"tool_name": "test", "parameters": {}}]}',
        '```json\n{"tool_calls": [{"tool_name": "test", "parameters": {}}]}\n```',
        '这是一个包含```json\n{"tool_calls": [{"tool_name": "test", "parameters": {}}]}\n```的响应',
        'invalid response'
    ]
    
    print("\n工具检测测试:")
    for i, test_case in enumerate(test_cases):
        result = original._has_executed_tools(test_case)
        print(f"测试{i+1}: {result} - {test_case[:50]}...")

if __name__ == "__main__":
    demonstrate_fix_application()