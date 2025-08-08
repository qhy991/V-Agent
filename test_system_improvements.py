#!/usr/bin/env python3
"""
系统改进验证测试
验证文件路径管理、智能体能力边界、构建脚本生成和错误处理等改进
"""

import sys
import logging
import asyncio
import tempfile
from pathlib import Path

# 设置路径
sys.path.append(str(Path(__file__).parent))

from core.path_manager import get_path_manager, reset_path_manager
from core.agent_capability_manager import get_capability_manager, TaskType, AgentRole
from core.build_script_generator import EnhancedBuildScriptGenerator, create_build_configuration
from core.enhanced_error_handler import get_error_handler, ErrorCategory, ErrorSeverity

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemImprovementTester:
    """系统改进测试器"""
    
    def __init__(self):
        self.logger = logger
        self.test_results = []
        self.temp_dir = None
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始系统改进验证测试")
        logger.info("="*80)
        
        # 创建临时测试环境
        self.temp_dir = Path(tempfile.mkdtemp(prefix="v_agent_test_"))
        logger.info(f"📁 测试环境: {self.temp_dir}")
        
        tests = [
            ("路径管理器功能测试", self.test_path_manager),
            ("智能体能力边界管理测试", self.test_capability_manager),
            ("构建脚本生成器测试", self.test_build_script_generator),
            ("错误处理器测试", self.test_error_handler),
            ("集成功能测试", self.test_integration)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*60}")
            logger.info(f"🧪 执行测试: {test_name}")
            logger.info(f"{'='*60}")
            
            try:
                result = await test_func()
                self.test_results.append((test_name, result, None))
                if result:
                    logger.info(f"✅ 测试通过: {test_name}")
                else:
                    logger.error(f"❌ 测试失败: {test_name}")
            except Exception as e:
                logger.error(f"💥 测试异常: {test_name} - {str(e)}")
                self.test_results.append((test_name, False, str(e)))
        
        # 清理测试环境
        self._cleanup()
        
        # 输出测试摘要
        self.print_test_summary()
    
    async def test_path_manager(self) -> bool:
        """测试路径管理器功能"""
        try:
            # 重置路径管理器以确保干净的测试环境
            reset_path_manager()
            path_manager = get_path_manager(self.temp_dir)
            
            # 创建测试文件
            test_design_file = self.temp_dir / "designs" / "counter.v"
            test_testbench_file = self.temp_dir / "testbenches" / "tb_counter.v"
            
            # 创建目录结构
            test_design_file.parent.mkdir(parents=True, exist_ok=True)
            test_testbench_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建测试文件
            test_design_file.write_text("module counter(); endmodule")
            test_testbench_file.write_text("module tb_counter(); endmodule")
            
            # 测试设计文件解析
            design_result = path_manager.resolve_design_file("counter", "counter.v")
            if not design_result.found:
                logger.error("❌ 设计文件解析失败")
                return False
            
            logger.info(f"✅ 设计文件解析成功: {design_result.path}")
            
            # 测试测试台文件解析
            tb_result = path_manager.resolve_testbench_file("counter")
            if not tb_result.found:
                logger.error("❌ 测试台文件解析失败")
                return False
            
            logger.info(f"✅ 测试台文件解析成功: {tb_result.path}")
            
            # 测试文件存在性验证
            validation = path_manager.validate_file_existence([design_result.path, tb_result.path])
            if not validation["all_exist"]:
                logger.error("❌ 文件存在性验证失败")
                return False
            
            logger.info("✅ 文件存在性验证通过")
            
            # 测试工作空间创建
            workspace = path_manager.create_unified_workspace("test_exp_001")
            if not all(path.exists() for path in workspace.values()):
                logger.error("❌ 工作空间创建失败")
                return False
            
            logger.info("✅ 统一工作空间创建成功")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 路径管理器测试异常: {str(e)}")
            return False
    
    async def test_capability_manager(self) -> bool:
        """测试智能体能力边界管理"""
        try:
            capability_manager = get_capability_manager()
            
            # 测试任务分配 - 设计任务
            design_assignment = capability_manager.assign_task(
                task_description="设计一个8位计数器模块",
                task_type=TaskType.DESIGN,
                complexity="medium",
                required_tools=["write_file", "generate_verilog_code"]
            )
            
            if design_assignment.assigned_agent.agent_role != AgentRole.VERILOG_DESIGNER:
                logger.error("❌ 设计任务分配给了错误的智能体")
                return False
            
            logger.info(f"✅ 设计任务正确分配给: {design_assignment.assigned_agent.agent_id}")
            logger.info(f"   分配推理: {design_assignment.reasoning}")
            
            # 测试任务分配 - 验证任务
            verification_assignment = capability_manager.assign_task(
                task_description="为计数器模块生成测试台并进行仿真验证",
                task_type=TaskType.VERIFICATION,
                complexity="medium",
                required_tools=["generate_testbench", "run_simulation"]
            )
            
            if verification_assignment.assigned_agent.agent_role != AgentRole.CODE_REVIEWER:
                logger.error("❌ 验证任务分配给了错误的智能体")
                return False
            
            logger.info(f"✅ 验证任务正确分配给: {verification_assignment.assigned_agent.agent_id}")
            logger.info(f"   分配推理: {verification_assignment.reasoning}")
            
            # 测试冲突检测
            conflict_assignment = capability_manager.assign_task(
                task_description="设计一个新模块并生成测试台",
                task_type=TaskType.DESIGN,
                complexity="medium"
            )
            
            if not conflict_assignment.warnings:
                logger.warning("⚠️ 应该检测到任务描述中的潜在冲突")
            else:
                logger.info(f"✅ 成功检测到潜在冲突: {conflict_assignment.warnings}")
            
            # 测试任务描述验证
            validation_result = capability_manager.validate_task_description(
                "设计一个计数器模块并生成测试台进行验证"
            )
            
            if not validation_result["warnings"]:
                logger.warning("⚠️ 应该检测到混合任务类型")
            else:
                logger.info(f"✅ 成功检测到混合任务类型: {validation_result['warnings']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 能力管理器测试异常: {str(e)}")
            return False
    
    async def test_build_script_generator(self) -> bool:
        """测试构建脚本生成器"""
        try:
            # 创建测试文件
            design_file = self.temp_dir / "counter.v"
            testbench_file = self.temp_dir / "tb_counter.v"
            
            design_file.write_text("""
module counter #(
    parameter WIDTH = 4
)(
    input clk,
    input rst,
    output reg [WIDTH-1:0] count
);
    always @(posedge clk or posedge rst) begin
        if (rst) count <= 0;
        else count <= count + 1;
    end
endmodule
""")
            
            testbench_file.write_text("""
module tb_counter;
    reg clk, rst;
    wire [3:0] count;
    
    counter dut(.clk(clk), .rst(rst), .count(count));
    
    initial begin
        $dumpfile("counter.vcd");
        $dumpvars(0, tb_counter);
        clk = 0; rst = 1;
        #10 rst = 0;
        #100 $finish;
    end
    
    always #5 clk = ~clk;
endmodule
""")
            
            # 创建构建配置
            build_config = create_build_configuration(
                module_name="counter",
                design_files=[design_file],
                testbench_files=[testbench_file],
                simulator="iverilog",
                working_dir=self.temp_dir
            )
            
            # 创建构建脚本生成器
            generator = EnhancedBuildScriptGenerator(self.temp_dir)
            
            # 验证构建文件
            validation = generator.validate_build_files(build_config)
            if not validation["valid"]:
                logger.error(f"❌ 构建配置验证失败: {validation['errors']}")
                return False
            
            logger.info("✅ 构建配置验证通过")
            
            # 生成构建文件
            created_files = generator.create_build_files(build_config)
            
            if "makefile" not in created_files or not created_files["makefile"].exists():
                logger.error("❌ Makefile生成失败")
                return False
            
            if "bash_script" not in created_files or not created_files["bash_script"].exists():
                logger.error("❌ Bash脚本生成失败")
                return False
            
            logger.info("✅ 构建文件生成成功")
            
            # 验证生成的内容
            makefile_content = created_files["makefile"].read_text()
            if "check_files" not in makefile_content:
                logger.error("❌ Makefile缺少文件检查功能")
                return False
            
            bash_content = created_files["bash_script"].read_text()
            if "log_info" not in bash_content:
                logger.error("❌ Bash脚本缺少增强功能")
                return False
            
            logger.info("✅ 构建脚本内容验证通过")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 构建脚本生成器测试异常: {str(e)}")
            return False
    
    async def test_error_handler(self) -> bool:
        """测试错误处理器"""
        try:
            error_handler = get_error_handler()
            
            # 测试文件不存在错误处理
            try:
                with open("/nonexistent/file.txt", 'r') as f:
                    f.read()
            except FileNotFoundError as e:
                error_info = error_handler.handle_error(
                    e, 
                    context={"operation": "read_file", "file": "/nonexistent/file.txt"},
                    auto_recover=False
                )
                
                if error_info.category.value != "file_not_found":
                    logger.error("❌ 错误类别识别失败")
                    return False
                
                logger.info(f"✅ 错误类别正确识别: {error_info.category.value}")
            
            # 测试文件存在性检查
            test_files = [
                self.temp_dir / "existing.txt",
                self.temp_dir / "nonexistent.txt"
            ]
            
            # 创建一个存在的文件
            test_files[0].write_text("test content")
            
            file_check_result = error_handler.check_file_existence(test_files)
            
            if file_check_result["all_exist"]:
                logger.error("❌ 应该检测到缺失文件")
                return False
            
            if len(file_check_result["missing_files"]) != 1:
                logger.error("❌ 缺失文件数量不正确")
                return False
            
            logger.info("✅ 文件存在性检查正确")
            
            # 测试错误摘要
            summary = error_handler.get_error_summary()
            if summary["total_errors"] < 1:
                logger.error("❌ 错误历史记录失败")
                return False
            
            logger.info(f"✅ 错误摘要生成正确: {summary['total_errors']}个错误")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 错误处理器测试异常: {str(e)}")
            return False
    
    async def test_integration(self) -> bool:
        """测试组件集成功能"""
        try:
            logger.info("🔗 测试组件间集成功能...")
            
            # 重置组件状态
            reset_path_manager()
            
            # 创建集成测试场景
            # 1. 使用能力管理器分配任务
            capability_manager = get_capability_manager()
            task_assignment = capability_manager.assign_task(
                task_description="设计并验证一个简单的计数器",
                task_type=TaskType.DESIGN,
                complexity="simple"
            )
            
            logger.info(f"✅ 任务分配成功: {task_assignment.assigned_agent.agent_id}")
            
            # 2. 使用路径管理器管理文件
            path_manager = get_path_manager(self.temp_dir)
            workspace = path_manager.create_unified_workspace("integration_test")
            
            # 3. 创建测试文件
            design_file = workspace["designs"] / "simple_counter.v"
            testbench_file = workspace["testbenches"] / "tb_simple_counter.v"
            
            design_file.write_text("module simple_counter(); endmodule")
            testbench_file.write_text("module tb_simple_counter(); endmodule")
            
            # 4. 使用构建脚本生成器
            build_config = create_build_configuration(
                module_name="simple_counter",
                design_files=[design_file],
                testbench_files=[testbench_file],
                working_dir=workspace["artifacts"]
            )
            
            generator = EnhancedBuildScriptGenerator(workspace["artifacts"])
            build_files = generator.create_build_files(build_config)
            
            # 5. 验证所有组件协同工作
            if not all(f.exists() for f in build_files.values()):
                logger.error("❌ 构建文件生成失败")
                return False
            
            # 6. 使用错误处理器进行文件验证
            error_handler = get_error_handler()
            all_files = [design_file, testbench_file] + list(build_files.values())
            file_check = error_handler.check_file_existence(all_files)
            
            if not file_check["all_exist"]:
                logger.error(f"❌ 文件完整性检查失败: {file_check}")
                return False
            
            logger.info("✅ 组件集成测试完全成功")
            logger.info(f"   创建的工作空间: {len(workspace)}个目录")
            logger.info(f"   生成的构建文件: {len(build_files)}个")
            logger.info(f"   验证的文件: {len(all_files)}个")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 集成测试异常: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _cleanup(self):
        """清理测试环境"""
        if self.temp_dir and self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info(f"🧹 清理测试环境: {self.temp_dir}")
    
    def print_test_summary(self):
        """打印测试摘要"""
        logger.info(f"\n{'='*80}")
        logger.info("🎯 系统改进验证测试摘要")
        logger.info(f"{'='*80}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, result, _ in self.test_results if result)
        failed_tests = total_tests - passed_tests
        
        logger.info(f"📊 总测试数: {total_tests}")
        logger.info(f"✅ 通过测试: {passed_tests}")
        logger.info(f"❌ 失败测试: {failed_tests}")
        logger.info(f"🎯 成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            logger.info(f"\n❌ 失败的测试:")
            for test_name, result, error in self.test_results:
                if not result:
                    logger.info(f"  - {test_name}")
                    if error:
                        logger.info(f"    错误: {error}")
        
        logger.info(f"\n{'='*80}")
        
        if passed_tests == total_tests:
            logger.info("🎉 所有系统改进验证测试通过！")
            logger.info("\n📋 改进摘要:")
            logger.info("1. ✅ 统一路径管理器 - 解决文件路径不一致问题")
            logger.info("2. ✅ 智能体能力边界管理 - 避免任务分配冲突")  
            logger.info("3. ✅ 增强构建脚本生成 - 提供可靠的Makefile和脚本")
            logger.info("4. ✅ 智能错误处理器 - 提供自动恢复和详细诊断")
            logger.info("5. ✅ 组件集成验证 - 确保各模块协同工作")
        else:
            logger.info("⚠️ 部分测试失败，需要进一步优化。")
        
        logger.info(f"{'='*80}")


async def main():
    """主函数"""
    tester = SystemImprovementTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())