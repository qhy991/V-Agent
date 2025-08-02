#!/usr/bin/env python3
"""
测试增强后的TDD系统
==================================================

验证以下功能:
✅ 中央文件管理器
✅ 智能体间的文件引用传递 
✅ 精确的错误报告
✅ 智能重试机制
"""

import asyncio
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.file_manager import initialize_file_manager, get_file_manager
from agents.enhanced_real_verilog_agent import EnhancedRealVerilogAgent
from extensions.test_analyzer import TestAnalyzer
from extensions.test_driven_coordinator import TestDrivenConfig, create_test_driven_coordinator
from core.enhanced_centralized_coordinator import EnhancedCentralizedCoordinator
from agents.enhanced_real_code_reviewer import EnhancedRealCodeReviewAgent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'test_enhanced_system.log')
    ]
)

logger = logging.getLogger(__name__)


async def test_file_manager():
    """测试中央文件管理器"""
    logger.info("🗂️ 测试中央文件管理器")
    
    # 初始化文件管理器
    workspace = project_root / "test_workspace"
    file_manager = initialize_file_manager(workspace)
    
    # 测试保存文件
    verilog_code = """
module test_counter(
    input clk,
    input rst,
    output reg [7:0] count
);

always @(posedge clk or posedge rst) begin
    if (rst) begin
        count <= 8'b0;
    end else begin
        count <= count + 1;
    end
end

endmodule
"""
    
    file_ref = file_manager.save_file(
        content=verilog_code,
        filename="test_counter.v",
        file_type="verilog",
        created_by="test_system",
        description="测试计数器模块"
    )
    
    logger.info(f"✅ 文件已保存: {file_ref.file_path} (ID: {file_ref.file_id})")
    
    # 测试读取文件
    content = file_manager.read_file_content(file_ref)
    assert content == verilog_code
    logger.info("✅ 文件读取验证通过")
    
    # 测试获取文件列表
    verilog_files = file_manager.get_files_by_type("verilog")
    logger.info(f"✅ 找到 {len(verilog_files)} 个Verilog文件")
    
    return file_ref


async def test_enhanced_verilog_agent():
    """测试增强的Verilog智能体"""
    logger.info("🤖 测试增强的Verilog智能体")
    
    config = FrameworkConfig.from_env()
    agent = EnhancedRealVerilogAgent(config)
    
    # 测试设计任务
    result = await agent.process_with_enhanced_validation(
        "设计一个8位加法器模块，包含进位输出",
        max_iterations=3
    )
    
    logger.info(f"✅ Verilog智能体处理结果: {result.get('success', False)}")
    
    # 检查文件管理器中是否有新文件
    file_manager = get_file_manager()
    latest_files = file_manager.get_latest_files_by_type("verilog", limit=3)
    logger.info(f"✅ 智能体创建了 {len(latest_files)} 个新文件")
    
    return result, latest_files


async def test_enhanced_tdd_workflow():
    """测试增强的TDD工作流"""
    logger.info("🔄 测试增强的TDD工作流")
    
    try:
        # 创建协调器
        base_coordinator = EnhancedCentralizedCoordinator()
        
        # 注册智能体
        config = FrameworkConfig.from_env()
        verilog_agent = EnhancedRealVerilogAgent(config)
        code_reviewer = EnhancedRealCodeReviewAgent(config)
        
        base_coordinator.register_agent(verilog_agent)
        base_coordinator.register_agent(code_reviewer)
        
        # 创建TDD协调器
        tdd_config = TestDrivenConfig(max_iterations=3, save_iteration_logs=True)
        tdd_coordinator = create_test_driven_coordinator(base_coordinator, tdd_config)
        
        # 执行TDD任务
        result = await tdd_coordinator.execute_test_driven_task(
            "设计一个简单的全加器模块，支持单位加法运算"
        )
        
        logger.info(f"✅ TDD工作流完成: {result.get('success', False)}")
        logger.info(f"📄 最终设计文件: {len(result.get('final_design', []))} 个") 
        
        return result
        
    except Exception as e:
        logger.error(f"❌ TDD工作流测试失败: {e}")
        return {"success": False, "error": str(e)}


