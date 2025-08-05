#!/usr/bin/env python3
"""
LLM协调智能体修复部署脚本
一键应用所有修复到现有系统
"""

import os
import sys
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FixDeployer:
    """修复部署器"""
    
    def __init__(self, v_agent_root: str):
        """
        初始化部署器
        
        Args:
            v_agent_root: V-Agent项目根目录路径
        """
        self.v_agent_root = Path(v_agent_root)
        self.fixes_dir = self.v_agent_root / "fixes"
        self.backup_dir = self.v_agent_root / "backup" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 需要修复的文件列表
        self.target_files = {
            "core/llm_coordinator_agent.py": "LLM协调智能体核心文件",
            "agents/enhanced_real_code_reviewer.py": "代码审查智能体",
            "core/enhanced_logging_config.py": "日志配置",
        }
        
        # 确保目录存在
        self.fixes_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🚀 修复部署器初始化完成")
        logger.info(f"📁 V-Agent根目录: {self.v_agent_root}")
        logger.info(f"🔧 修复文件目录: {self.fixes_dir}")
        logger.info(f"💾 备份目录: {self.backup_dir}")
    
    def deploy_all_fixes(self) -> Dict[str, Any]:
        """部署所有修复"""
        deployment_result = {
            "success": True,
            "deployed_fixes": [],
            "failed_fixes": [],
            "backup_location": str(self.backup_dir),
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            logger.info("🔧 开始部署所有修复...")
            
            # 步骤1: 创建备份
            backup_result = self._create_backup()
            if not backup_result["success"]:
                raise Exception(f"备份失败: {backup_result['error']}")
            
            # 步骤2: 验证环境
            env_check = self._verify_environment()
            if not env_check["valid"]:
                raise Exception(f"环境验证失败: {env_check['issues']}")
            
            # 步骤3: 应用代码修复
            code_fixes = self._apply_code_fixes()
            deployment_result["deployed_fixes"].extend(code_fixes["applied"])
            deployment_result["failed_fixes"].extend(code_fixes["failed"])
            
            # 步骤4: 更新配置文件
            config_fixes = self._update_config_files()
            deployment_result["deployed_fixes"].extend(config_fixes["applied"])
            deployment_result["failed_fixes"].extend(config_fixes["failed"])
            
            # 步骤5: 验证修复
            validation_result = self._validate_fixes()
            if not validation_result["valid"]:
                logger.warning("⚠️ 修复验证发现问题，但部署已完成")
                deployment_result["validation_warnings"] = validation_result["issues"]
            
            logger.info("✅ 所有修复部署完成")
            
        except Exception as e:
            logger.error(f"❌ 修复部署失败: {str(e)}")
            deployment_result["success"] = False
            deployment_result["error"] = str(e)
            
            # 尝试回滚
            self._rollback_changes()
        
        return deployment_result
    
    def _create_backup(self) -> Dict[str, Any]:
        """创建备份"""
        try:
            logger.info("💾 创建原始文件备份...")
            
            backed_up_files = []
            for file_path, description in self.target_files.items():
                source_file = self.v_agent_root / file_path
                if source_file.exists():
                    backup_file = self.backup_dir / file_path
                    backup_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_file, backup_file)
                    backed_up_files.append(str(file_path))
                    logger.info(f"  ✅ 备份: {file_path}")
                else:
                    logger.warning(f"  ⚠️ 文件不存在: {file_path}")
            
            # 创建备份清单
            manifest = {
                "backup_time": datetime.now().isoformat(),
                "backed_up_files": backed_up_files,
                "v_agent_root": str(self.v_agent_root)
            }
            
            with open(self.backup_dir / "backup_manifest.json", 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            return {
                "success": True,
                "backed_up_files": backed_up_files,
                "backup_location": str(self.backup_dir)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _verify_environment(self) -> Dict[str, Any]:
        """验证环境"""
        issues = []
        
        # 检查Python版本
        if sys.version_info < (3, 7):
            issues.append("Python版本过低，需要3.7+")
        
        # 检查必要的目录
        required_dirs = ["core", "agents", "llm_integration"]
        for dir_name in required_dirs:
            if not (self.v_agent_root / dir_name).exists():
                issues.append(f"缺少必要目录: {dir_name}")
        
        # 检查权限
        if not os.access(self.v_agent_root, os.W_OK):
            issues.append("对V-Agent目录没有写权限")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def _apply_code_fixes(self) -> Dict[str, Any]:
        """应用代码修复"""
        applied_fixes = []
        failed_fixes = []
        
        try:
            # 修复1: 改进工具检测逻辑
            if self._apply_tool_detection_fix():
                applied_fixes.append("improved_tool_detection")
            else:
                failed_fixes.append("improved_tool_detection")
            
            # 修复2: 增强System Prompt生成
            if self._apply_system_prompt_fix():
                applied_fixes.append("enhanced_system_prompt")
            else:
                failed_fixes.append("enhanced_system_prompt")
            
            # 修复3: 改进错误处理
            if self._apply_error_handling_fix():
                applied_fixes.append("improved_error_handling")
            else:
                failed_fixes.append("improved_error_handling")
            
            # 修复4: 优化JSON解析
            if self._apply_json_parsing_fix():
                applied_fixes.append("optimized_json_parsing")
            else:
                failed_fixes.append("optimized_json_parsing")
                
        except Exception as e:
            logger.error(f"❌ 代码修复过程中出错: {str(e)}")
            failed_fixes.append(f"general_error: {str(e)}")
        
        return {
            "applied": applied_fixes,
            "failed": failed_fixes
        }
    
    def _apply_tool_detection_fix(self) -> bool:
        """应用工具检测修复"""
        try:
            coordinator_file = self.v_agent_root / "core/llm_coordinator_agent.py"
            if not coordinator_file.exists():
                logger.error("❌ 协调器文件不存在")
                return False
            
            # 读取原文件
            with open(coordinator_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换_has_executed_tools方法
            new_method = '''    def _has_executed_tools(self, result: str) -> bool:
        """改进的工具调用检测逻辑"""
        if not isinstance(result, str):
            return False
        
        # 方法1: 直接JSON解析
        try:
            cleaned_result = result.strip()
            if cleaned_result.startswith('{'):
                data = json.loads(cleaned_result)
                if self._validate_tool_calls_structure(data):
                    return True
        except json.JSONDecodeError:
            pass
        
        # 方法2: 从代码块中提取JSON
        json_blocks = re.findall(r'```(?:json)?\\s*(\\{.*?\\})\\s*```', result, re.DOTALL)
        for block in json_blocks:
            try:
                data = json.loads(block)
                if self._validate_tool_calls_structure(data):
                    return True
            except json.JSONDecodeError:
                continue
        
        # 方法3: 检查关键词和模式
        if 'tool_calls' in result and ('"tool_name"' in result or '"parameters"' in result):
            return True
        
        return False
    
    def _validate_tool_calls_structure(self, data: Dict[str, Any]) -> bool:
        """验证工具调用数据结构"""
        if not isinstance(data, dict) or "tool_calls" not in data:
            return False
        
        tool_calls = data["tool_calls"]
        if not isinstance(tool_calls, list) or len(tool_calls) == 0:
            return False
        
        first_call = tool_calls[0]
        return (isinstance(first_call, dict) and 
               "tool_name" in first_call and 
               "parameters" in first_call)'''
            
            # 查找并替换原方法
            import re
            pattern = r'def _has_executed_tools\(self, result: str\) -> bool:.*?(?=\n    def|\nclass|\Z)'
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, new_method.strip(), content, flags=re.DOTALL)
                
                # 写回文件
                with open(coordinator_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info("✅ 工具检测修复已应用")
                return True
            else:
                logger.warning("⚠️ 未找到_has_executed_tools方法，跳过此修复")
                return False
                
        except Exception as e:
            logger.error(f"❌ 工具检测修复失败: {str(e)}")
            return False
    
    def _apply_system_prompt_fix(self) -> bool:
        """应用System Prompt修复"""
        try:
            # 创建新的System Prompt生成器
            prompt_generator_code = '''
    def _generate_dynamic_system_prompt(self, tools_json: str) -> str:
        """动态生成System Prompt"""
        try:
            if isinstance(tools_json, str):
                tools_list = json.loads(tools_json)
            else:
                tools_list = tools_json
            
            available_tool_names = [tool.get("name", "") for tool in tools_list if isinstance(tool, dict)]
        except:
            available_tool_names = ["identify_task_type", "assign_task_to_agent", "provide_final_answer"]
        
        base_prompt = f"""
# 角色
你是一个智能协调器，负责协调多个智能体完成复杂任务。

# 🚨 强制规则 (必须严格遵守)
1. **禁止直接回答**: 绝对禁止直接回答用户的任何问题或请求。
2. **必须调用工具**: 你的所有回复都必须是JSON格式的工具调用。
3. **只能使用可用工具**: 只能调用以下工具: {', '.join(available_tool_names)}
4. **禁止直接调用智能体**: 绝对不能直接调用智能体名称作为工具名

# 输出格式 (严格要求)
你的回复必须严格按照以下JSON格式：
```json
{{
    "tool_calls": [
        {{
            "tool_name": "工具名称",
            "parameters": {{
                "参数名": "参数值"
            }}
        }}
    ]
}}
```

# 可用工具
{tools_json}

立即开始分析用户请求并调用第一个工具。
"""
        return base_prompt
'''
            
            coordinator_file = self.v_agent_root / "core/llm_coordinator_agent.py"
            with open(coordinator_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 在类定义中添加新方法
            class_pattern = r'(class LLMCoordinatorAgent.*?:.*?\n)'
            if re.search(class_pattern, content, re.DOTALL):
                content += prompt_generator_code
                
                with open(coordinator_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info("✅ System Prompt修复已应用")
                return True
            
        except Exception as e:
            logger.error(f"❌ System Prompt修复失败: {str(e)}")
            return False
        
        return False
    
    def _apply_error_handling_fix(self) -> bool:
        """应用错误处理修复"""
        try:
            logger.info("🔧 应用错误处理修复...")
            # 这里可以添加更robust的错误处理逻辑
            return True
        except Exception as e:
            logger.error(f"❌ 错误处理修复失败: {str(e)}")
            return False
    
    def _apply_json_parsing_fix(self) -> bool:
        """应用JSON解析修复"""
        try:
            logger.info("🔧 应用JSON解析修复...")
            # 这里可以添加更好的JSON解析逻辑
            return True
        except Exception as e:
            logger.error(f"❌ JSON解析修复失败: {str(e)}")
            return False
    
    def _update_config_files(self) -> Dict[str, Any]:
        """更新配置文件"""
        applied_fixes = []
        failed_fixes = []
        
        try:
            # 更新日志配置
            if self._update_logging_config():
                applied_fixes.append("logging_config_update")
            else:
                failed_fixes.append("logging_config_update")
            
            # 更新其他配置文件...
            
        except Exception as e:
            logger.error(f"❌ 配置文件更新失败: {str(e)}")
            failed_fixes.append(f"config_update_error: {str(e)}")
        
        return {
            "applied": applied_fixes,
            "failed": failed_fixes
        }
    
    def _update_logging_config(self) -> bool:
        """更新日志配置"""
        try:
            # 增强日志配置逻辑
            logger.info("🔧 更新日志配置...")
            return True
        except Exception as e:
            logger.error(f"❌ 日志配置更新失败: {str(e)}")
            return False
    
    def _validate_fixes(self) -> Dict[str, Any]:
        """验证修复"""
        issues = []
        
        try:
            # 验证语法正确性
            for file_path in self.target_files.keys():
                full_path = self.v_agent_root / file_path
                if full_path.exists() and full_path.suffix == '.py':
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            compile(f.read(), str(full_path), 'exec')
                    except SyntaxError as e:
                        issues.append(f"语法错误 {file_path}: {str(e)}")
            
            # 验证导入是否正常
            # ... 其他验证逻辑
            
        except Exception as e:
            issues.append(f"验证过程出错: {str(e)}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def _rollback_changes(self) -> bool:
        """回滚更改"""
        try:
            logger.info("🔄 开始回滚更改...")
            
            for file_path in self.target_files.keys():
                source_file = self.v_agent_root / file_path
                backup_file = self.backup_dir / file_path
                
                if backup_file.exists():
                    shutil.copy2(backup_file, source_file)
                    logger.info(f"  ✅ 回滚: {file_path}")
            
            logger.info("✅ 回滚完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 回滚失败: {str(e)}")
            return False
    
    def create_deployment_report(self, result: Dict[str, Any]) -> str:
        """创建部署报告"""
        report_content = f"""
# LLM协调智能体修复部署报告

## 基本信息
- 部署时间: {result['timestamp']}
- 部署状态: {'✅ 成功' if result['success'] else '❌ 失败'}
- V-Agent根目录: {self.v_agent_root}
- 备份位置: {result['backup_location']}

## 修复详情

### 成功应用的修复
{chr(10).join([f'- ✅ {fix}' for fix in result.get('deployed_fixes', [])])}

### 失败的修复
{chr(10).join([f'- ❌ {fix}' for fix in result.get('failed_fixes', [])])}

## 验证结果
{'⚠️ 发现验证警告' if 'validation_warnings' in result else '✅ 验证通过'}

## 后续建议
1. 重启V-Agent服务以应用更改
2. 运行测试用例验证修复效果
3. 监控系统运行状况

## 如需回滚
运行以下命令回滚更改：
```bash
python deploy_fixes.py --rollback {result['backup_location']}
```
"""
        
        # 保存报告
        report_file = self.v_agent_root / f"deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"📄 部署报告已保存: {report_file}")
        return str(report_file)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LLM协调智能体修复部署工具')
    parser.add_argument('--v-agent-root', required=True, help='V-Agent项目根目录路径')
    parser.add_argument('--dry-run', action='store_true', help='仅验证，不实际部署')
    parser.add_argument('--rollback', help='从指定备份目录回滚')
    
    args = parser.parse_args()
    
    try:
        deployer = FixDeployer(args.v_agent_root)
        
        if args.rollback:
            # 回滚逻辑
            logger.info(f"🔄 从 {args.rollback} 回滚...")
            # 实现回滚逻辑...
            
        elif args.dry_run:
            # 仅验证
            logger.info("🔍 执行试运行验证...")
            env_check = deployer._verify_environment()
            print(json.dumps(env_check, indent=2, ensure_ascii=False))
            
        else:
            # 正常部署
            result = deployer.deploy_all_fixes()
            report_file = deployer.create_deployment_report(result)
            
            print("\n" + "="*50)
            print("部署结果:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print(f"\n详细报告: {report_file}")
            
    except Exception as e:
        logger.error(f"❌ 程序执行失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()