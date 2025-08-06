"""
增强实验记录系统使用示例
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, Any

# 导入增强实验记录系统
from core.enhanced_experiment_integration import (
    EnhancedExperimentIntegration,
    ExperimentContextManager,
    record_experiment
)
from core.llm_coordinator_agent import LLMCoordinatorAgent
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewer
from config.config import FrameworkConfig


class EnhancedExperimentExample:
    """增强实验记录示例"""
    
    def __init__(self, experiment_id: str, output_dir: Path):
        self.experiment_id = experiment_id
        self.output_dir = output_dir
        self.context_manager = ExperimentContextManager(experiment_id, output_dir)
    
    async def run_basic_experiment(self, user_request: str) -> Dict[str, Any]:
        """运行基础实验示例"""
        async with self.context_manager.experiment_context(user_request) as integration:
            # 创建配置
            config = FrameworkConfig()
            
            # 创建协调智能体
            coordinator = LLMCoordinatorAgent(config)
            
            # 包装协调智能体以记录其活动
            enhanced_coordinator = integration.wrap_coordinator(coordinator)
            
            # 创建并注册其他智能体
            verilog_agent = EnhancedRealVerilogAgent(config)
            review_agent = EnhancedRealCodeReviewer(config)
            
            # 包装智能体以记录其活动
            enhanced_verilog_agent = integration.wrap_agent(verilog_agent)
            enhanced_review_agent = integration.wrap_agent(review_agent)
            
            # 注册智能体到协调器
            await enhanced_coordinator.register_agent(enhanced_verilog_agent)
            await enhanced_coordinator.register_agent(enhanced_review_agent)
            
            # 记录系统消息
            integration.record_system_message(
                "系统已初始化，所有智能体已注册",
                {"registered_agents": ["enhanced_real_verilog_agent", "enhanced_real_code_reviewer"]}
            )
            
            try:
                # 执行协调任务
                result = await enhanced_coordinator.coordinate_task(
                    user_request,
                    max_iterations=5
                )
                
                # 记录成功信息
                integration.record_info(
                    "system",
                    f"实验成功完成，生成了 {len(result.get('generated_files', []))} 个文件"
                )
                
                return result
                
            except Exception as e:
                # 记录错误
                integration.record_error("system", f"实验执行失败: {str(e)}")
                raise
    
    async def run_advanced_experiment(self, user_request: str) -> Dict[str, Any]:
        """运行高级实验示例 - 使用装饰器"""
        return await self._advanced_experiment_logic(user_request)
    
    @record_experiment("advanced_experiment", Path("experiments/advanced_experiment"))
    async def _advanced_experiment_logic(self, user_request: str, 
                                       experiment_recorder: EnhancedExperimentIntegration = None) -> Dict[str, Any]:
        """高级实验逻辑 - 使用装饰器自动记录"""
        # 创建配置
        config = FrameworkConfig()
        
        # 创建协调智能体
        coordinator = LLMCoordinatorAgent(config)
        
        # 包装协调智能体
        enhanced_coordinator = experiment_recorder.wrap_coordinator(coordinator)
        
        # 创建并包装其他智能体
        verilog_agent = EnhancedRealVerilogAgent(config)
        review_agent = EnhancedRealCodeReviewer(config)
        
        enhanced_verilog_agent = experiment_recorder.wrap_agent(verilog_agent)
        enhanced_review_agent = experiment_recorder.wrap_agent(review_agent)
        
        # 注册智能体
        await enhanced_coordinator.register_agent(enhanced_verilog_agent)
        await enhanced_coordinator.register_agent(enhanced_review_agent)
        
        # 记录自定义信息
        experiment_recorder.record_info(
            "system",
            "高级实验开始执行",
            {"experiment_type": "advanced", "max_iterations": 10}
        )
        
        # 执行任务
        result = await enhanced_coordinator.coordinate_task(
            user_request,
            max_iterations=10
        )
        
        # 记录性能指标
        experiment_recorder.update_performance_metrics({
            "total_execution_time": time.time() - experiment_recorder.recorder.session.start_time,
            "success_rate": 1.0 if result.get('success') else 0.0,
            "files_generated": len(result.get('generated_files', []))
        })
        
        return result
    
    async def run_custom_recording_experiment(self, user_request: str) -> Dict[str, Any]:
        """运行自定义记录实验示例"""
        async with self.context_manager.experiment_context(user_request) as integration:
            # 记录实验开始
            integration.record_info("system", "自定义记录实验开始")
            
            # 模拟工具调用记录
            integration.record_tool_call(
                agent_id="test_agent",
                tool_name="analyze_requirements",
                parameters={"requirements": user_request},
                success=True,
                result={"analysis": "需求分析完成"},
                execution_time=1.5
            )
            
            # 模拟文件操作记录
            integration.record_file_operation(
                operation_type="generate",
                file_path="test_design.v",
                agent_id="test_agent",
                success=True
            )
            
            # 模拟错误记录
            integration.record_error(
                agent_id="test_agent",
                error_message="模拟错误：文件写入失败",
                metadata={"file_path": "failed_file.v", "error_code": "E001"}
            )
            
            # 记录实验完成
            integration.record_info("system", "自定义记录实验完成")
            
            return {"success": True, "message": "自定义记录实验完成"}


async def main():
    """主函数 - 演示增强实验记录系统"""
    print("🚀 增强实验记录系统演示")
    print("=" * 50)
    
    # 创建示例实例
    example = EnhancedExperimentExample(
        experiment_id=f"demo_experiment_{int(time.time())}",
        output_dir=Path("experiments/demo_experiment")
    )
    
    # 测试请求
    test_request = """
    请设计一个名为 counter 的Verilog模块。
    
    基本要求：
    1. 生成完整、可编译的Verilog代码
    2. 包含适当的端口定义和功能实现
    3. 符合Verilog标准语法
    4. 生成对应的测试台进行验证
    
    质量要求：
    - 代码结构清晰，注释完善
    - 遵循良好的命名规范
    - 确保功能正确性
    """
    
    try:
        print("📝 运行基础实验示例...")
        result1 = await example.run_basic_experiment(test_request)
        print(f"✅ 基础实验完成: {result1.get('success', False)}")
        
        print("\n📝 运行高级实验示例...")
        result2 = await example.run_advanced_experiment(test_request)
        print(f"✅ 高级实验完成: {result2.get('success', False)}")
        
        print("\n📝 运行自定义记录实验示例...")
        result3 = await example.run_custom_recording_experiment(test_request)
        print(f"✅ 自定义记录实验完成: {result3.get('success', False)}")
        
        print("\n📊 所有实验报告已保存到 experiments/ 目录")
        print("📁 可以查看以下文件：")
        print("   - experiment_report.json (详细报告)")
        print("   - conversation_history.json (对话历史)")
        print("   - tool_executions.json (工具执行记录)")
        print("   - agent_sessions.json (智能体会话)")
        print("   - analysis_summary.json (分析摘要)")
        
    except Exception as e:
        print(f"❌ 实验执行失败: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main()) 