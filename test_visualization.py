#!/usr/bin/env python3
"""
测试可视化功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gradio_multi_agent_visualizer import MultiAgentVisualizer

def test_visualization():
    """测试可视化功能"""
    print("🧪 测试可视化功能...")
    
    visualizer = MultiAgentVisualizer()
    
    # 测试1: 加载成功的对话历史（来自我们的测试结果）
    print("\n📝 测试1: 加载成功的对话历史")
    test_file_path = project_root / "test_full_workflow_result.json"
    print(f"测试文件: {test_file_path}")
    
    if test_file_path.exists():
        # 模拟实验路径结构
        result = visualizer.load_experiment_conversation(str(project_root))
        print(f"结果: {result}")
        
        if result.startswith("✅"):
            print(f"✅ 成功加载对话历史: {len(visualizer.conversation_history)} 条消息")
            
            # 显示前几条消息
            for i, msg in enumerate(visualizer.conversation_history[:3]):
                print(f"  消息 {i+1}: {msg['type']} - {msg['agent_id']} - {msg['content'][:50]}...")
        else:
            print(f"❌ 加载失败: {result}")
    else:
        print(f"❌ 测试文件不存在: {test_file_path}")
    
    # 测试2: 加载失败的实验
    print("\n📝 测试2: 加载失败的实验")
    failed_experiment_path = "/Users/haiyan-mini/Documents/Study/V-Agent/llm_experiments/llm_coordinator_counter_1754404768"
    result = visualizer.load_experiment_conversation(failed_experiment_path)
    print(f"结果: {result}")
    
    # 测试3: 模拟对话
    print("\n📝 测试3: 模拟对话显示")
    visualizer_test = MultiAgentVisualizer()
    
    # 模拟添加一些消息
    visualizer_test.add_message("user", "user_prompt", "设计一个counter模块")
    visualizer_test.add_message("coordinator", "system_prompt", "分析用户需求")
    visualizer_test.add_message("coordinator", "tool_call", "调用推荐智能体工具", 
                              tool_info={
                                  "tool_name": "recommend_agent",
                                  "parameters": {"task_type": "design"},
                                  "success": True,
                                  "result": "推荐使用Verilog设计智能体"
                              })
    
    print(f"✅ 模拟对话创建完成: {len(visualizer_test.conversation_history)} 条消息")
    
    # 生成HTML显示
    html_content = ""
    for msg in visualizer_test.conversation_history:
        html_content += visualizer_test.format_message_display(msg)
    
    # 保存HTML文件用于测试
    html_file = project_root / "test_visualization_output.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>多智能体对话可视化测试</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 多智能体对话可视化测试</h1>
        <h2>📝 测试对话流程</h2>
        {html_content}
    </div>
</body>
</html>
""")
    
    print(f"✅ HTML测试文件已生成: {html_file}")
    print(f"💡 可以在浏览器中打开查看效果")
    
    print("\n🎉 可视化功能测试完成!")

if __name__ == "__main__":
    test_visualization()