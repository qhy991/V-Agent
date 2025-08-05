#!/usr/bin/env python3
"""
静态多智能体协作对话可视化工具

生成HTML文件来可视化多智能体对话流程，方便debug
区分显示 System Prompt, User Prompt, 工具调用
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

class StaticAgentVisualizer:
    """静态多智能体协作可视化器"""
    
    def __init__(self):
        self.conversation_history = []
        
    def format_message_display(self, message: Dict[str, Any]) -> str:
        """格式化消息显示"""
        timestamp = datetime.fromtimestamp(message.get('timestamp', time.time())).strftime('%H:%M:%S')
        agent_id = message.get('agent_id', 'unknown')
        msg_type = message.get('type', 'unknown')
        content = str(message.get('content', ''))
        
        # 根据消息类型设置不同的样式和颜色
        if msg_type == 'system_prompt':
            return f"""
<div class="message system-prompt">
    <div class="message-header">
        <span class="icon">🔧</span>
        <span class="title">System Prompt - {agent_id.replace('_', ' ').title()}</span>
        <span class="timestamp">{timestamp}</span>
    </div>
    <div class="message-content">
        <pre class="code-content">{content[:1000]}{'...' if len(content) > 1000 else ''}</pre>
    </div>
</div>
"""
        elif msg_type == 'user_prompt':
            return f"""
<div class="message user-prompt">
    <div class="message-header">
        <span class="icon">👤</span>
        <span class="title">User Prompt - {agent_id.replace('_', ' ').title()}</span>
        <span class="timestamp">{timestamp}</span>
    </div>
    <div class="message-content">{content}</div>
</div>
"""
        elif msg_type == 'tool_call':
            tool_info = message.get('tool_info', {})
            tool_name = tool_info.get('tool_name', 'unknown')
            parameters = tool_info.get('parameters', {})
            success = tool_info.get('success', False)
            result = str(tool_info.get('result', ''))
            
            status_class = "success" if success else "error"
            status_icon = "✅" if success else "❌"
            
            return f"""
<div class="message tool-call {status_class}">
    <div class="message-header">
        <span class="icon">{status_icon}</span>
        <span class="title">Tool Call - {agent_id.replace('_', ' ').title()}</span>
        <span class="timestamp">{timestamp}</span>
    </div>
    <div class="message-content">
        <div class="tool-name">🔧 {tool_name}</div>
        <details class="tool-details">
            <summary>📋 Parameters</summary>
            <pre class="json-content">{json.dumps(parameters, indent=2, ensure_ascii=False)}</pre>
        </details>
        <div class="tool-result">
            <strong>Result:</strong>
            <div class="result-content">{result[:500]}{'...' if len(result) > 500 else ''}</div>
        </div>
    </div>
</div>
"""
        elif msg_type == 'assistant_response':
            return f"""
<div class="message assistant-response">
    <div class="message-header">
        <span class="icon">🤖</span>
        <span class="title">Assistant Response - {agent_id.replace('_', ' ').title()}</span>
        <span class="timestamp">{timestamp}</span>
    </div>
    <div class="message-content">{content}</div>
</div>
"""
        else:
            return f"""
<div class="message other">
    <div class="message-header">
        <span class="icon">📝</span>
        <span class="title">{msg_type.title()} - {agent_id.replace('_', ' ').title()}</span>
        <span class="timestamp">{timestamp}</span>
    </div>
    <div class="message-content">{content}</div>
</div>
"""
    
    def add_message(self, agent_id: str, msg_type: str, content: str, **kwargs):
        """添加消息到对话记录"""
        message = {
            'timestamp': time.time(),
            'agent_id': agent_id,
            'type': msg_type,
            'content': content,
            **kwargs
        }
        self.conversation_history.append(message)
    
    def simulate_conversation(self, user_request: str) -> str:
        """模拟完整的多智能体对话流程"""
        # 清空历史记录
        self.conversation_history = []
        
        # === 第1步: 用户发起请求 ===
        self.add_message("user", "user_prompt", user_request)
        
        # === 第2步: 协调器接收并分析任务 ===
        coordinator_system_prompt = """你是一个AI协调智能体，负责：
