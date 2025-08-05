#!/usr/bin/env python3
"""
系统提示词传递验证测试
验证LLM协调智能体的系统提示词是否正确传递给LLM
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.llm_coordinator_agent import LLMCoordinatorAgent
from core.schema_system.enhanced_base_agent import EnhancedBaseAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from core.enhanced_logging_config import setup_enhanced_logging

class SystemPromptVerificationTest:
    """系统提示词验证测试类"""
    
    def __init__(self):
        self.config = FrameworkConfig.from_env()
        self.logger = logging.getLogger(__name__)
        self.test_results = []
        
    async def setup_agents(self):
        """设置智能体"""
        self.logger.info("🔧 设置智能体...")
        
        # 创建协调智能体
        self.coordinator = LLMCoordinatorAgent(self.config)
        
        # 创建其他智能体
        self.verilog_agent = EnhancedRealVerilogAgent(self.config)
        self.code_review_agent = EnhancedRealCodeReviewAgent(self.config)
        
        # 注册智能体
        await self.coordinator.register_agent(self.verilog_agent)
        await self.coordinator.register_agent(self.code_review_agent)
        
        self.logger.info("✅ 智能体设置完成")
    
    def get_system_prompt(self):
        """获取当前的系统提示词"""
        return self.coordinator._build_enhanced_system_prompt()
    
    async def test_system_prompt_injection(self):
        """测试系统提示词注入"""
        self.logger.info("🧪 测试系统提示词注入...")
        
        # 获取系统提示词
        system_prompt = self.get_system_prompt()
        
        # 检查系统提示词的关键内容
        checks = {
            "包含强制规则": "禁止直接回答" in system_prompt,
            "包含工具调用格式": "tool_calls" in system_prompt,
            "包含工具列表": "identify_task_type" in system_prompt,
            "包含智能体调用示例": "assign_task_to_agent" in system_prompt,
            "包含禁止描述性文本": "禁止生成描述性文本" in system_prompt,
            "包含重要提醒": "重要提醒" in system_prompt
        }
        
        self.logger.info("📋 系统提示词检查结果:")
        for check_name, result in checks.items():
            status = "✅" if result else "❌"
            self.logger.info(f"  {status} {check_name}: {result}")
        
        # 记录系统提示词长度
        prompt_length = len(system_prompt)
        self.logger.info(f"📏 系统提示词长度: {prompt_length} 字符")
        
        # 保存系统提示词到文件
        prompt_file = f"system_prompt_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write("=== 系统提示词内容 ===\n")
            f.write(system_prompt)
            f.write("\n\n=== 检查结果 ===\n")
            for check_name, result in checks.items():
                f.write(f"{check_name}: {result}\n")
        
        self.logger.info(f"💾 系统提示词已保存到: {prompt_file}")
        
        return {
            "system_prompt": system_prompt,
            "checks": checks,
            "prompt_length": prompt_length,
            "prompt_file": prompt_file
        }
    
    async def test_llm_response_with_system_prompt(self):
        """测试LLM在系统提示词下的响应"""
        self.logger.info("🧪 测试LLM响应（带系统提示词）...")
        
        # 构建测试对话
        conversation = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": "请设计一个4位计数器模块"}
        ]
        
        try:
            # 调用LLM
            response = await self.coordinator._call_llm_for_function_calling(conversation)
            
            # 分析响应
            analysis = self.analyze_llm_response(response)
            
            self.logger.info("📊 LLM响应分析结果:")
            for key, value in analysis.items():
                self.logger.info(f"  {key}: {value}")
            
            return {
                "response": response,
                "analysis": analysis
            }
            
        except Exception as e:
            self.logger.error(f"❌ LLM调用失败: {str(e)}")
            return {
                "error": str(e),
                "analysis": {}
            }
    
    def analyze_llm_response(self, response: str) -> dict:
        """分析LLM响应"""
        analysis = {
            "response_length": len(response),
            "is_json_format": False,
            "contains_tool_calls": False,
            "contains_descriptive_text": False,
            "starts_with_json": False,
            "has_valid_tool_structure": False
        }
        
        # 检查是否以JSON格式开始
        response_trimmed = response.strip()
        analysis["starts_with_json"] = response_trimmed.startswith('{')
        
        # 检查是否包含描述性文本
        descriptive_indicators = [
            "###", "---", "####", "**", "用户需求", "任务分析", 
            "执行策略", "关键目标", "正在调用", "等待智能体"
        ]
        analysis["contains_descriptive_text"] = any(
            indicator in response for indicator in descriptive_indicators
        )
        
        # 尝试解析JSON
        try:
            if response_trimmed.startswith('{'):
                data = json.loads(response_trimmed)
                analysis["is_json_format"] = True
                analysis["contains_tool_calls"] = "tool_calls" in data
                
                if "tool_calls" in data and isinstance(data["tool_calls"], list):
                    tool_calls = data["tool_calls"]
                    if tool_calls and "tool_name" in tool_calls[0]:
                        analysis["has_valid_tool_structure"] = True
        except json.JSONDecodeError:
            pass
        
        return analysis
    
    async def test_coordination_without_self_continuation(self):
        """测试协调任务（禁用自我继续）"""
        self.logger.info("🧪 测试协调任务（禁用自我继续）...")
        
        try:
            result = await self.coordinator.coordinate_task(
                user_request="请设计一个4位计数器模块",
                conversation_id="test_system_prompt_verification",
                max_iterations=1,  # 只执行一次
                external_testbench_path=None
            )
            
            # 检查结果
            coordination_result = result.get("coordination_result", "")
            analysis = self.analyze_llm_response(coordination_result)
            
            self.logger.info("📊 协调任务结果分析:")
            for key, value in analysis.items():
                self.logger.info(f"  {key}: {value}")
            
            return {
                "result": result,
                "analysis": analysis
            }
            
        except Exception as e:
            self.logger.error(f"❌ 协调任务失败: {str(e)}")
            return {
                "error": str(e),
                "analysis": {}
            }
    
    async def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("🚀 开始系统提示词验证测试")
        
        try:
            # 设置智能体
            await self.setup_agents()
            
            # 测试1: 系统提示词注入
            test1_result = await self.test_system_prompt_injection()
            self.test_results.append(("系统提示词注入", test1_result))
            
            # 测试2: LLM响应测试
            test2_result = await self.test_llm_response_with_system_prompt()
            self.test_results.append(("LLM响应测试", test2_result))
            
            # 测试3: 协调任务测试
            test3_result = await self.test_coordination_without_self_continuation()
            self.test_results.append(("协调任务测试", test3_result))
            
            # 生成测试报告
            self.generate_test_report()
            
        except Exception as e:
            self.logger.error(f"❌ 测试执行失败: {str(e)}")
            raise
    
    def generate_test_report(self):
        """生成测试报告"""
        self.logger.info("📋 生成测试报告...")
        
        report_file = f"system_prompt_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 系统提示词验证测试报告\n\n")
            f.write(f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for test_name, result in self.test_results:
                f.write(f"## {test_name}\n\n")
                
                if "error" in result:
                    f.write(f"❌ **错误**: {result['error']}\n\n")
                else:
                    if "checks" in result:
                        f.write("### 系统提示词检查\n\n")
                        for check_name, check_result in result["checks"].items():
                            status = "✅" if check_result else "❌"
                            f.write(f"- {status} {check_name}\n")
                        f.write(f"\n**提示词长度**: {result.get('prompt_length', 0)} 字符\n\n")
                    
                    if "analysis" in result:
                        f.write("### LLM响应分析\n\n")
                        for key, value in result["analysis"].items():
                            f.write(f"- **{key}**: {value}\n")
                        f.write("\n")
                    
                    if "response" in result:
                        f.write("### LLM响应内容\n\n")
                        f.write("```\n")
                        f.write(result["response"][:1000])  # 只显示前1000字符
                        if len(result["response"]) > 1000:
                            f.write("\n... (内容已截断)")
                        f.write("\n```\n\n")
        
        self.logger.info(f"📄 测试报告已生成: {report_file}")
        
        # 输出关键发现
        self.logger.info("\n🔍 关键发现:")
        for test_name, result in self.test_results:
            if "error" not in result:
                if "checks" in result:
                    all_checks_passed = all(result["checks"].values())
                    self.logger.info(f"  {test_name}: {'✅ 通过' if all_checks_passed else '❌ 失败'}")
                
                if "analysis" in result:
                    analysis = result["analysis"]
                    if analysis.get("has_valid_tool_structure"):
                        self.logger.info(f"  {test_name}: ✅ 生成了有效的工具调用")
                    elif analysis.get("contains_descriptive_text"):
                        self.logger.info(f"  {test_name}: ❌ 生成了描述性文本而非工具调用")

async def main():
    """主函数"""
    # 设置日志
    setup_enhanced_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🧠 系统提示词传递验证测试")
    logger.info("=" * 60)
    
    # 创建测试实例
    test = SystemPromptVerificationTest()
    
    try:
        # 运行测试
        await test.run_all_tests()
        logger.info("✅ 所有测试完成")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 