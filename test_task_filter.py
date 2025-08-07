#!/usr/bin/env python3
"""
测试任务描述过滤逻辑
"""

import re

def _filter_task_description_by_agent(task_description: str, agent_id: str) -> str:
    """根据目标智能体过滤任务描述，移除不合适的要求"""
    
    if agent_id == "enhanced_real_verilog_agent":
        # 🔧 修正: 为Verilog设计智能体移除测试台生成相关要求 - 使用更直接的方法
        original_desc = task_description
        
        # 🔧 方法1: 直接字符串替换，移除常见的测试台相关表述
        filtered_desc = task_description
        
        # 移除常见的测试台相关短语
        testbench_phrases = [
            "和测试台",
            "、测试台", 
            "以及测试台",
            "还有测试台",
            "包含测试台",
            "生成测试台",
            "创建测试台",
            "编写测试台"
        ]
        
        for phrase in testbench_phrases:
            filtered_desc = filtered_desc.replace(phrase, "")
        
        # 🔧 方法2: 使用正则表达式清理
        testbench_patterns = [
            r"，包含完整的端口定义、功能实现和测试台",
            r"包含完整的端口定义、功能实现和测试台",
            r"生成.*?测试台.*?进行验证",
            r"并.*?生成.*?测试台",
            r"以及.*?测试台",
            r"和.*?测试台", 
            r"、.*?测试台"
        ]
        
        for pattern in testbench_patterns:
            filtered_desc = re.sub(pattern, "", filtered_desc, flags=re.IGNORECASE)
        
        # 🔧 方法3: 清理多余的标点符号
        filtered_desc = re.sub(r"，\s*$", "", filtered_desc)  # 移除末尾逗号
        filtered_desc = re.sub(r"、\s*$", "", filtered_desc)  # 移除末尾顿号
        filtered_desc = re.sub(r"和\s*$", "", filtered_desc)  # 移除末尾"和"
        filtered_desc = filtered_desc.strip()
        
        # 检查是否原来包含测试台要求
        has_testbench_requirement = ("测试台" in original_desc or 
                                   "testbench" in original_desc.lower() or 
                                   "验证" in original_desc)
        
        # 如果原来包含测试台要求，添加明确的职责说明
        if has_testbench_requirement:
            if filtered_desc:
                filtered_desc += """

🚨 **重要说明**: 
- 本任务仅要求完成Verilog模块设计和代码生成
- 测试台(testbench)生成和验证工作将由后续的代码审查智能体负责
- 请专注于设计模块的端口定义、功能实现和代码质量"""
            else:
                # 如果过滤后为空，提供默认的设计任务描述
                filtered_desc = """设计Verilog模块，专注于模块架构和功能实现

🚨 **重要说明**: 
- 本任务仅要求完成Verilog模块设计和代码生成
- 测试台(testbench)生成和验证工作将由后续的代码审查智能体负责
- 请专注于设计模块的端口定义、功能实现和代码质量"""
        
        return filtered_desc.strip()
    
    elif agent_id == "enhanced_real_code_review_agent":
        # 代码审查智能体保持原始任务描述
        return task_description
    
    return task_description

def test_task_filtering():
    """测试任务描述过滤功能"""
    
    # 测试用例1: 协调器生成的问题任务描述
    test_case_1 = "设计一个名为counter的Verilog模块，包含完整的端口定义、功能实现和测试台"
    result_1 = _filter_task_description_by_agent(test_case_1, "enhanced_real_verilog_agent")
    print("🧪 测试用例1：")
    print(f"原始: {test_case_1}")
    print(f"过滤后: {result_1}")
    # 检查任务描述部分（不包括重要说明）是否包含测试台
    task_part_1 = result_1.split("🚨 **重要说明**")[0].strip()
    testbench_removed_1 = "测试台" not in task_part_1
    print(f"任务描述部分是否移除测试台: {'✅ 成功' if testbench_removed_1 else '❌ 失败'}")
    print()
    
    # 测试用例2: 其他格式的测试台要求
    test_case_2 = "请设计counter模块并生成对应的测试台进行验证"
    result_2 = _filter_task_description_by_agent(test_case_2, "enhanced_real_verilog_agent")
    print("🧪 测试用例2：")
    print(f"原始: {test_case_2}")
    print(f"过滤后: {result_2}")
    task_part_2 = result_2.split("🚨 **重要说明**")[0].strip()
    testbench_removed_2 = "测试台" not in task_part_2
    print(f"任务描述部分是否移除测试台: {'✅ 成功' if testbench_removed_2 else '❌ 失败'}")
    print()
    
    # 测试用例3: 不包含测试台的正常任务
    test_case_3 = "设计一个名为counter的Verilog模块，实现计数功能"
    result_3 = _filter_task_description_by_agent(test_case_3, "enhanced_real_verilog_agent")
    print("🧪 测试用例3：")
    print(f"原始: {test_case_3}")
    print(f"过滤后: {result_3}")
    unchanged_3 = result_3 == test_case_3
    print(f"是否保持不变: {'✅ 成功' if unchanged_3 else '❌ 失败'}")
    print()
    
    # 测试用例4: 代码审查智能体应保持原样
    test_case_4 = "审查counter模块并生成测试台进行验证"
    result_4 = _filter_task_description_by_agent(test_case_4, "enhanced_real_code_review_agent")
    print("🧪 测试用例4（代码审查智能体）：")
    print(f"原始: {test_case_4}")
    print(f"过滤后: {result_4}")
    unchanged_4 = result_4 == test_case_4
    print(f"是否保持不变: {'✅ 成功' if unchanged_4 else '❌ 失败'}")
    print()
    
    # 汇总结果
    print("📊 测试结果汇总：")
    print(f"测试用例1 - Verilog智能体测试台过滤: {'✅ 成功' if testbench_removed_1 else '❌ 失败'}")
    print(f"测试用例2 - Verilog智能体测试台过滤: {'✅ 成功' if testbench_removed_2 else '❌ 失败'}")
    print(f"测试用例3 - 正常任务保持不变: {'✅ 成功' if unchanged_3 else '❌ 失败'}")
    print(f"测试用例4 - 代码审查智能体保持原样: {'✅ 成功' if unchanged_4 else '❌ 失败'}")

if __name__ == "__main__":
    test_task_filtering()