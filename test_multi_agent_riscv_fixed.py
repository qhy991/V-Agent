#!/usr/bin/env python3
"""
修复版本的多智能体RISC-V项目测试 - 包含完整的日志记录
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 第一步：强制重置日志系统以应用修复
print("🔧 应用日志修复...")
import core.enhanced_logging_config
core.enhanced_logging_config.reset_logging_system()

from config.config import FrameworkConfig
from core.centralized_coordinator import CentralizedCoordinator
from agents.real_verilog_agent import RealVerilogDesignAgent
from agents.real_code_reviewer import RealCodeReviewAgent
from core.enhanced_logging_config import setup_enhanced_logging, get_test_logger


class FixedMultiAgentRISCVTest:
    """修复版本的多智能体RISC-V项目协作测试"""
    
    def __init__(self):
        # 重新初始化日志系统（应用修复）
        self.log_session = setup_enhanced_logging("multi_agent_riscv_fixed")
        self.test_logger = get_test_logger()
        
        print(f"📂 实验目录: {self.log_session.get_session_dir()}")
        
        # 初始化配置
        self.config = FrameworkConfig.from_env()
        
        # 创建协调器
        self.coordinator = CentralizedCoordinator(self.config)
        
        # 初始化智能体
        self.verilog_agent = RealVerilogDesignAgent(self.config)
        self.reviewer_agent = RealCodeReviewAgent(self.config)
        
        # 注册智能体到协调器
        self.coordinator.register_agent(self.verilog_agent)
        self.coordinator.register_agent(self.reviewer_agent)
        
        print(f"🏗️ 修复版多智能体RISC-V项目测试初始化完成")
        print(f"📂 工作目录: {self.log_session.get_artifacts_dir()}")
        
        # 验证日志系统是否正常工作
        self.test_logger.info("多智能体RISC-V测试开始")
        self.coordinator.logger.info("协调器已初始化，开始测试")
    
    async def run_simplified_test(self):
        """运行简化的测试，重点验证日志记录"""
        print("\n" + "="*80)
        print("🚀 启动简化的多智能体协作测试（重点验证日志）")
        print("="*80)
        
        start_time = time.time()
        
        # 第一阶段：简单设计任务
        test_task = """
        请设计一个简单的32位RISC-V ALU模块，包括：
        1. 基础算术运算（加法、减法）
        2. 基础逻辑运算（与、或、异或）
        3. 移位操作（左移、右移）
        
        请提供完整的Verilog代码实现。
        """
        
        self.test_logger.info("开始执行RISC-V ALU设计任务")
        
        try:
            # 协调器协调任务执行
            result = await self.coordinator.coordinate_task_execution(test_task)
            
            self.test_logger.info(f"任务执行完成，结果长度: {len(str(result))} 字符")
            
            execution_time = time.time() - start_time
            print(f"\n⏱️ 任务执行时间: {execution_time:.2f} 秒")
            
            return {
                "success": True,
                "execution_time": execution_time,
                "result_size": len(str(result)),
                "result": result
            }
            
        except Exception as e:
            self.test_logger.error(f"任务执行失败: {str(e)}")
            execution_time = time.time() - start_time
            print(f"\n❌ 任务执行失败: {str(e)}")
            print(f"⏱️ 失败前执行时间: {execution_time:.2f} 秒")
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time
            }
    
    def analyze_logs(self):
        """分析生成的日志文件"""
        print("\n📊 分析生成的日志文件...")
        
        session_dir = self.log_session.get_session_dir()
        
        # 要检查的关键日志文件
        key_log_files = [
            ('centralized_coordinator.log', '协调器专用日志'),
            ('enhanced_llm_client.log', 'LLM完整对话日志'),
            ('real_verilog_agent.log', 'Verilog智能体日志'),
            ('real_code_reviewer.log', '代码审查智能体日志'),
            ('base_agent.log', '基础智能体日志'),
            ('experiment_summary.log', '实验总结日志')
        ]
        
        log_analysis = {
            "total_files": 0,
            "non_empty_files": 0,
            "total_size": 0,
            "llm_conversations": 0,
            "coordinator_activities": 0,
            "files_details": {}
        }
        
        for log_file, description in key_log_files:
            file_path = session_dir / log_file
            if file_path.exists():
                log_analysis["total_files"] += 1
                size = file_path.stat().st_size
                log_analysis["total_size"] += size
                
                if size > 0:
                    log_analysis["non_empty_files"] += 1
                    print(f"✅ {description}: {size} bytes")
                    
                    # 分析文件内容
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 统计关键指标
                        llm_requests = content.count('🤖 开始LLM请求')
                        llm_responses = content.count('🤖 LLM响应')
                        coordinator_debug = content.count('🔍 DEBUG:')
                        coordinator_activities = content.count('centralized_coordinator')
                        
                        log_analysis["llm_conversations"] += llm_requests
                        log_analysis["coordinator_activities"] += coordinator_activities
                        
                        file_stats = {
                            "size": size,
                            "llm_requests": llm_requests,
                            "llm_responses": llm_responses,
                            "coordinator_debug": coordinator_debug,
                            "coordinator_activities": coordinator_activities
                        }
                        
                        log_analysis["files_details"][log_file] = file_stats
                        
                        # 显示详细统计
                        if llm_requests > 0 or llm_responses > 0:
                            print(f"   🤖 LLM对话: {llm_requests} 请求, {llm_responses} 响应")
                        if coordinator_debug > 0:
                            print(f"   🧠 协调器调试: {coordinator_debug} 条")
                        if coordinator_activities > 0 and log_file != 'base_agent.log':
                            print(f"   📋 协调器活动: {coordinator_activities} 条")
                            
                    except Exception as e:
                        print(f"   ❌ 内容分析失败: {e}")
                        
                else:
                    print(f"❌ {description}: 文件为空")
            else:
                print(f"❌ {description}: 文件不存在")
        
        # 总结分析结果
        print(f"\n📈 日志分析总结:")
        print(f"   📁 总文件数: {log_analysis['total_files']}")
        print(f"   ✅ 非空文件: {log_analysis['non_empty_files']}")
        print(f"   📊 总大小: {log_analysis['total_size']} bytes")
        print(f"   🤖 LLM对话总数: {log_analysis['llm_conversations']}")
        print(f"   🧠 协调器活动: {log_analysis['coordinator_activities']}")
        
        # 重点验证协调器日志修复
        coord_log = session_dir / 'centralized_coordinator.log'
        if coord_log.exists() and coord_log.stat().st_size > 0:
            print(f"\n🎉 协调器日志修复成功！")
            print(f"   📄 文件: {coord_log}")
            print(f"   📊 大小: {coord_log.stat().st_size} bytes")
        else:
            print(f"\n⚠️ 协调器日志仍有问题")
            base_log = session_dir / 'base_agent.log'
            if base_log.exists():
                with open(base_log, 'r', encoding='utf-8') as f:
                    base_content = f.read()
                coord_in_base = base_content.count('centralized_coordinator')
                print(f"   📊 base_agent.log中协调器记录: {coord_in_base} 条")
        
        return log_analysis


async def main():
    """主函数"""
    print("🔥 启动修复版多智能体RISC-V项目测试")
    print("="*80)
    print("重点验证：")
    print("✅ 协调器日志正确写入centralized_coordinator.log")
    print("✅ LLM完整对话记录在enhanced_llm_client.log") 
    print("✅ 所有智能体活动完整记录")
    print("="*80)
    
    # 创建测试实例
    test_instance = FixedMultiAgentRISCVTest()
    
    # 运行测试
    result = await test_instance.run_simplified_test()
    
    # 分析日志
    log_analysis = test_instance.analyze_logs()
    
    # 显示最终结果
    print(f"\n🎯 测试结果:")
    if result["success"]:
        print(f"✅ 测试成功完成")
        print(f"⏱️ 执行时间: {result['execution_time']:.2f} 秒")
        print(f"📊 结果大小: {result['result_size']} 字符")
    else:
        print(f"❌ 测试失败: {result['error']}")
    
    # 验证修复效果
    print(f"\n🔍 修复效果验证:")
    coord_fixed = log_analysis['files_details'].get('centralized_coordinator.log', {}).get('size', 0) > 0
    llm_logging = log_analysis['llm_conversations'] > 0
    
    if coord_fixed:
        print(f"✅ 协调器日志修复成功")
    else:
        print(f"❌ 协调器日志仍有问题")
    
    if llm_logging:
        print(f"✅ LLM对话记录功能正常")
    else:
        print(f"❌ LLM对话记录有问题")
    
    if coord_fixed and llm_logging:
        print(f"\n🎉 所有日志修复都成功！")
    else:
        print(f"\n⚠️ 仍有部分日志问题需要解决")
    
    print(f"\n📂 详细日志目录: {test_instance.log_session.get_session_dir()}")
    
    return result, log_analysis


if __name__ == "__main__":
    result, log_analysis = asyncio.run(main())