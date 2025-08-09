#!/usr/bin/env python3
"""
Enhanced Logging Configuration for CentralizedAgentFramework
基于CircuitPilot-Lite的增强日志系统，支持组件分离和会话管理

Provides component-specific logging with file separation and session management
"""

import logging
import logging.config
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime
import json

# 导入对话显示优化器
try:
    from core.conversation_display_optimizer import conversation_optimizer
except ImportError:
    conversation_optimizer = None


class ComponentLoggerManager:
    """管理不同组件的专用日志记录器"""
    
    def __init__(self, base_log_dir: Optional[str] = None, experiment_workspace: Optional[Union[str, Path]] = None):
        """
        初始化组件日志管理器
        
        Args:
            base_log_dir: 基础日志目录，如果为None则使用默认的./logs目录
            experiment_workspace: 🔧 新增：实验工作空间路径，如果提供则将日志和artifacts放在实验目录中
        """
        # 🔧 统一目录结构：优先使用实验工作空间
        if experiment_workspace is not None:
            # 使用实验目录结构
            self.experiment_workspace = Path(experiment_workspace)
            self.session_log_dir = self.experiment_workspace / "logs"
            self.artifacts_dir = self.experiment_workspace / "temp"  # 使用temp目录存储临时artifacts
            
            # 保持兼容性：设置base_log_dir指向实验目录的logs
            self.base_log_dir = self.session_log_dir.parent
            self.session_id = self.experiment_workspace.name.split('_')[-1] if '_' in self.experiment_workspace.name else datetime.now().strftime("%Y%m%d_%H%M%S")
            
        else:
            # 使用传统logs目录结构（向后兼容）
            if base_log_dir is None:
                self.base_log_dir = Path("./logs")
            else:
                self.base_log_dir = Path(base_log_dir)
                
            # 创建会话特定的子目录（以时间命名）
            self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.session_log_dir = self.base_log_dir / f"experiment_{self.session_id}"
            
            # 创建artifacts子目录
            self.artifacts_dir = self.session_log_dir / "artifacts"
            self.experiment_workspace = None
        
        # 确保目录存在
        if hasattr(self, 'base_log_dir'):
            self.base_log_dir.mkdir(parents=True, exist_ok=True)
        self.session_log_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # 组件日志文件映射 - 针对CentralizedAgentFramework
        self.component_files = {
            # 核心框架组件
            'framework': 'framework.log',
            'coordinator': 'centralized_coordinator.log',
            'centralized_coordinator': 'centralized_coordinator.log',
            'base_agent': 'base_agent.log',
            
            # 智能体组件
            'verilog_agent': 'verilog_design_agent.log',
            'code_reviewer': 'code_review_agent.log',
            'real_verilog_agent': 'real_verilog_agent.log',
            'real_code_reviewer': 'real_code_reviewer.log',
            
            # Function Calling系统
            'function_calling': 'function_calling.log',
            
            # LLM集成
            'llm_client': 'llm_client.log',
            'enhanced_llm_client': 'enhanced_llm_client.log',
            
            # 数据库和工具
            'database': 'database.log',
            'tools': 'tools.log',
            'verilog_tools': 'verilog_tools.log',
            
            # 测试系统
            'test_runner': 'test_runner.log',
            'test_framework': 'test_framework.log',
            'validation': 'validation.log',
            
            # 工作流和配置
            'workflow': 'workflow.log',
            'config': 'config.log',
            
            # 调试和性能
            'debug': 'debug.log',
            'performance': 'performance.log',
            'error': 'error.log'
        }
        
        self.loggers = {}
        self._setup_logging_config()
    
    def _setup_logging_config(self):
        """设置日志配置"""
        # 创建formatters
        formatters = {
            'detailed': {
                'format': '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s - %(name)s - %(message)s'
            },
            'console': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%H:%M:%S'
            }
        }
        
        # 创建handlers
        handlers = {}
        
        # 控制台handler - 只显示LLM调用相关的关键信息
        handlers['console'] = {
            'class': 'logging.StreamHandler',
            'level': 'INFO',  # 提高控制台日志级别，减少输出
            'formatter': 'console',
            'stream': 'ext://sys.stdout'
        }
        
        # 为每个组件创建文件handler
        for component, filename in self.component_files.items():
            # 会话特定文件 - 记录所有DEBUG级别日志
            session_file = self.session_log_dir / filename
            # 主日志文件 - 记录INFO及以上，带轮转
            main_file = self.base_log_dir / filename
            
            handlers[f'{component}_session'] = {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': str(session_file),
                'mode': 'w',
                'encoding': 'utf-8'
            }
            
            handlers[f'{component}_main'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'filename': str(main_file),
                'maxBytes': 52428800,  # 50MB
                'backupCount': 5,
                'encoding': 'utf-8'
            }
        
        # 错误汇总handler - 收集所有ERROR级别日志
        handlers['error_summary'] = {
            'class': 'logging.FileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': str(self.session_log_dir / 'all_errors.log'),
            'mode': 'w',
            'encoding': 'utf-8'
        }
        
        # 全局汇总handler - 记录所有INFO及以上的日志
        handlers['global_summary'] = {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': str(self.session_log_dir / 'experiment_summary.log'),
            'mode': 'w',
            'encoding': 'utf-8'
        }
        
        # 创建loggers配置
        loggers = {}
        
        # 根日志器
        loggers[''] = {
            'level': 'DEBUG',
            'handlers': ['console', 'error_summary', 'global_summary']
        }
        
        # 组件特定日志器映射 - 针对CentralizedAgentFramework
        component_logger_mapping = {
            # 核心框架
            'CentralizedAgentFramework': 'framework',
            '__main__': 'framework',
            'config.config': 'config',
            
            # 协调器 - 添加实际使用的logger名称
            'core.centralized_coordinator': 'coordinator',
            'LLMCoordinatorAgent': 'coordinator',
            'Coordinator': 'coordinator',
            'centralized_coordinator': 'coordinator',
            
            # 基础智能体 - 添加Agent.前缀的日志器
            'core.base_agent': 'base_agent',
            'BaseAgent': 'base_agent',
            'Agent.real_verilog_design_agent': 'real_verilog_agent',
            'Agent.real_code_review_agent': 'real_code_reviewer',
            
            # 协调器特殊映射 - Agent.centralized_coordinator 应该映射到coordinator而不是base_agent
            'Agent.centralized_coordinator': 'coordinator',
            'Agent.coordinator': 'coordinator',
            
            # 智能体实现 - 添加所有可能的名称
            'agents.real_verilog_agent': 'real_verilog_agent',
            'agents.real_code_reviewer': 'real_code_reviewer',
            'RealVerilogDesignAgent': 'real_verilog_agent',
            'RealCodeReviewAgent': 'real_code_reviewer',
            'real_verilog_agent': 'real_verilog_agent',
            'real_code_reviewer': 'real_code_reviewer',
            
            # Function Calling
            'core.function_calling': 'function_calling',
            'function_calling': 'function_calling',
            
            # LLM集成 - 添加所有可能的名称
            'llm_integration.enhanced_llm_client': 'enhanced_llm_client',
            'EnhancedLLMClient': 'enhanced_llm_client',
            'llm_integration': 'llm_client',
            'enhanced_llm_client': 'enhanced_llm_client',
            'llm_client': 'llm_client',
            
            # 工具 - 添加script_tools等
            'tools': 'tools',
            'tools.verilog_tools': 'verilog_tools',
            'tools.sample_database': 'database',
            'tools.script_tools': 'tools',
            'script_tools': 'tools',
            'verilog_tools': 'verilog_tools',
            'database': 'database',
            
            # 测试
            'test_complete_framework': 'test_framework',
            'test_quick_validation': 'validation',
            'FrameworkTester': 'test_runner',
            'test_framework': 'test_framework',
            'test_runner': 'test_runner',
            'validation': 'validation',
            
            # 性能和调试
            'performance': 'performance',
            'debug': 'debug',
            'error': 'error'
        }
        
        for logger_name, component in component_logger_mapping.items():
            if component in self.component_files:
                loggers[logger_name] = {
                    'level': 'DEBUG',
                    'handlers': [
                        'console',
                        f'{component}_session',
                        f'{component}_main',
                        'error_summary',
                        'global_summary'
                    ],
                    'propagate': False
                }
        
        # 应用日志配置
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': formatters,
            'handlers': handlers,
            'loggers': loggers
        }
        
        try:
            logging.config.dictConfig(config)
            print(f"✅ 增强日志系统初始化成功")
            print(f"📂 实验目录: {self.session_log_dir}")
            print(f"📁 工件目录: {self.artifacts_dir}")
            print(f"📋 主日志目录: {self.base_log_dir}")
        except Exception as e:
            print(f"❌ 日志配置失败: {e}")
            # 降级到基本配置
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(),
                    logging.FileHandler(self.session_log_dir / 'fallback.log')
                ]
            )
    
    def get_component_logger(self, component_name: str, logger_name: Optional[str] = None) -> logging.Logger:
        """
        获取特定组件的日志器
        
        Args:
            component_name: 组件名称
            logger_name: 日志器名称，如果为None则使用component_name
            
        Returns:
            配置好的日志器
        """
        if logger_name is None:
            logger_name = component_name
            
        # 生成唯一的缓存键
        cache_key = f"{component_name}:{logger_name}"
        
        if cache_key not in self.loggers:
            logger = logging.getLogger(logger_name)
            
            # 确保logger使用正确的组件配置
            if component_name in self.component_files:
                # 清除现有handlers，避免重复
                logger.handlers.clear()
                
                # 添加控制台handler
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.INFO)
                console_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S'
                ))
                logger.addHandler(console_handler)
                
                # 添加会话文件handler
                session_file = self.session_log_dir / self.component_files[component_name]
                session_handler = logging.FileHandler(session_file, mode='a', encoding='utf-8')
                session_handler.setLevel(logging.DEBUG)
                session_handler.setFormatter(logging.Formatter(
                    '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                ))
                logger.addHandler(session_handler)
                
                # 添加主日志文件handler (轮转)
                main_file = self.base_log_dir / self.component_files[component_name]
                main_handler = logging.handlers.RotatingFileHandler(
                    main_file, maxBytes=52428800, backupCount=10, encoding='utf-8'
                )
                main_handler.setLevel(logging.INFO)
                main_handler.setFormatter(logging.Formatter(
                    '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                ))
                logger.addHandler(main_handler)
                
                # 添加错误汇总handler
                error_handler = logging.FileHandler(
                    self.session_log_dir / 'all_errors.log', mode='a', encoding='utf-8'
                )
                error_handler.setLevel(logging.ERROR)
                error_handler.setFormatter(logging.Formatter(
                    '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                ))
                logger.addHandler(error_handler)
                
                # 添加全局汇总handler
                global_handler = logging.FileHandler(
                    self.session_log_dir / 'experiment_summary.log', mode='a', encoding='utf-8'
                )
                global_handler.setLevel(logging.INFO)
                global_handler.setFormatter(logging.Formatter(
                    '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                ))
                logger.addHandler(global_handler)
                
                logger.setLevel(logging.DEBUG)
                logger.propagate = False
            else:
                # 对于未知组件，使用默认配置
                logger.handlers.clear()
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.INFO)
                console_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
                logger.addHandler(console_handler)
                
                # 写入到general日志文件
                file_handler = logging.FileHandler(
                    self.session_log_dir / 'framework.log', mode='a', encoding='utf-8'
                )
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(logging.Formatter(
                    '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                ))
                logger.addHandler(file_handler)
                
                logger.setLevel(logging.DEBUG)
                logger.propagate = False
            
            self.loggers[cache_key] = logger
            
        return self.loggers[cache_key]
    
    def get_artifacts_dir(self) -> Path:
        """获取工件目录路径"""
        return self.artifacts_dir
    
    def get_session_dir(self) -> Path:
        """获取会话目录路径"""
        return self.session_log_dir
    
    def create_session_summary(self):
        """创建会话日志摘要"""
        summary_file = self.session_log_dir / "session_summary.md"
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"# CentralizedAgentFramework 实验日志摘要\n\n")
                f.write(f"**实验ID**: {self.session_id}\n")
                f.write(f"**开始时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**日志目录**: {self.session_log_dir}\n")
                f.write(f"**工件目录**: {self.artifacts_dir}\n\n")
                
                f.write("## 📁 日志文件说明\n\n")
                for component, filename in self.component_files.items():
                    log_file = self.session_log_dir / filename
                    if log_file.exists():
                        size = log_file.stat().st_size
                        f.write(f"- **{filename}** ({component}): {size} bytes\n")
                
                # 列出生成的工件
                artifacts = list(self.artifacts_dir.glob("*"))
                if artifacts:
                    f.write(f"\n## 🛠️ 生成的工件\n\n")
                    for artifact in artifacts:
                        if artifact.is_file():
                            size = artifact.stat().st_size
                            f.write(f"- **{artifact.name}**: {size} bytes\n")
                
                f.write(f"\n## 🔍 快速查看命令\n\n")
                f.write(f"```bash\n")
                f.write(f"# 查看实验摘要\n")
                f.write(f"tail -f {self.session_log_dir}/experiment_summary.log\n\n")
                f.write(f"# 查看所有错误\n")
                f.write(f"cat {self.session_log_dir}/all_errors.log\n\n")
                f.write(f"# 查看特定组件日志\n")
                f.write(f"tail -f {self.session_log_dir}/coordinator.log\n")
                f.write(f"tail -f {self.session_log_dir}/real_verilog_agent.log\n")
                f.write(f"tail -f {self.session_log_dir}/real_code_reviewer.log\n\n")
                f.write(f"# 查看生成的工件\n")
                f.write(f"ls -la {self.artifacts_dir}\n")
                f.write(f"```\n")
                
        except Exception as e:
            print(f"⚠️ 无法创建会话摘要: {e}")
    
    def force_refresh_loggers(self):
        """强制刷新所有logger配置，应用新的映射"""
        print("🔄 强制刷新logger配置...")
        
        # 清理现有的logger缓存
        old_loggers = self.loggers.copy()
        self.loggers.clear()
        
        # 重新配置所有之前创建的logger
        refreshed_count = 0
        for cache_key, old_logger in old_loggers.items():
            try:
                # 解析缓存键
                if ':' in cache_key:
                    component_name, logger_name = cache_key.split(':', 1)
                else:
                    component_name = logger_name = cache_key
                
                # 重新创建logger（这会应用新的映射）
                new_logger = self.get_component_logger(component_name, logger_name)
                refreshed_count += 1
                print(f"  ✅ 刷新logger: {logger_name} -> {component_name}")
                
            except Exception as e:
                print(f"  ❌ 刷新logger失败 {cache_key}: {e}")
        
        print(f"✅ 完成刷新 {refreshed_count} 个logger")

    def get_log_stats(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        stats = {
            'session_id': self.session_id,
            'session_dir': str(self.session_log_dir),
            'artifacts_dir': str(self.artifacts_dir),
            'main_dir': str(self.base_log_dir),
            'components': {},
            'artifacts': {},
            'total_log_size': 0,
            'total_artifact_size': 0
        }
        
        # 统计日志文件
        for component, filename in self.component_files.items():
            session_file = self.session_log_dir / filename
            main_file = self.base_log_dir / filename
            
            component_stats = {
                'session_file': str(session_file) if session_file.exists() else None,
                'main_file': str(main_file) if main_file.exists() else None,
                'session_size': session_file.stat().st_size if session_file.exists() else 0,
                'main_size': main_file.stat().st_size if main_file.exists() else 0
            }
            
            stats['components'][component] = component_stats
            stats['total_log_size'] += component_stats['session_size'] + component_stats['main_size']
        
        # 统计工件文件
        for artifact in self.artifacts_dir.glob("*"):
            if artifact.is_file():
                size = artifact.stat().st_size
                stats['artifacts'][artifact.name] = {
                    'path': str(artifact),
                    'size': size
                }
                stats['total_artifact_size'] += size
        
        return stats


# 全局日志管理器实例
_logger_manager: Optional[ComponentLoggerManager] = None


def setup_enhanced_logging(base_log_dir: Optional[str] = None, experiment_workspace: Optional[Union[str, Path]] = None) -> ComponentLoggerManager:
    """
    设置增强日志系统
    
    Args:
        base_log_dir: 日志基础目录
        experiment_workspace: 🔧 新增：实验工作空间路径
        
    Returns:
        日志管理器实例
    """
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = ComponentLoggerManager(base_log_dir, experiment_workspace)
        
    return _logger_manager


def get_component_logger(component_name: str, logger_name: Optional[str] = None) -> logging.Logger:
    """
    便利函数：获取组件日志器
    
    Args:
        component_name: 组件名称
        logger_name: 日志器名称
        
    Returns:
        配置好的日志器
    """
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = setup_enhanced_logging()
        
    return _logger_manager.get_component_logger(component_name, logger_name)


def get_logger_manager() -> Optional[ComponentLoggerManager]:
    """获取全局日志管理器实例"""
    return _logger_manager


def get_artifacts_dir() -> Path:
    """获取当前会话的工件目录"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = setup_enhanced_logging()
    return _logger_manager.get_artifacts_dir()


def get_session_dir() -> Path:
    """获取当前会话的日志目录"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = setup_enhanced_logging()
    return _logger_manager.get_session_dir()


def force_refresh_all_loggers():
    """强制刷新所有logger配置，立即应用新的映射"""
    global _logger_manager
    if _logger_manager is not None:
        _logger_manager.force_refresh_loggers()
        return True
    else:
        print("⚠️ 日志管理器未初始化，无法刷新")
        return False


def reset_logging_system():
    """完全重置日志系统，强制重新初始化"""
    global _logger_manager
    print("🔄 完全重置日志系统...")
    
    # 清理全局日志管理器
    _logger_manager = None
    
    # 清理Python的logging模块中的handler
    import logging
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()
    
    # 清理所有已知的logger
    for name in list(logging.Logger.manager.loggerDict.keys()):
        if any(keyword in name.lower() for keyword in ['agent', 'coordinator', 'llm', 'enhanced']):
            logger = logging.getLogger(name)
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
                handler.close()
            logger.handlers.clear()
    
    print("✅ 日志系统重置完成")


# 预定义的便利函数
def get_framework_logger() -> logging.Logger:
    """获取框架主日志器"""
    return get_component_logger('framework')


def get_coordinator_logger() -> logging.Logger:
    """获取协调器日志器"""
    return get_component_logger('coordinator')


def get_agent_logger(agent_name: str) -> logging.Logger:
    """获取智能体日志器"""
    agent_map = {
        'RealVerilogDesignAgent': 'real_verilog_agent',
        'RealCodeReviewAgent': 'real_code_reviewer',
        'BaseAgent': 'base_agent'
    }
    
    component = agent_map.get(agent_name, 'base_agent')
    return get_component_logger(component, agent_name)


def get_llm_logger() -> logging.Logger:
    """获取LLM客户端日志器"""
    return get_component_logger('enhanced_llm_client')


def get_test_logger() -> logging.Logger:
    """获取测试日志器"""
    return get_component_logger('test_framework')


def get_function_calling_logger() -> logging.Logger:
    """获取Function Calling日志器"""
    return get_component_logger('function_calling')


if __name__ == "__main__":
    # 测试日志系统
    manager = setup_enhanced_logging()
    
    # 测试不同组件的日志
    framework_logger = get_framework_logger()
    framework_logger.info("框架日志测试")
    
    coordinator_logger = get_coordinator_logger()
    coordinator_logger.info("协调器日志测试")
    
    agent_logger = get_agent_logger('RealVerilogDesignAgent')
    agent_logger.info("智能体日志测试")
    
    llm_logger = get_llm_logger()
    llm_logger.warning("LLM客户端警告测试")
    
    test_logger = get_test_logger()
    test_logger.error("测试错误日志")
    
    # 显示统计信息
    stats = manager.get_log_stats()
    print("\n📊 日志统计:")
    print(f"实验目录: {stats['session_dir']}")
    print(f"工件目录: {stats['artifacts_dir']}")
    print(f"日志总大小: {stats['total_log_size']} bytes")
    print(f"工件总大小: {stats['total_artifact_size']} bytes")
    
    manager.create_session_summary()
    print("✅ 日志系统测试完成")