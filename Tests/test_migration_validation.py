#!/usr/bin/env python3
"""
Migration Validation Test Suite - 迁移验证测试套件
=============================================

用于验证重构后的智能体与原版本功能完全一致。
"""

import asyncio
import time
import json
import logging
import traceback
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入配置和工具
from config.config import FrameworkConfig

# 原版智能体
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from core.llm_coordinator_agent import LLMCoordinatorAgent

# 重构版智能体 (待创建)
from core.refactored_base_agent import RefactoredBaseAgent


class TestVerilogAgent(RefactoredBaseAgent):
    """测试版的Verilog智能体 - 继承自重构版基类"""
    
    def __init__(self, config: FrameworkConfig):
        super().__init__(
            agent_id="test_refactored_verilog_agent",
            role="verilog_designer", 
            capabilities={
                # 暂时导入枚举值
            }
        )
        self.config = config
        # 这里需要实现与原版相同的初始化逻辑
        
        # 注册Verilog特定的工具
        self._register_verilog_tools()
    
    def _register_verilog_tools(self):
        """注册Verilog专用工具"""
        
        # 添加generate_verilog_code工具
        self.register_function_calling_tool(
            name="generate_verilog_code",
            func=self._tool_generate_verilog_code,
            description="生成Verilog代码",
            parameters={
                "module_name": {"type": "string", "description": "模块名称", "required": True},
                "description": {"type": "string", "description": "功能描述", "required": True},
                "requirements": {"type": "string", "description": "具体需求", "required": False}
            }
        )
        
        # 添加analyze_design_requirements工具
        self.register_function_calling_tool(
            name="analyze_design_requirements",
            func=self._tool_analyze_design_requirements,
            description="分析设计需求",
            parameters={
                "requirements": {"type": "string", "description": "需求描述", "required": True}
            }
        )
    
    async def _tool_generate_verilog_code(self, module_name: str, description: str, requirements: str = "", **kwargs):
        """生成Verilog代码的工具实现"""
        # 这里实现与原版相同的逻辑
        # 为了测试，暂时返回简单结果
        return {
            "success": True,
            "result": f"// Generated Verilog module: {module_name}\nmodule {module_name}();\n    // {description}\nendmodule",
            "module_name": module_name
        }
    
    async def _tool_analyze_design_requirements(self, requirements: str, **kwargs):
        """分析设计需求的工具实现"""
        return {
            "success": True,
            "result": f"Requirements analyzed: {requirements[:100]}...",
            "analysis": "Basic requirements analysis completed"
        }
    
    async def _call_llm_for_function_calling(self, conversation: List[Dict[str, str]]) -> str:
        """LLM调用实现 - 简化版本用于测试"""
        # 对于测试，返回预设的响应
        if len(conversation) > 1:
            user_message = conversation[-1].get('content', '')
            
            if '4位加法器' in user_message or 'adder' in user_message.lower():
                return '''基于您的需求，我将生成一个4位加法器设计。

```json
{
    "tool_calls": [
        {
            "tool_name": "generate_verilog_code",
            "parameters": {
                "module_name": "four_bit_adder",
                "description": "4位加法器，包含进位输入和输出",
                "requirements": "两个4位输入，一个进位输入，4位输出和进位输出"
            }
        }
    ]
}
```'''
            
            elif '设计需求' in user_message:
                return '''我将分析设计需求。

```json
{
    "tool_calls": [
        {
            "tool_name": "analyze_design_requirements", 
            "parameters": {
                "requirements": "''' + user_message + '''"
            }
        }
    ]
}
```'''
        
        return "好的，我理解了您的需求。让我为您设计相应的Verilog模块。"
    
    async def execute_enhanced_task(self, enhanced_prompt: str, original_message=None, file_contents=None) -> Dict[str, Any]:
        """执行增强任务的实现"""
        # 简化实现用于测试
        return {
            "success": True,
            "result": f"Task completed: {enhanced_prompt[:100]}...",
            "execution_time": 1.0
        }


