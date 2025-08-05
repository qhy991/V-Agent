#!/usr/bin/env python3
"""
测试对话配置是否正确加载.env文件
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_env_loading():
    """测试环境变量加载"""
    print("🧪 测试.env文件加载")
    print("=" * 50)
    
    # 手动加载.env文件
    env_file = project_root / '.env'
    if env_file.exists():
        print(f"✅ 发现.env文件: {env_file}")
        
        # 读取并设置环境变量
        with open(env_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key.startswith('CONVERSATION_'):
                        os.environ[key] = value
                        print(f"✅ 加载: {key}={value}")
    else:
        print(f"❌ 未找到.env文件")
        return False
    
    print("\n🔧 测试对话配置")
    print("=" * 50)
    
    # 测试配置值
    config_vars = [
        'CONVERSATION_DISPLAY_OPTIMIZATION',
        'CONVERSATION_MAX_DISPLAY_ROUNDS', 
        'CONVERSATION_COMPACT_MODE',
        'CONVERSATION_MAX_RESPONSE_LENGTH',
        'CONVERSATION_MAX_HISTORY_TURNS',
        'CONVERSATION_HISTORY_COMPRESSION',
        'CONVERSATION_AUTO_CLEANUP',
        'CONVERSATION_OPTIMIZE_OLLAMA',
        'CONVERSATION_OLLAMA_MAX_CONTEXT'
    ]
    
    for var in config_vars:
        value = os.getenv(var, 'NOT_SET')
        print(f"📋 {var}: {value}")
    
    print("\n🚀 应用配置测试")
    print("=" * 50)
    
    # 测试具体配置
    display_optimization = os.getenv('CONVERSATION_DISPLAY_OPTIMIZATION', 'false').lower() == 'true'
    max_response_length = int(os.getenv('CONVERSATION_MAX_RESPONSE_LENGTH', '500'))
    compact_mode = os.getenv('CONVERSATION_COMPACT_MODE', 'false').lower() == 'true'
    
    print(f"显示优化启用: {display_optimization}")
    print(f"最大响应长度: {max_response_length}")
    print(f"紧凑模式启用: {compact_mode}")
    
    # 测试优化效果
    if display_optimization:
        test_response = "这是一个很长的AI响应内容。" * 50
        if len(test_response) > max_response_length:
            truncated = test_response[:max_response_length] + "...[已截断]"
            print(f"\n📏 响应截断测试:")
            print(f"原始长度: {len(test_response)} 字符")
            print(f"截断后长度: {len(truncated)} 字符")
            print(f"截断内容: {truncated}")
        
    return True

def test_conversation_optimizer():
    """测试对话优化器（如果可用）"""
    try:
        from core.conversation_display_optimizer import conversation_optimizer
        print("\n🎯 对话优化器测试")
        print("=" * 50)
        
        # 测试显示优化
        display_result = conversation_optimizer.display_current_round_only(
            user_request="测试用户请求",
            ai_response="这是一个测试AI响应" * 10,
            iteration_count=1,
            agent_id="test_agent"
        )
        print("✅ 对话优化器工作正常")
        print(f"优化显示示例:\n{display_result}")
        
        return True
    except ImportError as e:
        print(f"\n⚠️ 对话优化器导入失败: {e}")
        return False

if __name__ == "__main__":
    print("🔧 对话配置测试工具")
    print("=" * 60)
    
    # 测试环境变量加载
    env_success = test_env_loading()
    
    # 测试对话优化器
    optimizer_success = test_conversation_optimizer()
    
    print(f"\n📊 测试结果")
    print("=" * 60)
    print(f"环境变量加载: {'✅ 成功' if env_success else '❌ 失败'}")
    print(f"对话优化器: {'✅ 可用' if optimizer_success else '⚠️ 不可用'}")
    
    if env_success:
        print(f"\n🎉 配置已成功加载到.env文件！")
        print(f"现在运行原来的测试命令，应该会看到输出长度大大减少。")
        print(f"\n运行命令:")
        print(f"python3.11 test_llm_coordinator_enhanced.py --design counter --iterations 3")
    else:
        print(f"\n❌ 配置加载失败，请检查.env文件格式")