#!/usr/bin/env python3
"""
真正的协调智能体测试

Test Real Coordination Agent with Multi-Agent Orchestration
"""

import asyncio
import time
from pathlib import Path

from config.config import FrameworkConfig
from core.real_centralized_coordinator import RealCentralizedCoordinator
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent

# 导入增强日志系统
from core.enhanced_logging_config import (
    setup_enhanced_logging, 
    get_test_logger, 
    get_artifacts_dir
)


class RealCoordinationTester:
    """真正的协调智能体测试器"""
    
    def __init__(self):
        # 初始化增强日志系统
        self.logger_manager = setup_enhanced_logging()
        self.logger = get_test_logger()
        
        self.config = FrameworkConfig.from_env()
        self.artifacts_dir = get_artifacts_dir()
        self.session_dir = self.logger_manager.get_session_dir()
        
        self.logger.info("🚀 初始化真正的协调智能体测试器")
        print("🚀 初始化真正的协调智能体测试器")
        print(f"📁 实验目录: {self.session_dir}")
        print(f"🛠️ 工件目录: {self.artifacts_dir}")
        
        # 测试结果记录
        self.test_results = {}
        self.start_time = time.time()
    
    async def test_real_coordination_simple(self):
        """测试真正的协调 - 简单任务"""
        self.logger.info("开始真正的协调测试 - 简单任务")
        print("\n" + "="*80)
        print("🎯 真正的协调智能体测试 - 简单任务")
        print("="*80)
        
        try:
            # 创建协调智能体
            coordinator = RealCentralizedCoordinator(self.config)
            
            # 创建和注册专业智能体
            verilog_agent = RealVerilogDesignAgent(self.config)
            review_agent = RealCodeReviewAgent(self.config)
            
            coordinator.register_agent(verilog_agent)
            coordinator.register_agent(review_agent)
            
            print(f"✅ 协调智能体创建完成，注册了 {len(coordinator.registered_agents)} 个智能体")
            self.logger.info(f"协调智能体注册智能体数: {len(coordinator.registered_agents)}")
            
            # 定义一个简单但完整的任务
            simple_task = """
请设计并验证一个8位全加器模块，具体要求：

1. 设计一个8位全加器，支持：
   - 两个8位输入数据 A 和 B
   - 1位进位输入 Cin
   - 8位输出结果 Sum
   - 1位进位输出 Cout

2. 设计完成后进行验证：
   - 生成完整的测试台
   - 进行仿真测试
   - 验证功能正确性
   - 提供质量分析报告

请通过多智能体协作完成这个任务。
"""
            
            print("📋 任务描述:")
            print(simple_task.strip())
            
            # 通过协调智能体处理任务
            start_time = time.time()
            result = await coordinator.process_user_task(simple_task, max_rounds=5)
            execution_time = time.time() - start_time
            
            print(f"\n📊 协调执行结果:")
            print(f"  🎯 任务成功: {result.get('success', False)}")
            print(f"  🆔 对话ID: {result.get('conversation_id', 'N/A')}")
            print(f"  ⏱️ 执行时间: {execution_time:.2f}秒")
            print(f"  🔄 执行轮次: {result.get('execution_summary', {}).get('total_rounds', 0)}")
            print(f"  📋 完成任务数: {result.get('execution_summary', {}).get('successful_tasks', 0)}")
            print(f"  📁 生成文件数: {result.get('execution_summary', {}).get('generated_files', 0)}")
            
            # 显示生成的文件
            if result.get('generated_files'):
                print(f"\n📁 生成的文件:")
                for file_path in result['generated_files'][:10]:  # 显示前10个文件
                    print(f"  - {Path(file_path).name}")
                if len(result['generated_files']) > 10:
                    print(f"  ... 还有 {len(result['generated_files']) - 10} 个文件")
            
            # 显示任务执行详情
            if result.get('task_results'):
                print(f"\n📋 任务执行详情:")
                for i, task in enumerate(result['task_results'][:3]):  # 显示前3个任务
                    print(f"  {i+1}. 任务 {task.get('task_id', 'N/A')}")
                    print(f"     - 智能体: {task.get('agent_id', 'N/A')}")
                    print(f"     - 状态: {task.get('status', 'N/A')}")
                    print(f"     - 执行时间: {task.get('execution_time', 0):.2f}秒")
            
            return result.get('success', False)
            
        except Exception as e:
            self.logger.error(f"简单协调测试失败: {str(e)}")
            print(f"❌ 简单协调测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_real_coordination_complex(self):
        """测试真正的协调 - 复杂任务"""
        self.logger.info("开始真正的协调测试 - 复杂任务")
        print("\n" + "="*80)
        print("🎯 真正的协调智能体测试 - 复杂任务")
        print("="*80)
        
        try:
            # 创建协调智能体
            coordinator = RealCentralizedCoordinator(self.config)
            
            # 创建和注册专业智能体
            verilog_agent = RealVerilogDesignAgent(self.config)
            review_agent = RealCodeReviewAgent(self.config)
            
            coordinator.register_agent(verilog_agent)
            coordinator.register_agent(review_agent)
            
            # 定义一个复杂的多阶段任务
            complex_task = """
请设计并实现一个完整的16位算术逻辑单元(ALU)系统，包括以下组件：

阶段1 - 基础组件设计：
1. 16位全加器模块
2. 16位逻辑运算单元（AND, OR, XOR）
3. 16位移位器（左移、右移）

阶段2 - ALU集成：
1. 集成所有基础组件到一个16位ALU
2. 支持至少8种运算操作
3. 包含状态标志输出（零标志、负标志、溢出标志）

阶段3 - 验证和测试：
1. 为每个基础组件生成测试台
2. 为完整ALU生成综合测试台
3. 运行所有仿真测试
4. 生成完整的验证报告

阶段4 - 文档和优化：
1. 生成设计文档
2. 性能分析报告
3. 优化建议

这是一个需要多个智能体协作的复杂项目，请通过协调智能体来组织和管理整个开发流程。
"""
            
            print("📋 复杂任务描述:")
            print(complex_task.strip())
            
            # 通过协调智能体处理任务
            start_time = time.time()
            result = await coordinator.process_user_task(complex_task, max_rounds=8)
            execution_time = time.time() - start_time
            
            print(f"\n📊 复杂协调执行结果:")
            print(f"  🎯 任务成功: {result.get('success', False)}")
            print(f"  🆔 对话ID: {result.get('conversation_id', 'N/A')}")
            print(f"  ⏱️ 执行时间: {execution_time:.2f}秒")
            print(f"  🔄 执行轮次: {result.get('execution_summary', {}).get('total_rounds', 0)}")
            print(f"  📋 完成任务数: {result.get('execution_summary', {}).get('successful_tasks', 0)}")
            print(f"  📁 生成文件数: {result.get('execution_summary', {}).get('generated_files', 0)}")
            
            # 分析协调效果
            self._analyze_coordination_effectiveness(result)
            
            return result.get('success', False)
            
        except Exception as e:
            self.logger.error(f"复杂协调测试失败: {str(e)}")
            print(f"❌ 复杂协调测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _analyze_coordination_effectiveness(self, result: dict):
        """分析协调效果"""
        print(f"\n🔍 协调效果分析:")
        
        execution_summary = result.get('execution_summary', {})
        
        # 效率分析
        total_time = execution_summary.get('total_time', 0)
        total_tasks = execution_summary.get('successful_tasks', 0)
        if total_tasks > 0:
            avg_task_time = total_time / total_tasks
            print(f"  📊 平均任务执行时间: {avg_task_time:.2f}秒")
        
        # 成功率分析
        successful = execution_summary.get('successful_tasks', 0)
        failed = execution_summary.get('failed_tasks', 0)
        total = successful + failed
        if total > 0:
            success_rate = (successful / total) * 100
            print(f"  📈 任务成功率: {success_rate:.1f}%")
        
        # 协调轮次分析
        rounds = execution_summary.get('total_rounds', 0)
        print(f"  🔄 协调轮次数: {rounds}")
        
        if rounds > 0 and total_time > 0:
            avg_round_time = total_time / rounds
            print(f"  ⏱️ 平均轮次时间: {avg_round_time:.2f}秒")
        
        # 文件产出分析
        files_count = execution_summary.get('generated_files', 0)
        print(f"  📁 文件产出效率: {files_count}个文件")
        
        # 智能体利用率分析
        task_results = result.get('task_results', [])
        agent_usage = {}
        for task in task_results:
            agent_id = task.get('agent_id', 'unknown')
            agent_usage[agent_id] = agent_usage.get(agent_id, 0) + 1
        
        if agent_usage:
            print(f"  🤖 智能体利用情况:")
            for agent_id, count in agent_usage.items():
                print(f"     - {agent_id}: {count}个任务")
    
    async def test_coordination_decision_making(self):
        """测试协调决策能力"""
        self.logger.info("开始协调决策能力测试")
        print("\n" + "="*60)
        print("🧠 协调决策能力测试")
        print("="*60)
        
        try:
            # 创建协调智能体
            coordinator = RealCentralizedCoordinator(self.config)
            
            # 创建和注册智能体
            verilog_agent = RealVerilogDesignAgent(self.config)
            review_agent = RealCodeReviewAgent(self.config)
            
            coordinator.register_agent(verilog_agent)
            coordinator.register_agent(review_agent)
            
            # 测试不同类型的任务，看协调智能体如何分配
            test_cases = [
                {
                    "name": "纯设计任务",
                    "task": "设计一个4位计数器模块，包含时钟、复位和使能信号。",
                    "expected_agent": "real_verilog_design_agent"
                },
                {
                    "name": "纯验证任务", 
                    "task": "对现有的adder_2bit.v文件进行完整的功能验证和测试。",
                    "expected_agent": "real_code_review_agent"
                },
                {
                    "name": "混合任务",
                    "task": "设计一个8位移位寄存器并进行完整的验证测试。",
                    "expected_agent": "both"  # 应该两个智能体都会被使用
                }
            ]
            
            decision_results = []
            
            for i, test_case in enumerate(test_cases):
                print(f"\n📋 测试案例 {i+1}: {test_case['name']}")
                print(f"任务: {test_case['task']}")
                
                start_time = time.time()
                result = await coordinator.process_user_task(test_case['task'], max_rounds=3)
                execution_time = time.time() - start_time
                
                # 分析智能体使用情况
                task_results = result.get('task_results', [])
                used_agents = [task.get('agent_id') for task in task_results]
                unique_agents = list(set(used_agents))
                
                print(f"  🤖 使用的智能体: {', '.join(unique_agents)}")
                print(f"  ⏱️ 执行时间: {execution_time:.2f}秒")
                print(f"  📋 完成任务数: {len(task_results)}")
                
                decision_results.append({
                    "test_case": test_case['name'],
                    "used_agents": unique_agents,
                    "execution_time": execution_time,
                    "success": result.get('success', False)
                })
            
            # 总结决策能力
            print(f"\n🎯 决策能力总结:")
            successful_tests = sum(1 for r in decision_results if r['success'])
            print(f"  ✅ 成功测试: {successful_tests}/{len(decision_results)}")
            
            avg_time = sum(r['execution_time'] for r in decision_results) / len(decision_results)
            print(f"  ⏱️ 平均执行时间: {avg_time:.2f}秒")
            
            # 分析智能体选择的合理性
            print(f"  🤖 智能体选择分析:")
            for result in decision_results:
                agents_str = ', '.join(result['used_agents'])
                print(f"     - {result['test_case']}: {agents_str}")
            
            return successful_tests == len(decision_results)
            
        except Exception as e:
            self.logger.error(f"协调决策测试失败: {str(e)}")
            print(f"❌ 协调决策测试失败: {str(e)}")
            return False
    
    async def generate_coordination_test_report(self):
        """生成协调测试报告"""
        total_time = time.time() - self.start_time
        
        print("\n" + "="*80)
        print("📊 真正的协调智能体测试报告")
        print("="*80)
        
        print(f"⏱️ 总测试时间: {total_time:.2f}秒")
        
        # 统计文件
        artifacts_count = len(list(self.artifacts_dir.glob("*")))
        output_count = len(list(Path("./output").glob("*"))) if Path("./output").exists() else 0
        total_files = artifacts_count + output_count
        
        print(f"📁 生成文件总数: {total_files}")
        print(f"🛠️ 工件目录文件: {artifacts_count}")
        print(f"📋 输出目录文件: {output_count}")
        
        # 保存详细报告
        report = {
            "test_type": "real_coordination_multi_agent",
            "timestamp": time.time(),
            "duration": total_time,
            "files_generated": total_files,
            "artifacts_count": artifacts_count,
            "output_count": output_count,
            "session_dir": str(self.session_dir),
            "artifacts_dir": str(self.artifacts_dir),
            "test_results": self.test_results
        }
        
        import json
        report_file = self.session_dir / f"coordination_test_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 详细报告已保存: {report_file}")
        
        # 创建会话摘要
        self.logger_manager.create_session_summary()
        
        self.logger.info("真正的协调智能体测试完成")
        print("✅ 真正的协调智能体测试完成")


async def main():
    """主测试函数"""
    tester = RealCoordinationTester()
    
    print("🚀 开始真正的协调智能体测试")
    
    # Test 1: 简单协调任务
    print("\n" + "🔹" * 60)
    simple_success = await tester.test_real_coordination_simple()
    tester.test_results['simple_coordination'] = simple_success
    
    # Test 2: 复杂协调任务  
    print("\n" + "🔹" * 60)
    complex_success = await tester.test_real_coordination_complex()
    tester.test_results['complex_coordination'] = complex_success
    
    # Test 3: 协调决策能力
    print("\n" + "🔹" * 60)
    decision_success = await tester.test_coordination_decision_making()
    tester.test_results['decision_making'] = decision_success
    
    # 生成最终报告
    await tester.generate_coordination_test_report()
    
    # 显示总结
    successful_tests = sum(1 for success in tester.test_results.values() if success)
    total_tests = len(tester.test_results)
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\n🎉 测试总结:")
    print(f"  ✅ 成功测试: {successful_tests}/{total_tests}")
    print(f"  📈 成功率: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎊 真正的协调智能体测试成功！")
    else:
        print("⚠️ 协调智能体需要进一步优化")


if __name__ == "__main__":
    asyncio.run(main())