async def test_error_reporting():
    """测试错误报告功能"""
    logger.info("📊 测试错误报告功能")
    
    # 创建一个包含语法错误的Verilog文件
    buggy_code = """
module buggy_module(
    input clk,
    input rst,
    output reg [7:0] out
);

// 故意的语法错误
always @(posedge clk or posedge rst begin  // 缺少右括号
    if (rst) begin
        out <= 8'b0
    end else begin  // 缺少分号
        out <= out + 1;
    end
end

endmodule
"""
    
    # 保存到文件管理器
    file_manager = get_file_manager()
    buggy_file_ref = file_manager.save_file(
        content=buggy_code,
        filename="buggy_module.v",
        file_type="verilog",
        created_by="test_error_reporting",
        description="包含语法错误的测试模块"
    )
    
    # 创建测试台
    testbench_code = """
module buggy_module_tb;
    reg clk, rst;
    wire [7:0] out;
    
    buggy_module uut (
        .clk(clk),
        .rst(rst),
        .out(out)
    );
    
    initial begin
        clk = 0;
        rst = 1;
        #10 rst = 0;
        #100 $finish;
    end
    
    always #5 clk = ~clk;
    
endmodule
"""
    
    tb_file_ref = file_manager.save_file(
        content=testbench_code,
        filename="buggy_module_tb.v",
        file_type="testbench",
        created_by="test_error_reporting",
        description="用于测试错误报告的测试台"
    )
    
    # 使用TestAnalyzer测试
    analyzer = TestAnalyzer()
    
    design_files = [{
        "file_id": buggy_file_ref.file_id,
        "file_path": buggy_file_ref.file_path,
        "file_type": buggy_file_ref.file_type
    }]
    
    result = await analyzer.run_with_user_testbench(design_files, tb_file_ref.file_path)
    
    logger.info(f"✅ 错误报告测试完成")
    logger.info(f"📊 成功: {result.get('success', False)}")
    
    if "error_details" in result:
        error_details = result["error_details"]
        logger.info(f"📊 发现 {error_details.get('error_count', 0)} 个错误")
        
        for error in error_details.get("precise_errors", [])[:3]:
            logger.info(f"   📍 {error['file']}:{error['line']} - {error['message']}")
    
    return result


async def main():
    """主测试函数"""
    logger.info("🧪 开始测试增强后的TDD系统")
    
    results = {}
    
    try:
        # 1. 测试文件管理器
        logger.info("=" * 60)
        file_ref = await test_file_manager()
        results["file_manager"] = True
        
        # 2. 测试智能体
        logger.info("=" * 60)
        agent_result, latest_files = await test_enhanced_verilog_agent()
        results["verilog_agent"] = agent_result.get("success", False)
        
        # 3. 测试错误报告
        logger.info("=" * 60)
        error_result = await test_error_reporting()
        results["error_reporting"] = not error_result.get("success", True)  # 错误测试应该失败
        
        # 4. 测试TDD工作流
        logger.info("=" * 60)
        tdd_result = await test_enhanced_tdd_workflow()
        results["tdd_workflow"] = tdd_result.get("success", False)
        
    except Exception as e:
        logger.error(f"❌ 测试过程中出现异常: {e}")
        results["exception"] = str(e)
    
    # 总结测试结果
    logger.info("=" * 60)
    logger.info("📋 测试结果总结:")
    
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        logger.info(f"   {test_name}: {status}")
    
    success_count = sum(1 for success in results.values() if success is True)
    total_count = len([k for k in results.keys() if k != "exception"])
    
    logger.info(f"🎯 总体结果: {success_count}/{total_count} 个测试通过")
    
    if "exception" in results:
        logger.error(f"⚠️ 异常信息: {results['exception']}")
    
    # 显示文件管理器状态
    file_manager = get_file_manager()
    workspace_info = file_manager.get_workspace_info()
    logger.info(f"🗂️ 工作空间状态: 共 {workspace_info['total_files']} 个文件")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())