1. 分析用户需求
2. 决定调用哪个智能体
3. 分解复合任务
4. 协调多智能体协作

智能体分工：
- enhanced_real_verilog_agent: 负责Verilog设计代码生成
- enhanced_real_code_review_agent: 负责测试台生成和仿真验证

工作流程：
1. 接收用户请求
2. 分析任务类型
3. 分配任务给相应智能体
4. 监控执行进度
5. 整合最终结果"""
        
        self.add_message("coordinator", "system_prompt", coordinator_system_prompt)
        
        # 协调器分析任务类型
        if any(keyword in user_request.lower() for keyword in ["counter", "计数器", "设计", "模块"]):
            # === 第3步: 协调器分配设计任务给Verilog智能体 ===
            self.add_message("coordinator", "tool_call", 
                           "分析用户需求，分配设计任务给Verilog智能体",
                           tool_info={
                               "tool_name": "assign_task_to_agent",
                               "parameters": {
                                   "agent_id": "enhanced_real_verilog_agent",
                                   "task_description": f"根据用户需求设计Verilog模块: {user_request}",
                                   "task_priority": "high",
                                   "expected_deliverables": ["verilog_code", "design_documentation"]
                               },
                               "success": True,
                               "result": "✅ 设计任务已成功分配给Verilog智能体。任务ID: TASK_001, 预期完成时间: 2-3分钟"
                           })
            
            # === 第4步: Verilog智能体接收任务 ===
            verilog_system_prompt = """你是一位资深的Verilog硬件设计专家，专门负责：
- Verilog/SystemVerilog模块设计和代码生成
- 组合逻辑和时序逻辑设计
- 代码质量分析和最佳实践应用
- 设计文档生成

🚨 重要约束 - 角色边界:
❌ 绝对禁止调用 generate_testbench 工具 (这是代码审查智能体的职责)
❌ 绝对禁止调用 update_verilog_code 工具 (不存在的工具)
❌ 绝对禁止调用 run_simulation 工具 (这是代码审查智能体的职责)
❌ 绝对禁止调用 validate_code 工具 (不存在的工具)

✅ 只能调用设计相关工具:
- analyze_design_requirements: 分析设计需求
- generate_verilog_code: 生成Verilog代码
- search_existing_modules: 搜索现有模块
- analyze_code_quality: 分析代码质量
- validate_design_specifications: 验证设计规格
- generate_design_documentation: 生成设计文档
- optimize_verilog_code: 优化代码
- write_file: 保存文件
- read_file: 读取文件

