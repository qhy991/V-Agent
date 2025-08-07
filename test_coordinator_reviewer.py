#!/usr/bin/env python3
"""
专门测试协调器和审查智能体的示例
"""

import asyncio
import sys
import os
import tempfile
from pathlib import Path
import time

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_coordinator_and_reviewer():
    """测试协调器和审查智能体的协作"""
    
    try:
        print("🧪 开始测试协调器和审查智能体协作...")
        
        # 导入必要的模块
        from core.llm_coordinator_agent import LLMCoordinatorAgent
        from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
        from config.config import FrameworkConfig
        from core.base_agent import TaskContext
        
        # 初始化配置
        config = FrameworkConfig.from_env()
        
        print("1️⃣ 初始化协调器...")
        coordinator = LLMCoordinatorAgent(config)
        
        print("2️⃣ 初始化审查智能体...")
        reviewer = EnhancedRealCodeReviewAgent(config)
        
        # 手动注册审查智能体到协调器（模拟真实场景）
        print("3️⃣ 注册智能体到协调器...")
        coordinator.register_agent(reviewer)
        
        # 创建一个简单的Verilog文件用于测试
        print("4️⃣ 准备测试文件...")
        test_verilog_content = """module simple_counter(
    input clk,
    input reset,
    output reg [3:0] count
);

always @(posedge clk or posedge reset) begin
    if (reset)
        count <= 4'b0000;
    else
        count <= count + 1;
end

endmodule"""
        
        # 创建临时目录和文件
        test_dir = Path("./test_temp")
        test_dir.mkdir(exist_ok=True)
        
        verilog_file = test_dir / "simple_counter.v"
        with open(verilog_file, 'w') as f:
            f.write(test_verilog_content)
        
        print(f"   📁 测试文件已创建: {verilog_file}")
        
        # 测试直接调用审查智能体（不通过协调器）
        print("5️⃣ 直接测试审查智能体...")
        
        direct_task = f"""请为以下Verilog模块生成测试台并进行验证：

模块文件路径: {verilog_file}
模块内容:
{test_verilog_content}

要求：
1. 生成完整的测试台
2. 验证计数器功能
3. 检查复位逻辑"""
        
        print("   🤖 开始直接调用审查智能体...")
        start_time = time.time()
        
        try:
            direct_result = await reviewer.process_with_function_calling(
                direct_task, 
                max_iterations=5,
                conversation_id=f"direct_test_{int(time.time())}"
            )
            
            execution_time = time.time() - start_time
            print(f"   ✅ 直接调用成功！耗时: {execution_time:.2f}秒")
            print(f"   📝 结果长度: {len(direct_result)} 字符")
            print(f"   📋 结果预览: {direct_result[:200]}...")
            
        except Exception as e:
            print(f"   ❌ 直接调用失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试通过协调器调用
        print("\n6️⃣ 通过协调器测试...")
        
        coordinator_task = f"请为simple_counter模块生成测试台并进行验证，设计文件路径: {verilog_file}"
        
        print("   🤖 开始协调器调用...")
        start_time = time.time()
        
        try:
            coordinator_result = await coordinator.process_user_request(
                coordinator_task,
                conversation_id=f"coordinator_test_{int(time.time())}"
            )
            
            execution_time = time.time() - start_time
            print(f"   ✅ 协调器调用成功！耗时: {execution_time:.2f}秒")
            print(f"   📝 结果: {coordinator_result.get('success', False)}")
            if 'final_result' in coordinator_result:
                print(f"   📋 最终结果: {str(coordinator_result['final_result'])[:200]}...")
            
        except Exception as e:
            print(f"   ❌ 协调器调用失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 清理测试文件
        print("\n7️⃣ 清理测试文件...")
        try:
            if verilog_file.exists():
                os.remove(verilog_file)
            if test_dir.exists() and not any(test_dir.iterdir()):
                os.rmdir(test_dir)
            print("   🧹 清理完成")
        except Exception as e:
            print(f"   ⚠️ 清理失败: {e}")
        
        print("\n✅ 测试完成!")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("这通常是因为依赖项未安装或路径问题")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def simple_reviewer_test():
    """简化版本的审查智能体测试"""
    print("🧪 简化版审查智能体测试...")
    
    # 创建简单的测试文件
    test_content = """module test_adder(
    input [3:0] a,
    input [3:0] b,
    output [4:0] sum
);

assign sum = a + b;

endmodule"""
    
    test_file = Path("./test_adder.v")
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    print(f"📁 测试文件: {test_file}")
    print(f"📄 内容: {test_content}")
    
    # 模拟简单的测试台生成任务
    task = f"""为以下简单的加法器模块生成测试台:

文件路径: {test_file}

要求:
1. 生成基本的测试台
2. 测试几个加法案例
3. 验证输出正确性

这是一个非常简单的模块，应该能快速完成。"""
    
    print(f"\n📋 任务描述: {task}")
    print("\n如果要手动测试，可以使用以下代码:")
    print("""
# 手动测试代码示例:
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from config.config import FrameworkConfig
import asyncio

async def manual_test():
    config = FrameworkConfig.from_env()
    reviewer = EnhancedRealCodeReviewAgent(config)
    
    result = await reviewer.process_with_function_calling(
        task_description,
        max_iterations=3
    )
    
    print("结果:", result)

asyncio.run(manual_test())
""")
    
    # 清理
    try:
        os.remove(test_file)
        print(f"\n🧹 已清理测试文件: {test_file}")
    except:
        pass

if __name__ == "__main__":
    print("选择测试模式:")
    print("1. 完整测试 (协调器 + 审查智能体)")
    print("2. 简化测试 (仅准备测试文件和指导)")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "1":
        asyncio.run(test_coordinator_and_reviewer())
    else:
        asyncio.run(simple_reviewer_test())