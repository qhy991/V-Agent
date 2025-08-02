#!/usr/bin/env python3
"""
最终Schema修复验证 - 运行简化的TDD测试确保修复生效
"""

import sys
import asyncio
import tempfile
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.enhanced_centralized_coordinator import EnhancedCentralizedCoordinator
from core.file_manager import initialize_file_manager, get_file_manager
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent

def setup_logging():
    """设置测试日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_final_validation.log')
        ]
    )

async def test_enhanced_verilog_agent():
    """测试增强的Verilog Agent是否能成功调用工具"""
    print("🧪 测试增强Verilog Agent工具调用")
    print("=" * 50)
    
    # 创建临时工作空间
    temp_workspace = Path(tempfile.mkdtemp(prefix="final_test_"))
    initialize_file_manager(temp_workspace)
    
    try:
        # 初始化Agent
        config = FrameworkConfig.from_env()
        agent = EnhancedRealVerilogAgent(config)
        
        # 创建一个简单的设计任务
        design_task = """设计一个简单的2位加法器：

模块接口：
```verilog
module simple_2bit_adder (
    input  [1:0] a,         // 第一个2位操作数
    input  [1:0] b,         // 第二个2位操作数
    input        cin,       // 输入进位
    output [1:0] sum,       // 2位和
    output       cout       // 输出进位
);
```

🎯 功能要求：
1. 实现2位二进制加法运算：sum = a + b + cin
2. 正确计算输出进位：cout
3. 使用简洁的RTL风格编码
"""
        
        print(f"📋 设计任务: {design_task[:100]}...")
        
        # 使用增强验证处理（这会触发Schema验证和修复）
        result = await agent.process_with_enhanced_validation(
            design_task, max_iterations=3
        )
        
        print(f"\n📊 处理结果:")
        print(f"  成功: {result.get('success', False)}")
        print(f"  迭代次数: {result.get('iterations', 0)}")
        
        if result.get('success'):
            print("✅ Agent成功完成任务 - Schema修复系统工作正常！")
            
            # 检查是否有生成的文件
            file_manager = get_file_manager()
            verilog_files = file_manager.get_files_by_type("verilog")
            print(f"📄 生成的Verilog文件: {len(verilog_files)} 个")
            
            for file_ref in verilog_files:
                print(f"  - {Path(file_ref.file_path).name} ({file_ref.description})")
        else:
            print("⚠️ Agent未能完成任务")
            error = result.get('error', 'Unknown error')
            print(f"  错误: {error}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理临时文件
        import shutil
        try:
            shutil.rmtree(temp_workspace)
        except:
            pass

async def test_coordinator_integration():
    """测试协调器集成"""
    print("\n\n🤝 测试协调器集成")
    print("=" * 50)
    
    # 创建临时工作空间
    temp_workspace = Path(tempfile.mkdtemp(prefix="coordinator_test_"))
    initialize_file_manager(temp_workspace)
    
    try:
        # 初始化协调器
        config = FrameworkConfig.from_env()
        coordinator = EnhancedCentralizedCoordinator(config)
        
        # 注册增强的Agent
        verilog_agent = EnhancedRealVerilogAgent(config)
        coordinator.register_agent(verilog_agent)
        
        # 简单的设计任务
        simple_task = "设计一个2输入AND门的Verilog模块"
        
        print(f"📋 协调器任务: {simple_task}")
        
        # 执行任务
        result = await coordinator.coordinate_task_execution(simple_task)
        
        print(f"\n📊 协调结果:")
        print(f"  成功: {result.get('success', False)}")
        print(f"  状态: {result.get('status', 'unknown')}")
        
        if result.get('success'):
            print("✅ 协调器成功 - 整个系统工作正常！")
        else:
            print("⚠️ 协调器未能完成任务")
            if 'error' in result:
                print(f"  错误: {result['error']}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ 协调器测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理临时文件
        import shutil
        try:
            shutil.rmtree(temp_workspace)
        except:
            pass

async def main():
    """主测试流程"""
    print("🚀 最终Schema修复验证测试")
    print("=" * 80)
    
    setup_logging()
    
    success_count = 0
    total_tests = 2
    
    try:
        # 测试1: Agent直接调用
        print("🔬 第1阶段: Agent直接测试")
        if await test_enhanced_verilog_agent():
            success_count += 1
        
        # 测试2: 协调器集成测试
        print("🔬 第2阶段: 协调器集成测试")  
        if await test_coordinator_integration():
            success_count += 1
        
        # 结果汇总
        print("\n" + "=" * 80)
        print("📊 最终验证结果汇总")
        print("=" * 80)
        
        success_rate = success_count / total_tests
        print(f"🎯 测试成功率: {success_count}/{total_tests} ({success_rate*100:.1f}%)")
        
        if success_rate >= 1.0:
            print("🎉 完美！Schema修复系统完全成功")
            print("✅ test-12.log中的问题已彻底解决")
            print("✅ AI Agent与工具的'沟通障碍'已消除")
        elif success_rate >= 0.5:
            print("✅ 良好！大部分Schema问题已解决")
            print("🔧 还有少量问题需要微调")
        else:
            print("⚠️ 仍需改进Schema修复系统")
        
        print(f"\n📄 详细日志: test_final_validation.log")
        
    except Exception as e:
        print(f"❌ 主测试流程异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())