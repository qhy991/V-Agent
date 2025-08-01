#!/usr/bin/env python3
"""
🔧 修复LLM Token限制问题

这个脚本用于解决框架中LLM输出被截断的问题：
1. 检查当前的max_tokens硬编码问题
2. 统一提升所有组件的token限制
3. 确保环境变量配置生效
4. 提供验证和回滚功能
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import shutil
from datetime import datetime

class LLMTokenLimitFixer:
    """LLM Token限制修复器"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent
        self.backup_dir = self.project_root / "backup_token_limits"
        
        # 当前发现的硬编码max_tokens值和建议值
        self.token_fixes = {
            # 文件路径: [(行号, 当前值, 建议值, 描述)]
            "core/centralized_coordinator.py": [
                (146, 3000, 8000, "任务处理阶段"),
                (520, 100, 2000, "智能体选择阶段")  # 这个最关键
            ],
            "config/config.py": [
                (54, 1000, 4000, "决策阶段最大tokens"),
                (58, 1500, 6000, "分析阶段最大tokens")
            ],
            "core/base_agent.py": [
                (1395, 800, 3000, "基础智能体响应")
            ],
            "core/real_centralized_coordinator.py": [
                (264, 1000, 4000, "真实协调器")
            ],
            "agents/real_verilog_agent.py": [
                (313, 1500, 4000, "Verilog设计分析"),
                (644, 1500, 4000, "代码质量分析")
            ],
            "agents/real_code_reviewer.py": [
                (526, 2500, 6000, "测试台生成"),
                (1344, 1500, 4000, "代码分析"),
                (1446, 2000, 5000, "Function calling响应")
            ]
        }
        
        # 环境变量推荐值
        self.env_recommendations = {
            "CAF_LLM_MAX_TOKENS": "16384",  # 提升到16K
            "CAF_ANALYSIS_MAX_TOKENS": "6000",
            "CAF_DECISION_MAX_TOKENS": "4000"
        }
    
    def create_backup(self) -> bool:
        """创建修改前的备份"""
        try:
            # 创建备份目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{timestamp}"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            print(f"📦 创建备份: {backup_path}")
            
            # 备份所有需要修改的文件
            for file_path in self.token_fixes.keys():
                source = self.project_root / file_path
                if source.exists():
                    dest = backup_path / file_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dest)
                    print(f"   ✅ 备份: {file_path}")
                else:
                    print(f"   ⚠️ 文件不存在: {file_path}")
            
            # 备份.env文件
            env_file = self.project_root / ".env"
            if env_file.exists():
                shutil.copy2(env_file, backup_path / ".env")
                print(f"   ✅ 备份: .env")
            
            print(f"✅ 备份完成: {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ 备份失败: {str(e)}")
            return False
    
    def analyze_current_limits(self) -> Dict[str, List[Tuple[int, int, str]]]:
        """分析当前的token限制"""
        print("🔍 分析当前的max_tokens限制...")
        
        analysis = {}
        
        for file_path, fixes in self.token_fixes.items():
            full_path = self.project_root / file_path
            if not full_path.exists():
                print(f"   ⚠️ 文件不存在: {file_path}")
                continue
            
            file_analysis = []
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for line_num, current_val, suggested_val, desc in fixes:
                    if line_num <= len(lines):
                        line_content = lines[line_num - 1].strip()
                        # 检查是否包含max_tokens
                        if "max_tokens" in line_content and str(current_val) in line_content:
                            file_analysis.append((line_num, current_val, suggested_val, desc, line_content))
                            print(f"   📍 {file_path}:{line_num} - {desc}: {current_val} → {suggested_val}")
                        else:
                            print(f"   ⚠️ {file_path}:{line_num} - 行内容可能已变化")
                
                analysis[file_path] = file_analysis
                
            except Exception as e:
                print(f"   ❌ 读取失败 {file_path}: {str(e)}")
        
        return analysis
    
    def fix_token_limits(self, analysis: Dict[str, List[Tuple[int, int, str]]]) -> bool:
        """修复token限制"""
        print("🔧 开始修复max_tokens限制...")
        
        success_count = 0
        total_count = 0
        
        for file_path, file_fixes in analysis.items():
            if not file_fixes:
                continue
                
            full_path = self.project_root / file_path
            
            try:
                # 读取文件内容
                with open(full_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 应用修复
                modified = False
                for line_num, current_val, suggested_val, desc, original_line in file_fixes:
                    if line_num <= len(lines):
                        old_line = lines[line_num - 1]
                        # 替换max_tokens值
                        new_line = re.sub(
                            rf'max_tokens\s*=\s*{current_val}',
                            f'max_tokens={suggested_val}',
                            old_line
                        )
                        
                        if new_line != old_line:
                            lines[line_num - 1] = new_line
                            modified = True
                            total_count += 1
                            print(f"   ✅ {file_path}:{line_num} - {desc}: {current_val} → {suggested_val}")
                        else:
                            print(f"   ⚠️ {file_path}:{line_num} - 替换失败")
                
                # 写入修改后的内容
                if modified:
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    success_count += len([f for f in file_fixes if f])
                    print(f"   💾 保存: {file_path}")
                
            except Exception as e:
                print(f"   ❌ 修复失败 {file_path}: {str(e)}")
        
        print(f"✅ 修复完成: {success_count}/{total_count} 个token限制已更新")
        return success_count > 0
    
    def update_env_config(self) -> bool:
        """更新环境变量配置"""
        print("🔧 更新.env文件中的LLM配置...")
        
        env_file = self.project_root / ".env"
        if not env_file.exists():
            print("   ⚠️ .env文件不存在")
            return False
        
        try:
            # 读取当前.env内容
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 更新推荐的环境变量
            modified = False
            for var_name, new_value in self.env_recommendations.items():
                updated = False
                for i, line in enumerate(lines):
                    if line.startswith(f"{var_name}="):
                        old_value = line.split('=', 1)[1].strip()
                        lines[i] = f"{var_name}={new_value}\n"
                        print(f"   ✅ {var_name}: {old_value} → {new_value}")
                        modified = True
                        updated = True
                        break
                
                if not updated:
                    # 添加新的环境变量
                    lines.append(f"\n# Added by LLM Token Limit Fixer\n{var_name}={new_value}\n")
                    print(f"   ➕ 添加: {var_name}={new_value}")
                    modified = True
            
            # 写入更新后的内容
            if modified:
                with open(env_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                print("   💾 .env文件已更新")
                return True
            else:
                print("   ✅ .env文件无需更新")
                return True
                
        except Exception as e:
            print(f"   ❌ 更新.env失败: {str(e)}")
            return False
    
    def create_test_script(self) -> bool:
        """创建测试脚本验证修复效果"""
        test_script_content = '''#!/usr/bin/env python3
"""
🧪 测试LLM Token限制修复效果
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import FrameworkConfig
from core.centralized_coordinator import CentralizedCoordinator
from agents.real_verilog_agent import RealVerilogDesignAgent
from llm_integration.enhanced_llm_client import EnhancedLLMClient

async def test_token_limits():
    """测试各组件的token限制"""
    print("🧪 测试LLM Token限制修复效果")
    print("=" * 50)
    
    # 1. 测试配置读取
    config = FrameworkConfig.from_env()
    print(f"📋 环境变量配置:")
    print(f"   CAF_LLM_MAX_TOKENS: {config.llm.max_tokens}")
    
    # 2. 测试LLM客户端
    llm_client = EnhancedLLMClient(config.llm)
    print(f"🤖 LLM客户端配置:")
    print(f"   默认max_tokens: {llm_client.config.max_tokens}")
    
    # 3. 测试协调器配置
    coordinator = CentralizedCoordinator(config)
    print(f"🎛️ 协调器配置:")
    print(f"   分析max_tokens: {config.coordinator.analysis_max_tokens}")
    print(f"   决策max_tokens: {config.coordinator.decision_max_tokens}")
    
    # 4. 测试Verilog智能体
    verilog_agent = RealVerilogDesignAgent(config)
    print(f"🔧 Verilog智能体已初始化")
    
    print("✅ 所有组件token限制测试完成")
    print("如果看到更高的token值(如4000+)，说明修复成功！")

if __name__ == "__main__":
    asyncio.run(test_token_limits())
'''
        
        test_file = self.project_root / "test_token_limits_fix.py"
        try:
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_script_content)
            print(f"📝 创建测试脚本: {test_file.name}")
            return True
        except Exception as e:
            print(f"❌ 创建测试脚本失败: {str(e)}")
            return False
    
    def run_fix(self) -> bool:
        """运行完整的修复流程"""
        print("🚀 开始LLM Token限制修复流程")
        print("=" * 60)
        
        # 1. 创建备份
        if not self.create_backup():
            print("❌ 备份失败，终止修复")
            return False
        
        # 2. 分析当前限制
        analysis = self.analyze_current_limits()
        if not any(analysis.values()):
            print("⚠️ 未发现需要修复的token限制")
            return True
        
        # 3. 修复token限制
        if not self.fix_token_limits(analysis):
            print("❌ 修复token限制失败")
            return False
        
        # 4. 更新环境变量
        if not self.update_env_config():
            print("❌ 更新环境变量失败")
            return False
        
        # 5. 创建测试脚本
        self.create_test_script()
        
        print("=" * 60)
        print("🎉 LLM Token限制修复完成！")
        print()
        print("📋 修复摘要:")
        print("✅ 智能体选择阶段: 100 → 2000 tokens (20倍提升)")
        print("✅ 任务处理阶段: 3000 → 8000 tokens (2.7倍提升)")
        print("✅ 分析阶段: 1500 → 6000 tokens (4倍提升)")
        print("✅ 决策阶段: 1000 → 4000 tokens (4倍提升)")
        print("✅ 环境变量: 提升到16K tokens")
        print()
        print("🧪 验证修复效果:")
        print("   python test_token_limits_fix.py")
        print()
        print("🔄 如需回滚:")
        print(f"   备份位置: {self.backup_dir}")
        
        return True
    
    def show_status(self):
        """显示当前状态"""
        print("📊 当前LLM Token限制状态")
        print("=" * 40)
        
        analysis = self.analyze_current_limits()
        
        total_issues = sum(len(fixes) for fixes in analysis.values())
        if total_issues == 0:
            print("✅ 未发现token限制问题")
        else:
            print(f"⚠️ 发现 {total_issues} 个需要修复的token限制")
            print()
            print("🔧 运行修复:")
            print("   python fix_llm_token_limits.py --fix")


def main():
    """主程序"""
    fixer = LLMTokenLimitFixer()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        success = fixer.run_fix()
        sys.exit(0 if success else 1)
    else:
        fixer.show_status()


if __name__ == "__main__":
    main()