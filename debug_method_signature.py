#!/usr/bin/env python3
"""
调试方法签名问题
"""

import asyncio
import inspect
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent
from core.base_agent import TaskMessage

async def debug_method_signatures():
    """调试方法签名"""
    
    print("🔍 调试 execute_enhanced_task 方法签名")
    print("=" * 60)
    
    # 1. 检查Enhanced Verilog Agent
    config = FrameworkConfig.from_env() 
    verilog_agent = EnhancedRealVerilogAgent(config)
    
    print(f"📝 EnhancedRealVerilogAgent 类: {type(verilog_agent)}")
    print(f"📝 继承链: {[cls.__name__ for cls in type(verilog_agent).__mro__]}")
    
    # 检查方法是否存在
    if hasattr(verilog_agent, 'execute_enhanced_task'):
        method = getattr(verilog_agent, 'execute_enhanced_task')
        signature = inspect.signature(method)
        print(f"✅ execute_enhanced_task 方法存在")
        print(f"📋 方法签名: {signature}")
        print(f"📋 参数: {list(signature.parameters.keys())}")
        
        # 尝试调用检查
        task_message = TaskMessage(
            task_id="test_001",
            sender_id="test_sender",
            receiver_id=verilog_agent.agent_id,
            message_type="design_request",
            content="测试任务"
        )
        
        print("\n🧪 尝试调用测试...")
        try:
            # 创建参数字典
            kwargs = {
                'enhanced_prompt': "测试提示",
                'original_message': task_message,
                'file_contents': {}
            }
            
            print(f"📦 调用参数: {list(kwargs.keys())}")
            
            # 检查参数是否匹配
            bound_args = signature.bind(**kwargs)
            print(f"✅ 参数绑定成功: {bound_args.arguments}")
            
        except TypeError as e:
            print(f"❌ 参数绑定失败: {e}")
    else:
        print("❌ execute_enhanced_task 方法不存在")
    
    print("\n" + "=" * 60)
    
    # 2. 检查Enhanced Code Reviewer
    reviewer_agent = EnhancedRealCodeReviewAgent(config)
    
    print(f"📝 EnhancedRealCodeReviewAgent 类: {type(reviewer_agent)}")
    print(f"📝 继承链: {[cls.__name__ for cls in type(reviewer_agent).__mro__]}")
    
    if hasattr(reviewer_agent, 'execute_enhanced_task'):
        method = getattr(reviewer_agent, 'execute_enhanced_task')
        signature = inspect.signature(method)
        print(f"✅ execute_enhanced_task 方法存在")
        print(f"📋 方法签名: {signature}")
        print(f"📋 参数: {list(signature.parameters.keys())}")
    else:
        print("❌ execute_enhanced_task 方法不存在")
        
    print("\n" + "=" * 60)
    print("🔍 检查完成")

if __name__ == "__main__":
    asyncio.run(debug_method_signatures())