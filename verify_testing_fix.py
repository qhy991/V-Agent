#!/usr/bin/env python3
"""
验证修复后的测试功能

Verify Fixed Testing Functionality
"""

import asyncio
from pathlib import Path

from agents.real_code_reviewer import RealCodeReviewAgent
from core.base_agent import TaskMessage

async def test_fixed_functionality():
    """验证修复后的测试功能"""
    
    print("🔧 验证修复后的Verilog测试功能")
    print("=" * 50)
    
    try:
        # 1. 创建审查智能体
        reviewer = RealCodeReviewAgent()
        
        # 2. 读取ALU文件内容（包含markdown格式）
        alu_file = Path("./output/alu_32bit.v")
        if not alu_file.exists():
            print("❌ ALU文件不存在")
            return False
        
        alu_content = alu_file.read_text(encoding='utf-8')
        print(f"📄 ALU文件大小: {len(alu_content)} 字符")
        
        # 3. 准备测试数据
        file_contents = {
            "output/alu_32bit.v": {
                "type": "verilog", 
                "content": alu_content
            }
        }
        
        # 4. 测试触发条件检查
        prompt = "请对ALU模块进行全面的代码审查，重点关注语法正确性、设计质量、时序考虑和最佳实践"
        should_test = reviewer._should_perform_testing(prompt, {"alu_32bit.v": alu_content})
        print(f"✅ 测试触发检查: {should_test}")
        
        # 5. 测试模块可测试性检查
        is_testable = reviewer._is_testable_module(alu_content)
        print(f"✅ 模块可测试性: {is_testable}")
        
        # 6. 测试模块信息解析
        module_info = reviewer._parse_module_info(alu_content)
        print(f"✅ 模块信息解析: {module_info}")
        
        # 7. 如果都通过，执行完整的审查任务
        if should_test and is_testable:
            print("\n🧪 执行完整的代码审查和测试...")
            
            task_message = TaskMessage(
                task_id="test_fix_verification",
                sender_id="test_runner",
                receiver_id="real_code_review_agent", 
                message_type="task_execution",
                content="请对这个ALU模块进行全面审查并生成测试台进行功能验证",
                metadata={"test_mode": True}
            )
            
            result = await reviewer.execute_enhanced_task(
                enhanced_prompt="请对ALU模块进行全面的代码审查，包括语法检查、设计质量评估，并生成完整的测试台验证其功能正确性",
                original_message=task_message,
                file_contents=file_contents
            )
            
            if "formatted_response" in result:
                import json
                try:
                    response_data = json.loads(result["formatted_response"])
                    testing_performed = response_data.get('metadata', {}).get('testing_performed', False)
                    total_tests = response_data.get('metadata', {}).get('total_tests', 0)
                    
                    print(f"✅ 审查任务完成")
                    print(f"   - 测试执行: {'是' if testing_performed else '否'}")
                    print(f"   - 测试数量: {total_tests}")
                    
                    if testing_performed:
                        print("🎉 测试功能修复成功！")
                        return True
                    else:
                        print("⚠️ 测试功能仍未执行")
                        return False
                        
                except json.JSONDecodeError as e:
                    print(f"❌ 响应解析失败: {e}")
                    return False
            else:
                print("❌ 未找到格式化响应")
                return False
        else:
            print("❌ 触发条件或可测试性检查失败")
            return False
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_fixed_functionality())
    print(f"\n{'✅' if success else '❌'} 验证结果: {'成功' if success else '失败'}")