⚠️ 重要提醒: 如果用户要求生成测试台，请明确回复："测试台生成由代码审查智能体负责，我只负责设计代码的生成。"""
            
            self.add_message("verilog_agent", "system_prompt", verilog_system_prompt)
            
            # Verilog智能体收到包含提醒的用户请求
            enhanced_user_request = f"""请根据以下需求生成Verilog设计：
{user_request}

🚨 **每次工具调用前的重要检查清单**:
❌ 我不能调用 `generate_testbench` 工具
❌ 我不能调用 `update_verilog_code` 工具  
❌ 我不能调用 `run_simulation` 工具
❌ 我不能调用 `validate_code` 工具

✅ 我只能调用已注册的设计工具: 
   analyze_design_requirements, generate_verilog_code, search_existing_modules, 
   analyze_code_quality, validate_design_specifications, generate_design_documentation, 
   optimize_verilog_code, write_file, read_file

现在请严格按照可用工具列表进行工具调用，开始设计任务："""
            
            self.add_message("verilog_agent", "user_prompt", enhanced_user_request)
            
            # === 第5步: Verilog智能体执行设计工具调用 ===
            # 5.1: 分析设计需求
            self.add_message("verilog_agent", "tool_call",
                           "深入分析用户的设计需求和技术规格",
                           tool_info={
                               "tool_name": "analyze_design_requirements",
                               "parameters": {
                                   "requirements": user_request,
                                   "design_type": "sequential" if "counter" in user_request.lower() else "mixed",
                                   "complexity_level": "medium"
                               },
                               "success": True,
                               "result": """✅ 需求分析完成：
- 设计类型: 时序逻辑设计
- 模块功能: 计数器功能实现
- 接口需求: 时钟、复位、使能信号输入，计数值输出
- 技术要求: 可综合、符合IEEE 1800标准
- 复杂度评估: 中等复杂度，预计10-20行代码"""
                           })
            
            # 5.2: 生成Verilog代码
            module_name = "counter" if "counter" in user_request.lower() else "design_module"
            self.add_message("verilog_agent", "tool_call",
                           "生成高质量的Verilog设计代码",
                           tool_info={
                               "tool_name": "generate_verilog_code",
                               "parameters": {
                                   "module_name": module_name,
                                   "requirements": user_request,
                                   "input_ports": [
                                       {"name": "clk", "width": 1, "description": "时钟信号，上升沿触发"},
                                       {"name": "rst", "width": 1, "description": "异步复位信号，低有效"},
                                       {"name": "enable", "width": 1, "description": "使能信号，高有效"}
                                   ],
                                   "output_ports": [
                                       {"name": "count", "width": 8, "description": "8位计数输出，范围0-255"}
                                   ],
                                   "clock_domain": {
                                       "clock_name": "clk",
                                       "reset_name": "rst", 
                                       "reset_active": "low"
                                   },
                                   "coding_style": "rtl",
                                   "comments_required": True
                               },
                               "success": True,
                               "result": f"""✅ Verilog代码生成成功！

生成的模块特性:
- 模块名称: {module_name}
- 接口: 3个输入端口(clk, rst, enable), 1个输出端口(count[7:0])
- 功能: 8位同步计数器，支持异步复位和使能控制
- 代码行数: 18行
- 注释覆盖率: 85%
- 综合兼容性: ✅ 支持主流FPGA工具链

文件已保存到: ./designs/{module_name}.v"""
                           })
            
            # 5.3: 保存文件
            sample_verilog_code = f"""// 8位同步计数器模块
// 作者: Enhanced Verilog Agent
// 日期: {datetime.now().strftime('%Y-%m-%d')}

module {module_name} (
    input  wire        clk,     // 系统时钟
    input  wire        rst,     // 异步复位 (低有效)
    input  wire        enable,  // 计数使能
    output reg  [7:0]  count    // 8位计数输出
);

    // 异步复位，同步计数
    always @(posedge clk or negedge rst) begin
        if (!rst) begin
            count <= 8'b0;  // 复位时清零
        end else if (enable) begin
            count <= count + 1'b1;  // 使能时递增
        end
        // 使能无效时保持当前值
    end

endmodule"""
            
            self.add_message("verilog_agent", "tool_call",
                           "保存生成的Verilog设计文件",
                           tool_info={
                               "tool_name": "write_file",
                               "parameters": {
                                   "filename": f"{module_name}.v",
                                   "content": sample_verilog_code,
                                   "description": f"生成的{module_name}模块Verilog代码"
                               },
                               "success": True,
                               "result": f"""✅ 文件保存成功!

文件信息:
- 路径: ./designs/{module_name}.v
- 大小: {len(sample_verilog_code)} bytes
- 文件ID: FILE_001
- 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 校验状态: ✅ 语法检查通过"""
                           })
            
            # 5.4: 生成设计文档
            self.add_message("verilog_agent", "tool_call",
                           "生成完整的设计文档",
                           tool_info={
                               "tool_name": "generate_design_documentation",
                               "parameters": {
                                   "module_name": module_name,
                                   "verilog_code": sample_verilog_code,
                                   "requirements": user_request,
                                   "design_type": "sequential"
                               },
                               "success": True,
                               "result": f"""✅ 设计文档生成完成!

文档内容包括:
- 模块概述和功能描述
- 接口信号定义和时序图
- 内部架构和实现细节  
- 使用说明和实例化示例
- 综合约束和时序要求
- 测试建议和验证要点

文档已保存到: ./reports/{module_name}_design_doc.md"""
                           })
            
            # === 第6步: 如果需要验证，协调器分配测试任务给代码审查智能体 ===
            if any(keyword in user_request.lower() for keyword in ["验证", "测试", "testbench", "仿真"]):
                self.add_message("coordinator", "tool_call",
                               "检测到验证需求，分配测试任务给代码审查智能体", 
                               tool_info={
                                   "tool_name": "assign_task_to_agent",
                                   "parameters": {
                                       "agent_id": "enhanced_real_code_review_agent",
                                       "task_description": f"为{module_name}模块生成测试台并执行仿真验证",
                                       "input_files": [f"./designs/{module_name}.v"],
                                       "task_priority": "high",
                                       "verification_requirements": ["functional_test", "timing_analysis", "coverage_report"]
                                   },
                                   "success": True,
                                   "result": "✅ 验证任务已成功分配给代码审查智能体。任务ID: TASK_002, 预期完成时间: 3-5分钟"
                               })
                
                # === 第7步: 代码审查智能体执行验证 ===
                review_system_prompt = """你是专业的Verilog代码审查和测试专家，负责：
- 生成全面的测试台 (testbench)
- 执行仿真验证和功能测试
- 分析测试结果和覆盖率报告
- 提供代码质量评估和改进建议
- 生成验证报告和测试文档

✅ 可用工具:
- generate_testbench: 生成测试台文件
- run_simulation: 执行仿真验证
- analyze_code_quality: 分析代码质量
- use_external_testbench: 使用外部测试台
- generate_build_script: 生成构建脚本
- write_file: 保存文件
- read_file: 读取文件

工作原则:
1. 生成全面的测试用例，覆盖所有功能场景
2. 执行多种仿真验证（功能、时序、极限测试）
3. 提供详细的测试报告和质量评估
4. 确保设计满足所有技术要求"""
                
                self.add_message("review_agent", "system_prompt", review_system_prompt)
                
                self.add_message("review_agent", "user_prompt", 
                               f"""请为{module_name}模块执行完整的验证流程：

1. 生成全面的测试台文件
2. 执行功能仿真验证
3. 生成测试报告

设计文件路径: ./designs/{module_name}.v

请确保测试覆盖以下场景:
- 复位功能测试
- 正常计数功能
- 使能控制测试
- 边界条件测试""")
                
                # 7.1: 生成测试台
                self.add_message("review_agent", "tool_call",
                               "生成全面的测试台文件",
                               tool_info={
                                   "tool_name": "generate_testbench",
                                   "parameters": {
                                       "module_name": module_name,
                                       "module_code": sample_verilog_code,
                                       "testbench_name": f"{module_name}_tb",
                                       "test_scenarios": ["reset_test", "count_test", "enable_test", "overflow_test"],
                                       "simulation_time": "1000ns",
                                       "clock_period": "10ns"
                                   },
                                   "success": True,
                                   "result": f"""✅ 测试台生成成功!

测试台特性:
- 文件名: {module_name}_tb.v
- 测试场景: 4个主要测试用例
- 时钟频率: 100MHz (周期10ns)
- 仿真时长: 1000ns (100个时钟周期)
- 测试覆盖率: 预计95%+

生成的测试用例:
1. 复位测试: 验证异步复位功能
2. 计数测试: 验证正常递增计数
3. 使能测试: 验证使能控制逻辑
4. 溢出测试: 验证计数器回绕行为

文件已保存到: ./testbenches/{module_name}_tb.v"""
                               })
                
                # 7.2: 执行仿真
                self.add_message("review_agent", "tool_call",
                               "执行仿真验证测试",
                               tool_info={
                                   "tool_name": "run_simulation",
                                   "parameters": {
                                       "design_file": f"./designs/{module_name}.v",
                                       "testbench_file": f"./testbenches/{module_name}_tb.v",
                                       "simulation_time": "1000ns",
                                       "simulator": "iverilog",
                                       "output_format": "vcd"
                                   },
                                   "success": True,
                                   "result": f"""✅ 仿真执行成功!

仿真结果摘要:
- 仿真工具: Icarus Verilog
- 仿真时长: 1000ns (实际用时: 0.234秒)
- 测试状态: 全部通过 ✅
- 波形文件: ./simulation/{module_name}_tb.vcd

详细测试结果:
📋 复位测试: ✅ PASS (计数器正确复位为0)
📋 计数测试: ✅ PASS (0→255正常递增)
📋 使能测试: ✅ PASS (使能控制工作正常)
📋 溢出测试: ✅ PASS (255→0回绕正确)

性能指标:
- 最大工作频率: >200MHz
- 资源消耗: 8个FF, 7个LUT
- 功耗估算: 0.1mW @100MHz"""
                               })
                
                # 7.3: 生成测试报告
                self.add_message("review_agent", "tool_call",
                               "生成详细的验证报告",
                               tool_info={
                                   "tool_name": "write_file",
                                   "parameters": {
                                       "filename": f"{module_name}_verification_report.md",
                                       "content": f"# {module_name.title()} 模块验证报告\n\n## 测试摘要\n- 所有测试用例通过\n- 功能验证完成\n- 性能指标满足要求",
                                       "description": f"{module_name}模块完整验证报告"
                                   },
                                   "success": True,
                                   "result": f"""✅ 验证报告生成完成!

报告内容:
- 测试执行摘要
- 功能验证结果
- 性能分析数据
- 代码质量评估
- 改进建议和结论

报告已保存到: ./reports/{module_name}_verification_report.md"""
                               })
            
            # === 第8步: 协调器提供最终结果 ===
            final_result = f"""🎉 {module_name.title()}模块设计和验证全部完成!

📁 生成的文件清单:
✅ ./designs/{module_name}.v - 主设计文件
✅ ./reports/{module_name}_design_doc.md - 设计文档"""
            
            if any(keyword in user_request.lower() for keyword in ["验证", "测试", "testbench", "仿真"]):
                final_result += f"""
✅ ./testbenches/{module_name}_tb.v - 测试台文件
✅ ./simulation/{module_name}_tb.vcd - 仿真波形
✅ ./reports/{module_name}_verification_report.md - 验证报告

🧪 验证结果摘要:
- 功能测试: ✅ 全部通过
- 时序分析: ✅ 满足要求  
- 代码质量: ✅ 高质量代码
- 综合兼容: ✅ 支持主流工具链"""
            
            final_result += f"""

💡 后续建议:
1. 可以在FPGA开发板上进行硬件验证
2. 根据实际需求调整位宽和功能
3. 考虑添加更多控制信号
4. 进行功耗和面积优化

总耗时: 约3-5分钟 | 智能体协作: 成功 ✅"""
            
            self.add_message("coordinator", "assistant_response", final_result)
        
        else:
            # 处理其他类型的请求
            self.add_message("coordinator", "assistant_response", 
                           "请提供更具体的Verilog设计需求，例如：'设计一个8位计数器模块'或'创建一个状态机控制器'")
        
        return self._generate_html_report()
    
    def _generate_html_report(self) -> str:
        """生成完整的HTML可视化报告"""
        
        # 生成CSS样式
        css_styles = """
<style>
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    min-height: 100vh;
}

.header {
    text-align: center;
    padding: 30px;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 15px;
    margin-bottom: 30px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

.header h1 {
    margin: 0;
    font-size: 2.5em;
    font-weight: 300;
}

.header p {
    margin: 15px 0 0 0;
    font-size: 1.2em;
    opacity: 0.9;
}

.timeline {
    position: relative;
    padding-left: 30px;
}

.timeline::before {
    content: '';
    position: absolute;
    left: 15px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: linear-gradient(to bottom, #667eea, #764ba2);
}

.message {
    position: relative;
    margin: 20px 0;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    background: white;
    margin-left: 30px;
}

.message::before {
    content: '';
    position: absolute;
    left: -45px;
    top: 20px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: white;
    border: 3px solid;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.system-prompt {
    border-left: 5px solid #ff6b6b;
    background: linear-gradient(135deg, #fff5f5 0%, #ffe0e0 100%);
}
.system-prompt::before { border-color: #ff6b6b; }

.user-prompt {
    border-left: 5px solid #4ecdc4;
    background: linear-gradient(135deg, #f0fdfc 0%, #e0f9f5 100%);
}
.user-prompt::before { border-color: #4ecdc4; }

.tool-call {
    border-left: 5px solid #45b7d1;
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2ff 100%);
}
.tool-call::before { border-color: #45b7d1; }

.tool-call.error {
    border-left-color: #ff6b6b;
    background: linear-gradient(135deg, #fff5f5 0%, #ffe0e0 100%);
}
.tool-call.error::before { border-color: #ff6b6b; }

.assistant-response {
    border-left: 5px solid #95a5a6;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}
.assistant-response::before { border-color: #95a5a6; }

.other {
    border-left: 5px solid #bdc3c7;
    background: linear-gradient(135deg, #ecf0f1 0%, #d5dbdb 100%);
}
.other::before { border-color: #bdc3c7; }

.message-header {
    display: flex;
    align-items: center;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(0,0,0,0.1);
}

.message-header .icon {
    font-size: 1.5em;
    margin-right: 10px;
}

.message-header .title {
    font-weight: 600;
    font-size: 1.1em;
    flex-grow: 1;
}

.message-header .timestamp {
    font-size: 0.9em;
    color: #666;
    background: rgba(0,0,0,0.05);
    padding: 4px 10px;
    border-radius: 15px;
}

.message-content {
    font-size: 0.95em;
    line-height: 1.6;
}

.code-content, .json-content {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 6px;
    padding: 15px;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 0.85em;
    overflow-x: auto;
    max-height: 300px;
    overflow-y: auto;
    white-space: pre-wrap;
    margin: 10px 0;
}

.tool-name {
    font-weight: 600;
    color: #2c3e50;
    margin-bottom: 10px;
    font-size: 1.05em;
}

.tool-details {
    margin: 15px 0;
}

.tool-details summary {
    cursor: pointer;
    font-weight: 500;
    color: #666;
    padding: 5px 0;
    user-select: none;
}

.tool-details summary:hover {
    color: #333;
}

.tool-result {
    margin-top: 15px;
}

.result-content {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 6px;
    padding: 12px;
    margin-top: 8px;
    max-height: 200px;
    overflow-y: auto;
}

.stats {
    background: white;
    padding: 25px;
    border-radius: 10px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    margin: 30px 0;
}

.stats h3 {
    margin-top: 0;
    color: #2c3e50;
    text-align: center;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.stat-card {
    text-align: center;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.stat-number {
    font-size: 2.5em;
    font-weight: bold;
    margin-bottom: 5px;
}

.stat-label {
    font-size: 0.9em;
    opacity: 0.9;
}

.workflow {
    background: white;
    padding: 20px;
    border-radius: 10px;
    margin-top: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    text-align: center;
}

.workflow-steps {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 15px;
}

.workflow-step {
    padding: 8px 15px;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 20px;
    font-size: 0.9em;
    color: #495057;
    border: 1px solid #dee2e6;
}

.footer {
    text-align: center;
    padding: 30px;
    color: #666;
    border-top: 1px solid #dee2e6;
    margin-top: 50px;
}

@media (max-width: 768px) {
    body {
        padding: 10px;
    }
    
    .message {
        margin-left: 20px;
        padding: 15px;
    }
    
    .timeline {
        padding-left: 20px;
    }
    
    .timeline::before {
        left: 10px;
    }
    
    .message::before {
        left: -35px;
    }
    
    .stats-grid {
        grid-template-columns: 1fr;
    }
    
    .workflow-steps {
        flex-direction: column;
        align-items: center;
    }
}
</style>
"""
        
        # 生成消息内容
        messages_html = ""
        for msg in self.conversation_history:
            messages_html += self.format_message_display(msg)
        
        # 生成统计信息
        stats = {
            "总消息数": len(self.conversation_history),
            "System Prompt": len([m for m in self.conversation_history if m['type'] == 'system_prompt']),
            "User Prompt": len([m for m in self.conversation_history if m['type'] == 'user_prompt']),
            "工具调用": len([m for m in self.conversation_history if m['type'] == 'tool_call']),
            "Assistant Response": len([m for m in self.conversation_history if m['type'] == 'assistant_response'])
        }
        
        stats_html = f"""
<div class="stats">
    <h3>📊 对话统计分析</h3>
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{stats['总消息数']}</div>
            <div class="stat-label">总消息数</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{stats['System Prompt']}</div>
            <div class="stat-label">System Prompt</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{stats['User Prompt']}</div>
            <div class="stat-label">User Prompt</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{stats['工具调用']}</div>
            <div class="stat-label">工具调用</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{stats['Assistant Response']}</div>
            <div class="stat-label">Assistant Response</div>
        </div>
    </div>
    
    <div class="workflow">
        <h4>🔄 多智能体协作工作流程</h4>
        <div class="workflow-steps">
            <span class="workflow-step">👤 用户请求</span>
            <span>→</span>
            <span class="workflow-step">🧠 协调器分析</span>
            <span>→</span>
            <span class="workflow-step">🔧 Verilog设计</span>
            <span>→</span>
            <span class="workflow-step">🧪 代码审查</span>
            <span>→</span>
            <span class="workflow-step">✅ 任务完成</span>
        </div>
    </div>
</div>
"""
        
        # 组装完整HTML
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>多智能体协作对话可视化</title>
    {css_styles}