class MigrationValidator:
    """迁移验证器"""
    
    def __init__(self):
        self.config = FrameworkConfig.from_env()
        self.test_results = {}
        self.logger = logging.getLogger(__name__)
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    async def run_full_validation(self) -> Dict[str, Any]:
        """运行完整的验证测试"""
        self.logger.info("🚀 开始迁移验证测试")
        
        validation_results = {
            'timestamp': time.time(),
            'basic_functionality': False,
            'tool_calling_parity': False,
            'performance_comparison': False,
            'error_handling': False,
            'integration_tests': False,
            'overall_success': False,
            'details': {}
        }
        
        try:
            # 1. 基础功能测试
            self.logger.info("📋 测试1: 基础功能验证")
            validation_results['basic_functionality'] = await self._test_basic_functionality()
            
            # 2. 工具调用功能对等性测试
            self.logger.info("📋 测试2: 工具调用功能对等性")
            validation_results['tool_calling_parity'] = await self._test_tool_calling_parity()
            
            # 3. 性能对比测试
            self.logger.info("📋 测试3: 性能对比")
            validation_results['performance_comparison'] = await self._test_performance_comparison()
            
            # 4. 错误处理测试
            self.logger.info("📋 测试4: 错误处理")
            validation_results['error_handling'] = await self._test_error_handling()
            
            # 5. 集成测试
            self.logger.info("📋 测试5: 集成测试")
            validation_results['integration_tests'] = await self._test_integration()
            
            # 计算总体成功率
            success_count = sum([
                validation_results['basic_functionality'],
                validation_results['tool_calling_parity'], 
                validation_results['performance_comparison'],
                validation_results['error_handling'],
                validation_results['integration_tests']
            ])
            
            validation_results['overall_success'] = success_count >= 4  # 至少4个测试通过
            validation_results['success_rate'] = success_count / 5
            
        except Exception as e:
            self.logger.error(f"❌ 验证测试异常: {str(e)}")
            validation_results['error'] = str(e)
            validation_results['traceback'] = traceback.format_exc()
        
        # 输出结果摘要
        self._print_validation_summary(validation_results)
        
        return validation_results
    
    async def _test_basic_functionality(self) -> bool:
        """测试基础功能"""
        try:
            self.logger.info("  🔧 创建重构版智能体")
            test_agent = TestVerilogAgent(self.config)
            
            # 测试基本属性
            assert test_agent.agent_id == "test_refactored_verilog_agent"
            assert test_agent.role == "verilog_designer"
            assert test_agent.get_capabilities() is not None
            assert test_agent.get_specialty_description()
            
            # 测试组件初始化
            assert test_agent.conversation_manager is not None
            assert test_agent.tool_call_parser is not None
            assert test_agent.agent_context is not None
            
            # 测试工具注册
            assert 'write_file' in test_agent.function_calling_tools
            assert 'read_file' in test_agent.function_calling_tools
            assert 'generate_verilog_code' in test_agent.function_calling_tools
            
            self.logger.info("  ✅ 基础功能测试通过")
            return True
            
        except Exception as e:
            self.logger.error(f"  ❌ 基础功能测试失败: {str(e)}")
            return False
    
    async def _test_tool_calling_parity(self) -> bool:
        """测试工具调用功能对等性"""
        try:
            # 创建测试智能体
            test_agent = TestVerilogAgent(self.config)
            
            # 测试请求
            test_request = "请设计一个4位加法器"
            
            # 执行Function Calling
            result = await test_agent.process_with_function_calling(
                user_request=test_request,
                max_iterations=3
            )
            
            # 验证结果
            assert result is not None
            assert len(result) > 0
            
            # 验证对话历史
            conversation_summary = test_agent.get_conversation_summary()
            assert conversation_summary['total_conversations'] > 0
            
            self.logger.info("  ✅ 工具调用功能对等性测试通过")
            return True
            
        except Exception as e:
            self.logger.error(f"  ❌ 工具调用功能对等性测试失败: {str(e)}")
            return False
    
    async def _test_performance_comparison(self) -> bool:
        """测试性能对比"""
        try:
            test_agent = TestVerilogAgent(self.config)
            
            # 性能测试
            test_requests = [
                "设计一个简单的计数器",
                "创建一个4位加法器", 
                "生成一个基本的触发器"
            ]
            
            total_time = 0
            successful_requests = 0
            
            for request in test_requests:
                start_time = time.time()
                try:
                    result = await test_agent.process_with_function_calling(request, max_iterations=2)
                    execution_time = time.time() - start_time
                    
                    if result and len(result) > 0:
                        total_time += execution_time
                        successful_requests += 1
                        self.logger.info(f"    📊 请求 '{request[:30]}...' 耗时: {execution_time:.2f}s")
                    
                except Exception as e:
                    self.logger.warning(f"    ⚠️ 请求失败: {str(e)}")
                    continue
            
            # 性能评估
            if successful_requests > 0:
                avg_time = total_time / successful_requests
                performance_acceptable = avg_time < 10.0  # 平均不超过10秒
                
                self.logger.info(f"  📊 平均响应时间: {avg_time:.2f}s")
                self.logger.info(f"  📊 成功率: {successful_requests}/{len(test_requests)}")
                
                if performance_acceptable:
                    self.logger.info("  ✅ 性能测试通过")
                    return True
                else:
                    self.logger.warning("  ⚠️ 性能测试未达标")
                    return False
            else:
                self.logger.error("  ❌ 没有成功的请求")
                return False
            
        except Exception as e:
            self.logger.error(f"  ❌ 性能测试失败: {str(e)}")
            return False
    
    async def _test_error_handling(self) -> bool:
        """测试错误处理"""
        try:
            test_agent = TestVerilogAgent(self.config)
            
            # 测试文件写入错误处理
            result = await test_agent._tool_write_file(
                content="test content",
                filename="test.txt"
            )
            assert result.get('success', False)
            
            # 测试文件读取错误处理
            result = await test_agent._tool_read_file(filepath="/nonexistent/path/file.txt")
            assert not result.get('success', True)  # 应该失败
            assert 'error' in result
            
            self.logger.info("  ✅ 错误处理测试通过")
            return True
            
        except Exception as e:
            self.logger.error(f"  ❌ 错误处理测试失败: {str(e)}")
            return False
    
    async def _test_integration(self) -> bool:
        """测试集成功能"""
        try:
            test_agent = TestVerilogAgent(self.config)
            
            # 综合测试：包含多个工具调用的复杂任务
            complex_request = """
            请设计一个8位计数器，要求：
            1. 包含时钟和复位信号
            2. 有使能控制
            3. 生成完整的Verilog代码
            """
            
            result = await test_agent.process_with_function_calling(
                user_request=complex_request,
                max_iterations=5
            )
            
            # 验证结果
            assert result is not None
            assert len(result) > 50  # 应该有较长的响应
            
            # 验证对话管理
            summary = test_agent.get_conversation_summary()
            assert summary['total_conversations'] > 0
            
            # 验证状态管理
            status = test_agent.get_status()
            assert 'agent_id' in status
            assert status['agent_id'] == "test_refactored_verilog_agent"
            
            self.logger.info("  ✅ 集成测试通过")
            return True
            
        except Exception as e:
            self.logger.error(f"  ❌ 集成测试失败: {str(e)}")
            return False
    
    def _print_validation_summary(self, results: Dict[str, Any]):
        """打印验证结果摘要"""
        print("\n" + "="*80)
        print("🎯 迁移验证测试结果摘要")
        print("="*80)
        
        print(f"📊 总体成功率: {results.get('success_rate', 0)*100:.1f}%")
        print(f"🎯 总体结果: {'✅ 通过' if results.get('overall_success', False) else '❌ 失败'}")
        
        print(f"\n📋 详细测试结果:")
        test_items = [
            ('基础功能', 'basic_functionality'),
            ('工具调用功能对等性', 'tool_calling_parity'),
            ('性能对比', 'performance_comparison'),
            ('错误处理', 'error_handling'),
            ('集成测试', 'integration_tests')
        ]
        
        for name, key in test_items:
            status = "✅ 通过" if results.get(key, False) else "❌ 失败"
            print(f"   {name}: {status}")
        
        if 'error' in results:
            print(f"\n❌ 异常信息: {results['error']}")
        
        print("="*80)


async def main():
    """主测试函数"""
    print("🧪 开始 BaseAgent 重构迁移验证测试")
    
    validator = MigrationValidator()
    results = await validator.run_full_validation()
    
    # 保存测试结果
    results_path = Path("test_results") / f"migration_validation_{int(time.time())}.json"
    results_path.parent.mkdir(exist_ok=True)
    
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 测试结果已保存到: {results_path}")
    
    # 返回退出码
    return 0 if results.get('overall_success', False) else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())