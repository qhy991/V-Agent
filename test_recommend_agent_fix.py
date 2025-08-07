#!/usr/bin/env python3
"""
推荐代理工具调用验证测试

验证LLM协调智能体是否正确调用推荐代理工具
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入必要的模块
from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from config.config import FrameworkConfig


class RecommendAgentTest:
    """推荐代理工具调用测试类"""
    
    def __init__(self):
        self.config = FrameworkConfig()
        self.coordinator = None
        self.verilog_agent = None
        self.code_reviewer_agent = None
        
    async def setup(self):
        """设置测试环境"""
        logger.info("🔧 设置测试环境...")
        
        # 创建协调智能体
        self.coordinator = LLMCoordinatorAgent(self.config)
        
        # 创建并注册工作智能体
        self.verilog_agent = EnhancedRealVerilogAgent(self.config)
        self.code_reviewer_agent = EnhancedRealCodeReviewAgent(self.config)
        
        await self.coordinator.register_agent(self.verilog_agent)
        await self.coordinator.register_agent(self.code_reviewer_agent)
        
        logger.info("✅ 测试环境设置完成")
        
    async def test_recommend_agent_tool(self):
        """测试推荐代理工具"""
        logger.info("🧪 测试推荐代理工具...")
        
        # 测试用例
        test_cases = [
            {
                "name": "设计任务",
                "task_type": "design",
                "task_description": "设计一个4位加法器模块",
                "priority": "medium"
            },
            {
                "name": "验证任务",
                "task_type": "verification",
                "task_description": "验证计数器模块的功能正确性",
                "priority": "high"
            },
            {
                "name": "分析任务",
                "task_type": "analysis",
                "task_description": "分析ALU模块的性能指标",
                "priority": "low"
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            logger.info(f"📋 测试用例: {test_case['name']}")
            
            try:
                # 调用推荐代理工具
                result = await self.coordinator._tool_recommend_agent(
                    task_type=test_case["task_type"],
                    task_description=test_case["task_description"],
                    priority=test_case["priority"]
                )
                
                # 验证结果
                if result.get("success"):
                    recommended_agent = result.get("recommended_agent")
                    score = result.get("score", 0)
                    reasoning = result.get("reasoning", "")
                    
                    logger.info(f"✅ 推荐成功: {recommended_agent} (评分: {score:.1f})")
                    logger.info(f"📝 推荐理由: {reasoning}")
                    
                    results.append({
                        "test_case": test_case["name"],
                        "success": True,
                        "recommended_agent": recommended_agent,
                        "score": score,
                        "reasoning": reasoning
                    })
                else:
                    logger.error(f"❌ 推荐失败: {result.get('error')}")
                    results.append({
                        "test_case": test_case["name"],
                        "success": False,
                        "error": result.get("error")
                    })
                    
            except Exception as e:
                logger.error(f"❌ 测试异常: {str(e)}")
                results.append({
                    "test_case": test_case["name"],
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    async def test_coordination_flow(self):
        """测试完整协调流程"""
        logger.info("🔄 测试完整协调流程...")
        
        # 测试用户请求
        user_request = "设计一个8位二进制计数器，包含时钟、复位和使能信号"
        
        try:
            # 创建任务上下文
            from core.llm_coordinator_agent import TaskContext
            task_context = TaskContext(
                task_id="test_task_001",
                original_request=user_request
            )
            
            # 1. 识别任务类型
            logger.info("🔍 步骤1: 识别任务类型")
            task_type_result = await self.coordinator._tool_identify_task_type(user_request)
            
            if not task_type_result.get("success"):
                logger.error(f"❌ 任务类型识别失败: {task_type_result.get('error')}")
                return False
            
            task_type = task_type_result.get("task_type", "composite")
            logger.info(f"✅ 识别任务类型: {task_type}")
            
            # 2. 推荐智能体
            logger.info("🤖 步骤2: 推荐智能体")
            recommend_result = await self.coordinator._tool_recommend_agent(
                task_type=task_type,
                task_description=user_request,
                priority="medium"
            )
            
            if not recommend_result.get("success"):
                logger.error(f"❌ 智能体推荐失败: {recommend_result.get('error')}")
                return False
            
            recommended_agent = recommend_result.get("recommended_agent")
            score = recommend_result.get("score", 0)
            logger.info(f"✅ 推荐智能体: {recommended_agent} (评分: {score:.1f})")
            
            # 3. 分配任务
            logger.info("📋 步骤3: 分配任务")
            assign_result = await self.coordinator._tool_assign_task_to_agent(
                agent_id=recommended_agent,
                task_description=user_request,
                task_type=task_type,
                priority="medium"
            )
            
            if not assign_result.get("success"):
                logger.error(f"❌ 任务分配失败: {assign_result.get('error')}")
                return False
            
            logger.info(f"✅ 任务分配成功: {recommended_agent}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 协调流程测试异常: {str(e)}")
            return False
    
    async def test_force_assignment(self):
        """测试强制分配机制"""
        logger.info("🚨 测试强制分配机制...")
        
        user_request = "设计一个16位ALU模块"
        
        try:
            # 创建任务上下文
            from core.llm_coordinator_agent import TaskContext
            task_context = TaskContext(
                task_id="test_force_task_001",
                original_request=user_request
            )
            
            # 调用强制分配
            result = await self.coordinator._force_assign_task(user_request, task_context)
            
            if result.get("success"):
                agent_id = result.get("agent_id")
                logger.info(f"✅ 强制分配成功: {agent_id}")
                
                # 检查对话历史
                conversation_summary = task_context.get_conversation_summary()
                logger.info(f"📝 对话历史: {conversation_summary}")
                
                return True
            else:
                logger.error(f"❌ 强制分配失败: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 强制分配测试异常: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始运行推荐代理工具测试...")
        
        # 设置环境
        await self.setup()
        
        # 测试结果
        test_results = {
            "recommend_agent_tool": None,
            "coordination_flow": None,
            "force_assignment": None
        }
        
        # 1. 测试推荐代理工具
        logger.info("\n" + "="*50)
        logger.info("测试1: 推荐代理工具")
        logger.info("="*50)
        test_results["recommend_agent_tool"] = await self.test_recommend_agent_tool()
        
        # 2. 测试完整协调流程
        logger.info("\n" + "="*50)
        logger.info("测试2: 完整协调流程")
        logger.info("="*50)
        test_results["coordination_flow"] = await self.test_coordination_flow()
        
        # 3. 测试强制分配机制
        logger.info("\n" + "="*50)
        logger.info("测试3: 强制分配机制")
        logger.info("="*50)
        test_results["force_assignment"] = await self.test_force_assignment()
        
        # 生成测试报告
        self.generate_test_report(test_results)
        
        return test_results
    
    def generate_test_report(self, results: Dict[str, Any]):
        """生成测试报告"""
        logger.info("\n" + "="*60)
        logger.info("📊 测试报告")
        logger.info("="*60)
        
        # 推荐代理工具测试结果
        if results["recommend_agent_tool"]:
            logger.info("\n🔧 推荐代理工具测试:")
            success_count = sum(1 for r in results["recommend_agent_tool"] if r.get("success"))
            total_count = len(results["recommend_agent_tool"])
            logger.info(f"   成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
            
            for result in results["recommend_agent_tool"]:
                if result.get("success"):
                    logger.info(f"   ✅ {result['test_case']}: {result['recommended_agent']} (评分: {result['score']:.1f})")
                else:
                    logger.info(f"   ❌ {result['test_case']}: {result.get('error')}")
        
        # 协调流程测试结果
        logger.info(f"\n🔄 协调流程测试:")
        if results["coordination_flow"]:
            logger.info("   ✅ 协调流程测试通过")
        else:
            logger.info("   ❌ 协调流程测试失败")
        
        # 强制分配测试结果
        logger.info(f"\n🚨 强制分配测试:")
        if results["force_assignment"]:
            logger.info("   ✅ 强制分配测试通过")
        else:
            logger.info("   ❌ 强制分配测试失败")
        
        # 总体评估
        overall_success = (
            results["recommend_agent_tool"] and 
            results["coordination_flow"] and 
            results["force_assignment"]
        )
        
        logger.info(f"\n🎯 总体评估:")
        if overall_success:
            logger.info("   ✅ 所有测试通过 - 推荐代理工具调用正常")
        else:
            logger.info("   ❌ 部分测试失败 - 需要进一步调试")


async def main():
    """主函数"""
    test = RecommendAgentTest()
    await test.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main()) 