</head>
<body>
    <div class="header">
        <h1>🤖 多智能体协作对话可视化</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    {stats_html}
    
    <div class="timeline">
        {messages_html}
    </div>
    
    <div class="footer">
        <p>🔧 多智能体协作框架可视化工具 | 帮助理解Verilog设计智能体工作流程</p>
        <p>可视化内容包括: System Prompt, User Prompt, 工具调用详情, Assistant Response</p>
    </div>
</body>
</html>
"""
        
        return html_content

def main():
    """主函数"""
    print("🚀 静态多智能体协作对话可视化工具")
    print("=" * 60)
    
    visualizer = StaticAgentVisualizer()
    
    # 测试用例
    test_cases = [
        "请设计一个8位counter模块",
        "设计一个counter模块并生成测试台验证",
        "创建一个带使能和复位的计数器并进行仿真测试"
    ]
    
    print("\n可选择的测试用例:")
    for i, case in enumerate(test_cases, 1):
        print(f"{i}. {case}")
    
    print("\n输入选项:")
    print("- 输入数字1-3选择预设测试用例")
    print("- 直接输入自定义需求")
    print("- 输入 'q' 退出")
    
    while True:
        user_input = input("\n请输入: ").strip()
        
        if user_input.lower() == 'q':
            print("👋 再见!")
            break
        
        if user_input.isdigit() and 1 <= int(user_input) <= 3:
            user_request = test_cases[int(user_input) - 1]
        else:
            user_request = user_input
        
        if not user_request:
            print("❌ 请输入有效的需求")
            continue
        
        print(f"\n🔄 开始模拟对话: {user_request}")
        print("⏳ 正在生成可视化报告...")
        
        try:
            html_content = visualizer.simulate_conversation(user_request)
            
            # 保存HTML文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"agent_conversation_{timestamp}.html"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ 可视化报告已生成: {filename}")
            print(f"📊 包含 {len(visualizer.conversation_history)} 条对话消息")
            print(f"🌐 请用浏览器打开 {filename} 文件查看可视化结果")
            
            # 显示统计信息
            stats = {
                "System Prompt": len([m for m in visualizer.conversation_history if m['type'] == 'system_prompt']),
                "User Prompt": len([m for m in visualizer.conversation_history if m['type'] == 'user_prompt']),
                "工具调用": len([m for m in visualizer.conversation_history if m['type'] == 'tool_call']),
                "Assistant Response": len([m for m in visualizer.conversation_history if m['type'] == 'assistant_response'])
            }
            
            print("\n📈 对话统计:")
            for key, value in stats.items():
                print(f"  - {key}: {value}")
            
        except Exception as e:
            print(f"❌ 生成失败: {str(e)}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    main()