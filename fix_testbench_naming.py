#!/usr/bin/env python3
"""
修复测试台名称硬编码问题

问题分析：
1. 代码审查智能体的系统提示中硬编码了 "simple_adder" 作为示例
2. LLM在生成工具调用时直接复制了示例中的模块名
3. 导致ALU实验生成了错误的测试台名称
"""

import re
import sys
from pathlib import Path

def fix_system_prompt_hardcoded_examples():
    """修复系统提示中的硬编码示例"""
    print("🔧 修复系统提示中的硬编码示例...")
    
    # 修复代码审查智能体
    review_agent_file = Path("agents/enhanced_real_code_reviewer.py")
    if not review_agent_file.exists():
        print("❌ 找不到 enhanced_real_code_reviewer.py 文件")
        return False
    
    with open(review_agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换硬编码的示例
    old_examples = [
        '"module_name": "simple_adder"',
        '"code": "module simple_adder(...); endmodule"',
        '"verilog_code": "module simple_adder(...); endmodule"'
    ]
    
    new_examples = [
        '"module_name": "target_module"',
        '"code": "module target_module(...); endmodule"',
        '"verilog_code": "module target_module(...); endmodule"'
    ]
    
    modified = False
    for old, new in zip(old_examples, new_examples):
        if old in content:
            content = content.replace(old, new)
            modified = True
            print(f"✅ 替换: {old} -> {new}")
    
    if modified:
        with open(review_agent_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ 代码审查智能体系统提示修复完成")
        return True
    else:
        print("⚠️ 未找到需要修复的硬编码示例")
        return True

def fix_verilog_agent_hardcoded_examples():
    """修复Verilog智能体中的硬编码示例"""
    print("🔧 修复Verilog智能体中的硬编码示例...")
    
    verilog_agent_file = Path("agents/enhanced_real_verilog_agent.py")
    if not verilog_agent_file.exists():
        print("❌ 找不到 enhanced_real_verilog_agent.py 文件")
        return False
    
    with open(verilog_agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换硬编码的示例
    old_examples = [
        '"module_name": "simple_adder"',
        '"requirements": "设计一个8位加法器"',
        '"input_ports": ["a [7:0]", "b [7:0]", "cin"]',
        '"output_ports": ["sum [7:0]", "cout"]'
    ]
    
    new_examples = [
        '"module_name": "target_module"',
        '"requirements": "设计目标模块"',
        '"input_ports": ["input1 [7:0]", "input2 [7:0]", "ctrl"]',
        '"output_ports": ["output1 [7:0]", "status"]'
    ]
    
    modified = False
    for old, new in zip(old_examples, new_examples):
        if old in content:
            content = content.replace(old, new)
            modified = True
            print(f"✅ 替换: {old} -> {new}")
    
    if modified:
        with open(verilog_agent_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Verilog智能体系统提示修复完成")
        return True
    else:
        print("⚠️ 未找到需要修复的硬编码示例")
        return True

def add_dynamic_module_name_extraction():
    """添加动态模块名提取功能"""
    print("🔧 添加动态模块名提取功能...")
    
    review_agent_file = Path("agents/enhanced_real_code_reviewer.py")
    if not review_agent_file.exists():
        print("❌ 找不到 enhanced_real_code_reviewer.py 文件")
        return False
    
    with open(review_agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经有模块名提取功能
    if 'def _extract_module_name' in content:
        print("✅ 模块名提取功能已存在")
        return True
    
    # 添加模块名提取方法
    extract_method = '''
    def _extract_module_name_from_code(self, verilog_code: str) -> str:
        """从Verilog代码中提取模块名"""
        import re
        
        # 匹配module声明
        module_pattern = r'module\\s+(\\w+)\\s*\\('
        match = re.search(module_pattern, verilog_code, re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        # 如果没有找到，返回默认名称
        return "unknown_module"
    
    def _validate_and_fix_module_name(self, provided_name: str, verilog_code: str) -> str:
        """验证并修复模块名"""
        extracted_name = self._extract_module_name_from_code(verilog_code)
        
        if provided_name and provided_name != extracted_name:
            self.logger.warning(f"⚠️ 模块名不匹配: 提供={provided_name}, 提取={extracted_name}")
            return extracted_name
        
        return provided_name or extracted_name
'''
    
    # 在类中添加方法
    insert_pos = content.find('    def _build_enhanced_system_prompt(self) -> str:')
    if insert_pos != -1:
        content = content[:insert_pos] + extract_method + content[insert_pos:]
        
        with open(review_agent_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ 动态模块名提取功能添加完成")
        return True
    
    print("⚠️ 无法找到合适的插入位置")
    return False

def update_testbench_generation_logic():
    """更新测试台生成逻辑以使用动态模块名"""
    print("🔧 更新测试台生成逻辑...")
    
    review_agent_file = Path("agents/enhanced_real_code_reviewer.py")
    if not review_agent_file.exists():
        print("❌ 找不到 enhanced_real_code_reviewer.py 文件")
        return False
    
    with open(review_agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找测试台生成方法的开始
    method_start = 'async def _tool_generate_testbench(self, module_name: str, module_code: str,'
    if method_start not in content:
        print("❌ 找不到测试台生成方法")
        return False
    
    # 在方法开始后添加模块名验证逻辑
    validation_code = '''
        """生成测试台工具实现"""
        try:
            # 验证并修复模块名
            actual_module_name = self._validate_and_fix_module_name(module_name, module_code)
            if actual_module_name != module_name:
                self.logger.info(f"🔧 模块名已修正: {module_name} -> {actual_module_name}")
                module_name = actual_module_name
            
            self.logger.info(f"🧪 生成测试台: {module_name}")
'''
    
    # 替换方法开始部分
    old_start = '''async def _tool_generate_testbench(self, module_name: str, module_code: str,
                                     test_scenarios: List[Dict] = None,
                                     clock_period: float = 10.0,
                                     simulation_time: int = 10000,
                                     coverage_options: Dict = None) -> Dict[str, Any]:
        """生成测试台工具实现"""
        try:
            self.logger.info(f"🧪 生成测试台: {module_name}")'''
    
    new_start = '''async def _tool_generate_testbench(self, module_name: str, module_code: str,
                                     test_scenarios: List[Dict] = None,
                                     clock_period: float = 10.0,
                                     simulation_time: int = 10000,
                                     coverage_options: Dict = None) -> Dict[str, Any]:''' + validation_code
    
    if old_start in content:
        content = content.replace(old_start, new_start)
        
        with open(review_agent_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ 测试台生成逻辑更新完成")
        return True
    else:
        print("⚠️ 无法找到需要替换的方法开始部分")
        return False

def create_test_script():
    """创建测试脚本验证修复效果"""
    print("🔧 创建测试脚本...")
    
    test_script = '''#!/usr/bin/env python3
"""
测试修复后的测试台生成功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent

async def test_testbench_generation():
    """测试测试台生成功能"""
    print("🧪 测试测试台生成功能...")
    
    # 创建配置和智能体
    config = FrameworkConfig.from_env()
    agent = EnhancedRealCodeReviewAgent(config)
    
    # 测试ALU模块
    alu_code = """module alu_32bit (
    input  [31:0] a,        // 操作数A
    input  [31:0] b,        // 操作数B
    input  [3:0]  op,       // 操作码
    output [31:0] result,   // 结果
    output        zero      // 零标志 (result == 0 时为1)
);

    // 根据操作码选择对应的操作
    always @(*) begin
        case (op)
            4'b0000: result = a + b;     // 加法
            4'b0001: result = a - b;     // 减法
            4'b0010: result = a & b;     // 逻辑与
            4'b0011: result = a | b;     // 逻辑或
            4'b0100: result = a ^ b;     // 异或
            4'b0101: result = a << b[4:0]; // 逻辑左移
            4'b0110: result = a >> b[4:0]; // 逻辑右移
            default: result = 32'h00000000; // 其他操作码
        endcase
    end
    
    // 零标志：当结果为0时输出1
    assign zero = (result == 32'h00000000) ? 1'b1 : 1'b0;
    
endmodule"""
    
    # 测试不同的模块名情况
    test_cases = [
        ("alu_32bit", alu_code, "正确模块名"),
        ("wrong_name", alu_code, "错误模块名"),
        ("", alu_code, "空模块名")
    ]
    
    for module_name, code, description in test_cases:
        print(f"\\n📋 测试用例: {description}")
        print(f"   提供模块名: {module_name}")
        
        result = await agent._tool_generate_testbench(
            module_name=module_name,
            module_code=code,
            test_scenarios=[
                {"name": "basic_test", "description": "基本功能测试"},
                {"name": "corner_test", "description": "边界条件测试"}
            ]
        )
        
        if result.get("success"):
            print(f"   ✅ 成功生成测试台")
            print(f"   实际模块名: {result.get('module_name')}")
            print(f"   测试台文件名: {result.get('testbench_filename')}")
        else:
            print(f"   ❌ 生成失败: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_testbench_generation())
'''
    
    test_file = Path("test_testbench_fix.py")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print(f"✅ 测试脚本已创建: {test_file}")

def main():
    """主修复流程"""
    print("🚀 开始修复测试台名称硬编码问题...")
    print("=" * 60)
    
    # 1. 修复系统提示中的硬编码示例
    if not fix_system_prompt_hardcoded_examples():
        print("❌ 系统提示修复失败")
        return False
    
    # 2. 修复Verilog智能体中的硬编码示例
    if not fix_verilog_agent_hardcoded_examples():
        print("❌ Verilog智能体修复失败")
        return False
    
    # 3. 添加动态模块名提取功能
    if not add_dynamic_module_name_extraction():
        print("❌ 动态模块名提取功能添加失败")
        return False
    
    # 4. 更新测试台生成逻辑
    if not update_testbench_generation_logic():
        print("❌ 测试台生成逻辑更新失败")
        return False
    
    # 5. 创建测试脚本
    create_test_script()
    
    print("=" * 60)
    print("✅ 测试台名称硬编码问题修复完成")
    print("📋 修复内容:")
    print("   1. 移除了系统提示中的硬编码 'simple_adder' 示例")
    print("   2. 添加了动态模块名提取功能")
    print("   3. 更新了测试台生成逻辑以使用正确的模块名")
    print("   4. 创建了测试脚本验证修复效果")
    print("\\n🧪 运行测试:")
    print("   python test_testbench_fix.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 