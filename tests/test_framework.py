#!/usr/bin/env python3
"""
框架测试脚本

Framework Test Script for Centralized Agent Framework
"""

import asyncio
import logging
import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig, LLMConfig, CoordinatorConfig, AgentConfig
from core.centralized_coordinator import CentralizedCoordinator
from core.base_agent import TaskMessage, FileReference
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent

from llm_integration.enhanced_llm_client import EnhancedLLMClient


class FrameworkTester:
    """框架测试器"""
    
    def __init__(self):
        self.test_results = []
        self.temp_dir = None
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("FrameworkTester")
    
    def setup_test_environment(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp(prefix="caf_test_")
        os.chdir(self.temp_dir)
        self.logger.info(f"📁 临时测试目录: {self.temp_dir}")
    
    def cleanup_test_environment(self):
        """清理测试环境"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.logger.info("🧹 测试环境清理完成")
    
    def record_test_result(self, test_name: str, success: bool, 
                          message: str = "", details: dict = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        self.logger.info(f"{status} - {test_name}: {message}")
    
    async def test_config_loading(self):
        """测试配置加载"""
        test_name = "配置加载测试"
        
        try:
            # 测试默认配置
            config = FrameworkConfig()
            assert config.llm.provider == "dashscope"
            assert config.coordinator.max_conversation_iterations == 20
            assert config.agent.default_timeout == 120.0
            
            # 测试环境变量配置
            os.environ["CAF_LLM_PROVIDER"] = "openai"
            os.environ["CAF_MAX_ITERATIONS"] = "15"
            config_env = FrameworkConfig.from_env()
            assert config_env.llm.provider == "openai"
            assert config_env.coordinator.max_conversation_iterations == 15
            
            self.record_test_result(test_name, True, "配置加载正常")
            
        except Exception as e:
            self.record_test_result(test_name, False, f"配置加载失败: {str(e)}")
    
    async def test_llm_client_creation(self):
        """测试LLM客户端创建"""
        test_name = "LLM客户端创建测试"
        
        try:
            llm_config = LLMConfig(
                provider="dashscope",
                model_name="qwen-turbo",
                api_key="test_key",
                temperature=0.7
            )
            
            client = EnhancedLLMClient(llm_config)
            assert client.config.provider == "dashscope"
            assert client.config.model_name == "qwen-turbo"
            assert client.config.temperature == 0.7
            
            self.record_test_result(test_name, True, "LLM客户端创建成功")
            
        except Exception as e:
            self.record_test_result(test_name, False, f"LLM客户端创建失败: {str(e)}")
    
    async def test_agent_creation_and_registration(self):
        """测试智能体创建和注册"""
        test_name = "智能体创建和注册测试"
        
        try:
            # 创建配置
            config = FrameworkConfig()
            
            # 创建协调者
            coordinator = CentralizedCoordinator(config)
            
            # 创建智能体
            design_agent = VerilogDesignAgent()
            test_agent = VerilogTestAgent()
            review_agent = VerilogReviewAgent()
            
            # 注册智能体
            assert coordinator.register_agent(design_agent) == True
            assert coordinator.register_agent(test_agent) == True
            assert coordinator.register_agent(review_agent) == True
            
            # 检查注册状态
            team_status = coordinator.get_team_status()
            assert team_status["total_agents"] == 3
            assert "verilog_design_agent" in coordinator.registered_agents
            assert "verilog_test_agent" in coordinator.registered_agents
            assert "verilog_review_agent" in coordinator.registered_agents
            
            self.record_test_result(test_name, True, f"成功注册 {team_status['total_agents']} 个智能体")
            
        except Exception as e:
            self.record_test_result(test_name, False, f"智能体注册失败: {str(e)}")
    
    async def test_task_analysis(self):
        """测试任务分析功能"""
        test_name = "任务分析功能测试"
        
        try:
            config = FrameworkConfig()
            coordinator = CentralizedCoordinator(config)
            
            task_description = "设计一个8位计数器，支持向上和向下计数"
            
            # 测试简单任务分析（无LLM）
            analysis = await coordinator.analyze_task_requirements(task_description)
            
            assert "task_type" in analysis
            assert "complexity" in analysis
            assert isinstance(analysis["complexity"], (int, float))
            assert analysis["complexity"] >= 1
            
            self.record_test_result(test_name, True, 
                                  f"任务分析完成: 类型={analysis.get('task_type')}, "
                                  f"复杂度={analysis.get('complexity')}")
            
        except Exception as e:
            self.record_test_result(test_name, False, f"任务分析失败: {str(e)}")
    
    async def test_agent_selection(self):
        """测试智能体选择功能"""
        test_name = "智能体选择功能测试"
        
        try:
            config = FrameworkConfig()
            coordinator = CentralizedCoordinator(config)
            
            # 注册智能体
            design_agent = VerilogDesignAgent()
            test_agent = VerilogTestAgent()
            coordinator.register_agent(design_agent)
            coordinator.register_agent(test_agent)
            
            # 测试设计任务的智能体选择
            design_task_analysis = {
                "task_type": "design",
                "complexity": 5,
                "required_capabilities": ["code_generation"]
            }
            
            selected_agent = await coordinator.select_best_agent(design_task_analysis)
            assert selected_agent == "verilog_design_agent"
            
            # 测试测试任务的智能体选择
            test_task_analysis = {
                "task_type": "testing",
                "complexity": 3,
                "required_capabilities": ["test_generation"]
            }
            
            selected_agent = await coordinator.select_best_agent(test_task_analysis)
            assert selected_agent == "verilog_test_agent"
            
            self.record_test_result(test_name, True, "智能体选择逻辑正常")
            
        except Exception as e:
            self.record_test_result(test_name, False, f"智能体选择失败: {str(e)}")
    
    async def test_file_operations(self):
        """测试文件操作功能"""
        test_name = "文件操作功能测试"
        
        try:
            design_agent = VerilogDesignAgent()
            
            # 测试文件保存
            test_content = """
module test_module (
    input wire clk,
    input wire rst_n,
    output reg [7:0] count
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= 8'b0;
        else
            count <= count + 1;
    end
endmodule
"""
            
            file_ref = await design_agent.save_result_to_file(
                content=test_content,
                file_path="test_module.v",
                file_type="verilog"
            )
            
            assert file_ref.file_path == "test_module.v"
            assert file_ref.file_type == "verilog"
            assert os.path.exists("test_module.v")
            
            # 测试文件读取
            read_content = await design_agent.autonomous_file_read(file_ref)
            assert read_content == test_content
            
            self.record_test_result(test_name, True, "文件读写操作正常")
            
        except Exception as e:
            self.record_test_result(test_name, False, f"文件操作失败: {str(e)}")
    
    async def test_task_message_processing(self):
        """测试任务消息处理"""
        test_name = "任务消息处理测试"
        
        try:
            design_agent = VerilogDesignAgent()
            
            # 创建测试任务消息
            task_message = TaskMessage(
                task_id="test_task_001",
                sender_id="coordinator",
                receiver_id="verilog_design_agent",
                message_type="design_request",
                content="设计一个简单的8位计数器模块",
                file_references=None,
                metadata={"priority": "high"}
            )
            
            # 处理任务消息
            result = await design_agent.process_task_with_file_references(task_message)
            
            assert "success" in result
            assert "agent_id" in result
            assert result["agent_id"] == "verilog_design_agent"
            
            self.record_test_result(test_name, True, 
                                  f"任务处理完成: 成功={result.get('success')}")
            
        except Exception as e:
            self.record_test_result(test_name, False, f"任务消息处理失败: {str(e)}")
    
    async def test_conversation_flow(self):
        """测试对话流程"""
        test_name = "对话流程测试"
        
        try:
            config = FrameworkConfig()
            coordinator = CentralizedCoordinator(config)
            
            # 注册智能体
            design_agent = VerilogDesignAgent()
            coordinator.register_agent(design_agent)
            
            # 执行简单对话
            task_description = "设计一个8位加法器"
            result = await coordinator.coordinate_task_execution(task_description)
            
            assert "success" in result
            assert "conversation_id" in result
            assert "total_iterations" in result
            
            self.record_test_result(test_name, True, 
                                  f"对话完成: 轮次={result.get('total_iterations', 0)}")
            
        except Exception as e:
            self.record_test_result(test_name, False, f"对话流程失败: {str(e)}")
    
    async def test_error_handling(self):
        """测试错误处理"""
        test_name = "错误处理测试"
        
        try:
            config = FrameworkConfig()
            coordinator = CentralizedCoordinator(config)
            
            # 测试无智能体的情况
            task_description = "设计一个模块"
            result = await coordinator.coordinate_task_execution(task_description)
            
            assert result["success"] == False
            assert "error" in result
            
            # 测试无效任务消息
            design_agent = VerilogDesignAgent()
            invalid_message = TaskMessage(
                task_id="invalid",
                sender_id="test",
                receiver_id="agent",
                message_type="invalid",
                content=""
            )
            
            result = await design_agent.process_task_with_file_references(invalid_message)
            # 应该能处理，但可能结果不理想
            assert "success" in result
            
            self.record_test_result(test_name, True, "错误处理机制正常")
            
        except Exception as e:
            self.record_test_result(test_name, False, f"错误处理测试失败: {str(e)}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始运行框架测试...")
        
        self.setup_test_environment()
        
        try:
            # 按顺序运行测试
            await self.test_config_loading()
            await self.test_llm_client_creation()
            await self.test_agent_creation_and_registration()
            await self.test_task_analysis()
            await self.test_agent_selection()
            await self.test_file_operations()
            await self.test_task_message_processing()
            await self.test_conversation_flow()
            await self.test_error_handling()
            
        finally:
            self.cleanup_test_environment()
    
    def print_test_summary(self):
        """打印测试摘要"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 测试结果摘要:")
        print(f"- 总测试数: {total_tests}")
        print(f"- 通过测试: {passed_tests}")
        print(f"- 失败测试: {failed_tests}")
        print(f"- 成功率: {passed_tests/total_tests*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"- {result['test_name']}: {result['message']}")
        
        print(f"\n{'✅ 所有测试通过!' if failed_tests == 0 else '⚠️ 部分测试失败'}")
        
        return failed_tests == 0


async def main():
    """主测试函数"""
    tester = FrameworkTester()
    
    try:
        await tester.run_all_tests()
        success = tester.print_test_summary()
        
        if success:
            print("🎉 框架测试全部通过！")
            return 0
        else:
            print("😞 框架测试存在问题，请检查日志")
            return 1
            
    except Exception as e:
        print(f"❌ 测试运行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)