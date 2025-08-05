#!/usr/bin/env python3
"""
批量生成多智能体协作可视化示例
"""

from static_agent_visualizer import StaticAgentVisualizer
from datetime import datetime

def main():
    """生成多个可视化示例"""
    visualizer = StaticAgentVisualizer()
    
    test_cases = [
        {
            "name": "basic_counter",
            "request": "请设计一个8位counter模块",
            "description": "基础设计任务 - 只包含设计流程"
        },
        {
            "name": "counter_with_verification", 
            "request": "设计一个counter模块并生成测试台验证",
            "description": "完整流程 - 设计+验证"
        },
        {
            "name": "advanced_counter",
            "request": "创建一个带使能和复位的计数器并进行仿真测试",
            "description": "高级需求 - 包含详细功能和测试"
        },
        {
            "name": "alu_design",
            "request": "设计一个ALU模块，支持加减法运算，并进行功能验证",
            "description": "复杂设计 - ALU模块设计和验证"
        }
    ]
    
    print("🚀 批量生成多智能体协作可视化示例")
    print("=" * 60)
    
    generated_files = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 生成示例 {i}/{len(test_cases)}: {test_case['name']}")
        print(f"📝 需求: {test_case['request']}")
        print(f"📄 描述: {test_case['description']}")
        print("⏳ 正在生成...")
        
        try:
            html_content = visualizer.simulate_conversation(test_case['request'])
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"visualization_{test_case['name']}_{timestamp}.html"
            
            # 保存文件
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            generated_files.append({
                'filename': filename,
                'name': test_case['name'],
                'description': test_case['description'],
                'message_count': len(visualizer.conversation_history)
            })
            
            print(f"✅ 生成成功: {filename}")
            print(f"📊 包含 {len(visualizer.conversation_history)} 条对话消息")
            
        except Exception as e:
            print(f"❌ 生成失败: {str(e)}")
    
    # 生成索引页面
    print(f"\n📁 生成索引页面...")
    index_html = generate_index_page(generated_files)
    
    index_filename = f"visualization_index_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(index_filename, 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    print(f"✅ 索引页面: {index_filename}")
    
    print(f"\n🎉 生成完成!")
    print(f"📁 共生成 {len(generated_files)} 个可视化文件 + 1个索引页面")
    print(f"🌐 请用浏览器打开 {index_filename} 查看所有示例")

def generate_index_page(files):
    """生成索引页面"""
    
    files_html = ""
    for file_info in files:
        files_html += f"""
<div class="file-card">
    <h3>🔧 {file_info['name'].replace('_', ' ').title()}</h3>
    <p class="description">{file_info['description']}</p>
    <div class="stats">
        <span class="stat">📊 {file_info['message_count']} 条消息</span>
    </div>
    <a href="{file_info['filename']}" class="view-btn" target="_blank">查看可视化</a>
</div>
"""
    
    return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>多智能体协作可视化示例集</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }}
        
        .header {{
            text-align: center;
            padding: 40px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.8em;
            font-weight: 300;
        }}
        
        .header p {{
            margin: 15px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin: 30px 0;
        }}
        
        .file-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .file-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}
        
        .file-card h3 {{
            margin-top: 0;
            color: #2c3e50;
            font-size: 1.3em;
        }}
        
        .description {{
            color: #666;
            margin: 15px 0;
            line-height: 1.5;
        }}
        
        .stats {{
            margin: 15px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 6px;
            font-size: 0.9em;
        }}
        
        .stat {{
            color: #495057;
        }}
        
        .view-btn {{
            display: inline-block;
            padding: 12px 24px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
        }}
        
        .view-btn:hover {{
            background: linear-gradient(90deg, #5a6fd8 0%, #6a4190 100%);
            transform: translateY(-2px);
        }}
        
        .intro {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .intro h2 {{
            color: #2c3e50;
            margin-top: 0;
        }}
        
        .features {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .feature {{
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            color: #666;
            border-top: 1px solid #dee2e6;
            margin-top: 50px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 多智能体协作可视化示例集</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="intro">
        <h2>📖 使用说明</h2>
        <p>这个可视化工具展示了多智能体协作框架中不同智能体之间的对话流程，包括：</p>
        
        <div class="features">
            <div class="feature">
                <strong>🔧 System Prompt</strong><br>
                显示每个智能体的系统提示，定义其角色和能力边界
            </div>
            <div class="feature">
                <strong>👤 User Prompt</strong><br>
                展示用户请求和智能体接收到的具体任务描述
            </div>
            <div class="feature">
                <strong>⚙️ 工具调用</strong><br>
                可视化工具调用过程，包括参数、执行结果和状态
            </div>
            <div class="feature">
                <strong>🤖 Assistant Response</strong><br>
                显示智能体的最终响应和任务完成情况
            </div>
        </div>
        
        <p><strong>💡 调试建议：</strong>通过观察工具调用的成功/失败状态，可以快速定位问题所在。特别关注Verilog设计智能体是否尝试调用禁止的testbench相关工具。</p>
    </div>
    
    <h2 style="text-align: center; color: #2c3e50; margin: 40px 0 20px 0;">📋 可视化示例</h2>
    
    <div class="grid">
        {files_html}
    </div>
    
    <div class="footer">
        <p>🔧 多智能体协作框架可视化工具</p>
        <p>帮助理解和调试Verilog设计智能体工作流程</p>
    </div>
</body>
</html>
"""

if __name__ == "__main__":
    main()