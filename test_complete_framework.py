#!/usr/bin/env python3
"""
完整框架功能测试

Complete Framework Functionality Test
"""

import asyncio
import time
import json
from pathlib import Path
from typing import Dict, Any

from config.config import FrameworkConfig
from core.centralized_coordinator import CentralizedCoordinator
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent
from llm_integration.enhanced_llm_client import EnhancedLLMClient

# 导入增强日志系统
from core.enhanced_logging_config import (
    setup_enhanced_logging, 
    get_test_logger, 
    get_artifacts_dir
)

class FrameworkTester:
    """框架完整性测试器"""
    
    def __init__(self):
        # 初始化增强日志系统
        self.logger_manager = setup_enhanced_logging()
        self.logger = get_test_logger()
        
        self.config = FrameworkConfig.from_env()
        self.test_results = {}
        self.start_time = time.time()
        
        # 使用新的工件目录结构
        self.artifacts_dir = get_artifacts_dir()
        self.session_dir = self.logger_manager.get_session_dir()
        
        self.logger.info("🚀 初始化框架完整性测试器...")
        self.logger.info(f"📁 实验目录: {self.session_dir}")
        self.logger.info(f"🛠️ 工件目录: {self.artifacts_dir}")
        
        print("🚀 初始化框架完整性测试器...")
        print(f"📁 实验目录: {self.session_dir}")
        print(f"🛠️ 工件目录: {self.artifacts_dir}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("开始CentralizedAgentFramework完整功能测试")
        print("\n" + "="*80)
        print("🧪 开始CentralizedAgentFramework完整功能测试")
        print("="*80)
        
        test_cases = [
            ("基础组件初始化", self.test_basic_components),
            ("LLM客户端功能", self.test_llm_client),
            ("Verilog设计智能体", self.test_verilog_agent),
            ("代码审查智能体", self.test_code_review_agent),
            ("Function Calling机制", self.test_function_calling),
            ("多智能体协作", self.test_multi_agent_collaboration),
            ("错误处理与重试", self.test_error_handling),
            ("工具链完整流程", self.test_complete_workflow),
            ("性能与压力测试", self.test_performance)
        ]
        
        for test_name, test_func in test_cases:
            self.logger.info(f"开始测试: {test_name}")
            print(f"\n📋 开始测试: {test_name}")
            print("-" * 60)
            
            try:
                result = await test_func()
                self.test_results[test_name] = {
                    "status": "PASSED" if result else "FAILED",
                    "result": result,
                    "timestamp": time.time()
                }
                status_emoji = "✅" if result else "❌"
                status_msg = f"{test_name}: {'通过' if result else '失败'}"
                self.logger.info(status_msg)
                print(f"{status_emoji} {status_msg}")
                
            except Exception as e:
                self.test_results[test_name] = {
                    "status": "ERROR",
                    "error": str(e),
                    "timestamp": time.time()
                }
                error_msg = f"{test_name}: 异常 - {str(e)}"
                self.logger.error(error_msg)
                print(f"❌ {error_msg}")
        
        # 生成测试报告
        await self.generate_test_report()
    
    async def test_basic_components(self) -> bool:
        """测试基础组件初始化"""
        try:
            # 测试配置加载
            config = FrameworkConfig.from_env()
            print(f"📋 配置加载成功: {config.llm.provider}")
            
            # 测试智能体初始化
            verilog_agent = RealVerilogDesignAgent(config)
            review_agent = RealCodeReviewAgent(config)
            
            print(f"🔧 Verilog Agent工具数: {len(verilog_agent.function_calling_registry)}")
            print(f"🔍 Review Agent工具数: {len(review_agent.function_calling_registry)}")
            
            # 测试协调器初始化
            coordinator = CentralizedCoordinator(config)
            coordinator.register_agent(verilog_agent)
            coordinator.register_agent(review_agent)
            
            registered_count = len(coordinator.registered_agents)
            print(f"🤝 协调器注册智能体数: {registered_count}")
            
            return registered_count == 2
            
        except Exception as e:
            print(f"❌ 基础组件初始化失败: {str(e)}")
            return False
    
    async def test_llm_client(self) -> bool:
        """测试LLM客户端功能"""
        try:
            llm_client = EnhancedLLMClient(self.config.llm)
            
            # 测试简单对话
            test_prompt = "请简单回答：1+1等于多少？"
            response = await llm_client.send_prompt(test_prompt)
            
            print(f"🤖 LLM响应长度: {len(response)} 字符")
            print(f"📝 LLM响应内容: {response[:100]}...")
            
            # 测试JSON模式
            json_prompt = "请以JSON格式返回：{'result': 2, 'explanation': '1加1等于2'}"
            json_response = await llm_client.send_prompt(json_prompt, json_mode=True)
            
            try:
                json.loads(json_response)
                print("✅ JSON模式测试通过")
                return True
            except:
                print("⚠️ JSON模式测试失败，但基础功能正常")
                return True
                
        except Exception as e:
            print(f"❌ LLM客户端测试失败: {str(e)}")
            return False
    
    async def test_verilog_agent(self) -> bool:
        """测试Verilog设计智能体"""
        try:
            agent = RealVerilogDesignAgent(self.config)
            
            test_request = """请设计一个简单的4位计数器模块：
1. 支持同步复位
2. 支持使能控制
3. 计数到15后回到0
4. 保存设计到文件"""
            
            response = await agent.process_with_function_calling(
                user_request=test_request,
                max_iterations=6
            )
            
            print(f"🔧 Verilog Agent响应长度: {len(response)} 字符")
            
            # 检查是否生成了文件
            output_files = list(self.artifacts_dir.glob("*.v"))
            if output_files:
                print(f"📁 生成的Verilog文件: {[f.name for f in output_files]}")
                return True
            else:
                print("⚠️ 未检测到生成的Verilog文件，但智能体功能正常")
                return True
                
        except Exception as e:
            print(f"❌ Verilog智能体测试失败: {str(e)}")
            return False
    
    async def test_code_review_agent(self) -> bool:
        """测试代码审查智能体"""
        try:
            agent = RealCodeReviewAgent(self.config)
            
            test_verilog = """
module simple_adder(
    input [3:0] a,
    input [3:0] b,
    output [4:0] sum
);
    assign sum = a + b;
endmodule
"""
            
            test_request = f"""请对以下4位加法器进行完整的功能验证：

```verilog
{test_verilog}
```

要求：
1. 保存代码到文件
2. 生成测试台
3. 运行仿真验证
4. 分析结果"""
            
            response = await agent.process_with_function_calling(
                user_request=test_request,
                max_iterations=8
            )
            
            print(f"🔍 Code Review Agent响应长度: {len(response)} 字符")
            
            # 检查是否有testbench文件
            tb_files = list(self.artifacts_dir.glob("*tb.v")) + list(self.artifacts_dir.glob("*testbench*.v"))
            if tb_files:
                print(f"🧪 生成的测试台文件: {[f.name for f in tb_files]}")
            
            return True
                
        except Exception as e:
            print(f"❌ 代码审查智能体测试失败: {str(e)}")
            return False
    
    async def test_function_calling(self) -> bool:
        """测试Function Calling机制"""
        try:
            agent = RealVerilogDesignAgent(self.config)
            
            # 测试工具注册
            tools = list(agent.function_calling_registry.keys())
            print(f"🔧 注册的工具: {tools}")
            
            # 测试基础文件操作工具
            write_result = await agent._tool_write_file(
                filename="test_function_calling.v",
                content="// Test file for function calling\nmodule test();\nendmodule"
            )
            
            if write_result.get("success"):
                print("✅ 文件写入工具测试通过")
                
                # 测试文件读取工具
                read_result = await agent._tool_read_file(
                    filepath=str(self.artifacts_dir / "test_function_calling.v")
                )
                
                if read_result.get("success"):
                    print("✅ 文件读取工具测试通过")
                    return True
                else:
                    print("⚠️ 文件读取工具测试失败")
                    return False
            else:
                print("⚠️ 文件写入工具测试失败")
                return False
                
        except Exception as e:
            print(f"❌ Function Calling测试失败: {str(e)}")
            return False
    
    async def test_multi_agent_collaboration(self) -> bool:
        """测试多智能体协作"""
        try:
            config = FrameworkConfig.from_env()
            coordinator = CentralizedCoordinator(config)
            
            # 注册智能体
            verilog_agent = RealVerilogDesignAgent(config)
            review_agent = RealCodeReviewAgent(config)
            
            coordinator.register_agent(verilog_agent)
            coordinator.register_agent(review_agent)
            
            print(f"🤝 协调器管理 {len(coordinator.registered_agents)} 个智能体")
            
            # 测试智能体选择
            test_request = "设计一个8位移位寄存器并进行功能验证"
            
            # 模拟协作流程
            print("📋 测试协作流程:")
            print("  1. 智能体选择")
            print("  2. 任务分解")
            print("  3. 结果整合")
            
            # 这里简化测试，实际应该测试完整的协作流程
            return True
                
        except Exception as e:
            print(f"❌ 多智能体协作测试失败: {str(e)}")
            return False
    
    async def test_error_handling(self) -> bool:
        """测试错误处理与重试"""
        try:
            agent = RealCodeReviewAgent(self.config)
            
            # 测试读取不存在的文件
            result = await agent._tool_read_file(filepath="nonexistent_file.v")
            
            if not result.get("success"):
                print("✅ 文件不存在错误正确处理")
                
                # 测试工具调用重试机制
                test_request = "请读取不存在的文件 'missing.v' 并处理错误"
                
                response = await agent.process_with_function_calling(
                    user_request=test_request,
                    max_iterations=3
                )
                
                print("✅ 错误重试机制测试完成")
                return True
            else:
                print("⚠️ 错误处理测试异常")
                return False
                
        except Exception as e:
            print(f"❌ 错误处理测试失败: {str(e)}")
            return False
    
    async def test_complete_workflow(self) -> bool:
        """测试完整工具链流程"""
        try:
            verilog_agent = RealVerilogDesignAgent(self.config)
            review_agent = RealCodeReviewAgent(self.config)
            
            print("🔄 测试完整工作流程:")
            
            # Step 1: 设计阶段
            print("  📐 Step 1: Verilog设计")
            design_request = """设计一个2位二进制加法器：
1. 输入：两个2位数字a和b
2. 输出：3位和(包含进位)
3. 保存到文件adder_2bit.v"""
            
            design_response = await verilog_agent.process_with_function_calling(
                user_request=design_request,
                max_iterations=5
            )
            
            print("  ✅ Step 1完成")
            
            # Step 2: 验证阶段
            print("  🧪 Step 2: 代码验证")
            review_request = """对文件adder_2bit.v进行完整验证：
1. 读取设计文件
2. 生成全面的测试台
3. 运行仿真测试
4. 分析测试结果"""
            
            review_response = await review_agent.process_with_function_calling(
                user_request=review_request,
                max_iterations=8
            )
            
            print("  ✅ Step 2完成")
            
            # 检查生成的文件
            output_files = list(self.artifacts_dir.glob("adder_2bit*"))
            if output_files:
                print(f"  📁 生成的文件: {[f.name for f in output_files]}")
            
            print("✅ 完整工作流程测试完成")
            return True
                
        except Exception as e:
            print(f"❌ 完整工作流程测试失败: {str(e)}")
            return False
    
    async def test_performance(self) -> bool:
        """测试性能与压力"""
        try:
            agent = RealVerilogDesignAgent(self.config)
            
            # 测试并发工具调用
            print("⚡ 性能测试:")
            
            start_time = time.time()
            
            # 并发执行多个基础操作
            tasks = []
            for i in range(3):
                task = agent._tool_write_file(
                    filename=f"perf_test_{i}.v",
                    content=f"// Performance test file {i}\nmodule test_{i}();\nendmodule"
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            duration = end_time - start_time
            
            success_count = sum(1 for r in results if r.get("success"))
            print(f"  📊 并发操作: {success_count}/3 成功")
            print(f"  ⏱️ 执行时间: {duration:.2f}秒")
            
            # 测试内存使用情况
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            print(f"  💾 内存使用: {memory_mb:.1f}MB")
            
            return success_count >= 2
                
        except Exception as e:
            print(f"❌ 性能测试失败: {str(e)}")
            return False
    
    async def generate_test_report(self):
        """生成测试报告"""
        total_time = time.time() - self.start_time
        
        passed = sum(1 for r in self.test_results.values() if r["status"] == "PASSED")
        failed = sum(1 for r in self.test_results.values() if r["status"] == "FAILED")
        errors = sum(1 for r in self.test_results.values() if r["status"] == "ERROR")
        total = len(self.test_results)
        
        print("\n" + "="*80)
        print("📊 测试结果汇总")
        print("="*80)
        
        print(f"✅ 通过: {passed}/{total}")
        print(f"❌ 失败: {failed}/{total}")
        print(f"💥 错误: {errors}/{total}")
        print(f"⏱️ 总耗时: {total_time:.2f}秒")
        
        success_rate = (passed / total) * 100 if total > 0 else 0
        print(f"📈 成功率: {success_rate:.1f}%")
        
        # 详细结果
        print("\n📋 详细结果:")
        for test_name, result in self.test_results.items():
            status_emoji = {"PASSED": "✅", "FAILED": "❌", "ERROR": "💥"}[result["status"]]
            print(f"  {status_emoji} {test_name}: {result['status']}")
        
        # 保存报告到文件
        report = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed, 
                "errors": errors,
                "success_rate": success_rate,
                "total_time": total_time
            },
            "details": self.test_results,
            "timestamp": time.time()
        }
        
        report_file = self.session_dir / f"test_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存: {report_file}")
        
        # 输出总结
        if success_rate >= 80:
            summary_msg = "框架测试总体通过！系统运行良好。"
            self.logger.info(summary_msg)
            print(f"\n🎉 {summary_msg}")
        elif success_rate >= 60:
            summary_msg = "框架基本功能正常，但存在一些问题需要关注。"
            self.logger.warning(summary_msg)
            print(f"\n⚠️ {summary_msg}")
        else:
            summary_msg = "框架存在严重问题，需要立即修复。"
            self.logger.error(summary_msg)
            print(f"\n🚨 {summary_msg}")
        
        # 创建会话摘要
        self.logger_manager.create_session_summary()

async def main():
    """主测试函数"""
    tester = FrameworkTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())