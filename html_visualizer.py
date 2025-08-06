#!/usr/bin/env python3
"""
HTML可视化器 - 直接生成HTML文件
HTML Visualizer - Generate HTML files directly
"""

import json
import os
import glob
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

class HTMLVisualizer:
    def __init__(self, experiment_path=None, output_dir=None, config_file=None):
        """
        初始化可视化器
        
        Args:
            experiment_path: 实验路径，如果为None则自动发现最新的实验
            output_dir: 输出目录，如果为None则使用当前目录
            config_file: 配置文件路径，如果为None则使用默认配置
        """
        # 加载配置
        self.config = self._load_config(config_file)
        
        self.experiment_path = Path(experiment_path) if experiment_path else self._find_latest_experiment()
        self.output_dir = Path(output_dir) if output_dir else Path(self.config['output']['default_output_dir'])
        
        # 验证实验路径
        if not self.experiment_path or not self.experiment_path.exists():
            raise ValueError(f"实验路径不存在: {self.experiment_path}")
        
        if self.config['logging']['show_progress']:
            print(f"📁 使用实验路径: {self.experiment_path}")
    
    def _load_config(self, config_file=None):
        """加载配置文件"""
        default_config = {
            "file_patterns": {
                "experiment_reports": ["*.json", "reports/*.json", "**/experiment_report.json"],
                "experiment_summaries": ["*.txt", "reports/*.txt", "**/experiment_summary.txt"],
                "design_files": ["*.v", "designs/*.v", "**/*.v"],
                "testbench_files": ["*testbench*.v", "*tb*.v", "testbenches/*.v"],
                "log_files": ["*.txt", "*.log", "logs/*.txt", "logs/*.log"]
            },
            "experiment_discovery": {
                "patterns": ["llm_experiments/*", "experiments/*", "*/llm_coordinator_*"],
                "sort_by": "mtime"
            },
            "chart_settings": {
                "colors": {
                    "user": "#4CAF50", "assistant": "#2196F3", "system": "#FF9800",
                    "llm_call": "#9C27B0", "tool_execution": "#4CAF50", "tool_failure": "#F44336"
                },
                "chart_height": 500, "timeline_height": 400
            },
            "html_template": {
                "title": "V-Agent 实验可视化报告",
                "subtitle": "基于统一日志系统的实验结果可视化展示"
            },
            "output": {
                "default_output_dir": ".", "filename_template": "experiment_visualization_{experiment_name}.html"
            },
            "logging": {"level": "INFO", "show_progress": True, "show_file_loading": True}
        }
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                # 深度合并配置
                return self._deep_merge(default_config, user_config)
            except Exception as e:
                print(f"⚠️ 加载配置文件失败: {e}，使用默认配置")
        
        return default_config
    
    def _deep_merge(self, default, user):
        """深度合并配置"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
        
    def _find_latest_experiment(self):
        """自动发现最新的实验目录"""
        experiments_dir = Path("llm_experiments")
        if not experiments_dir.exists():
            experiments_dir = Path.cwd()
        
        patterns = self.config['experiment_discovery']['patterns']
        all_experiments = []
        for pattern in patterns:
            all_experiments.extend(glob.glob(pattern))
        
        if not all_experiments:
            raise ValueError("未找到任何实验目录")
        
        # 按修改时间排序，选择最新的
        latest_experiment = max(all_experiments, key=lambda x: Path(x).stat().st_mtime)
        return Path(latest_experiment)
    
    def _find_files_by_pattern(self, directory, patterns, file_type="文件"):
        """根据模式查找文件"""
        if not directory.exists():
            print(f"⚠️ {file_type}目录不存在: {directory}")
            return []
        
        files = []
        for pattern in patterns:
            files.extend(directory.glob(pattern))
        
        return sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def _load_file_content(self, file_path, default_content="文件不存在"):
        """安全加载文件内容"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return default_content
        except Exception as e:
            print(f"⚠️ 读取文件失败 {file_path}: {e}")
            return f"读取失败: {e}"
    
    def load_experiment_data(self):
        """加载实验数据"""
        try:
            print(f"🔄 正在加载实验数据...")
            
            # 1. 查找并加载实验报告
            report_patterns = self.config['file_patterns']['experiment_reports']
            report_files = self._find_files_by_pattern(self.experiment_path, report_patterns, "报告")
            
            if report_files:
                self.experiment_report = json.loads(self._load_file_content(report_files[0]))
                print(f"✅ 加载实验报告: {report_files[0].name}")
            else:
                print("⚠️ 未找到实验报告文件")
                self.experiment_report = {"experiment_id": self.experiment_path.name}
            
            # 2. 查找并加载实验摘要
            summary_patterns = self.config['file_patterns']['experiment_summaries']
            summary_files = self._find_files_by_pattern(self.experiment_path, summary_patterns, "摘要")
            
            if summary_files:
                self.experiment_summary = self._load_file_content(summary_files[0])
                print(f"✅ 加载实验摘要: {summary_files[0].name}")
            else:
                self.experiment_summary = "实验摘要文件不存在"
            
            # 3. 查找并加载设计文件
            design_patterns = self.config['file_patterns']['design_files']
            design_files = self._find_files_by_pattern(self.experiment_path, design_patterns, "设计")
            
            if design_files:
                self.design_code = self._load_file_content(design_files[0])
                print(f"✅ 加载设计文件: {design_files[0].name}")
            else:
                self.design_code = "// 设计文件不存在"
            
            # 4. 查找并加载测试台文件
            testbench_patterns = self.config['file_patterns']['testbench_files']
            testbench_files = self._find_files_by_pattern(self.experiment_path, testbench_patterns, "测试台")
            
            if testbench_files:
                self.testbench_code = self._load_file_content(testbench_files[0])
                print(f"✅ 加载测试台文件: {testbench_files[0].name}")
            else:
                self.testbench_code = "// 测试台文件不存在"
            
            # 5. 查找并加载日志文件
            log_patterns = self.config['file_patterns']['log_files']
            log_files = self._find_files_by_pattern(self.experiment_path, log_patterns, "日志")
            
            # 也在当前目录查找日志文件
            current_log_patterns = ["counter_test_*.txt", "*.log", "test_*.txt"]
            current_log_files = self._find_files_by_pattern(Path.cwd(), current_log_patterns, "当前目录日志")
            log_files.extend(current_log_files)
            
            if log_files:
                self.log_data = self._load_file_content(log_files[0])
                print(f"✅ 加载日志文件: {log_files[0].name}")
            else:
                self.log_data = "日志文件不存在"
            
            # 6. 收集文件结构信息
            self.file_structure = self._generate_file_structure()
            
            print(f"✅ 实验数据加载完成")
            return True
            
        except Exception as e:
            print(f"❌ 加载实验数据失败: {e}")
            return False
    
    def _generate_file_structure(self):
        """生成文件结构信息"""
        structure = []
        
        def scan_directory(path, level=0):
            try:
                for item in sorted(path.iterdir()):
                    if item.name.startswith('.'):
                        continue
                    
                    if item.is_file():
                        size = item.stat().st_size
                        size_str = f"({self._format_size(size)})"
                        structure.append({
                            'type': 'file',
                            'name': item.name,
                            'path': str(item.relative_to(self.experiment_path)),
                            'size': size_str,
                            'level': level
                        })
                    elif item.is_dir():
                        structure.append({
                            'type': 'dir',
                            'name': item.name,
                            'path': str(item.relative_to(self.experiment_path)),
                            'level': level
                        })
                        scan_directory(item, level + 1)
            except PermissionError:
                pass
        
        scan_directory(self.experiment_path)
        return structure
    
    def _format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"
    
    def _get_agent_generated_files(self, agent_id):
        """获取智能体生成的文件内容"""
        try:
            # 根据智能体ID确定可能生成的文件
            file_patterns = []
            if "verilog" in agent_id.lower():
                file_patterns = ["*.v", "designs/*.v", "**/*.v"]
            elif "review" in agent_id.lower() or "test" in agent_id.lower():
                file_patterns = ["*testbench*.v", "*tb*.v", "testbenches/*.v", "**/*testbench*.v"]
            
            if not file_patterns:
                return None
            
            # 在实验目录中查找文件
            found_files = []
            for pattern in file_patterns:
                found_files.extend(self.experiment_path.glob(pattern))
            
            if not found_files:
                return None
            
            # 读取文件内容
            file_contents = []
            for file_path in sorted(found_files):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if content.strip():  # 确保文件不为空
                            file_contents.append(f"📄 {file_path.name}:\n```verilog\n{content}\n```")
                except Exception as e:
                    file_contents.append(f"📄 {file_path.name}: 读取失败 - {e}")
            
            if file_contents:
                return "\n\n".join(file_contents)
            else:
                return None
                
        except Exception as e:
            print(f"⚠️ 获取智能体生成文件失败: {e}")
            return None
    
    def _generate_file_structure_html(self, structure, level=0):
        """生成文件结构的HTML"""
        html = ""
        for item in structure:
            if item['level'] == level:
                indent = "  " * level
                if item['type'] == 'dir':
                    html += f"{indent}📂 {item['name']}<br>"
                    # 递归处理子目录
                    children = [s for s in structure if s['level'] == level + 1 and 
                               s['path'].startswith(item['path'])]
                    if children:
                        html += f"{indent}<div style='margin-left: 20px;'>"
                        html += self._generate_file_structure_html(children, level + 1)
                        html += "</div>"
                else:
                    html += f"{indent}📄 {item['name']} {item['size']}<br>"
        return html

    def parse_conversation_data(self):
        """解析对话数据"""
        conversation_data = []
        
        # 从实验报告中提取对话历史
        detailed_result = self.experiment_report.get('detailed_result', {})
        conversation_history = detailed_result.get('conversation_history', [])
        
        for msg in conversation_history:
            timestamp = msg.get('timestamp', 0)
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            agent_id = msg.get('agent_id', 'unknown')
            
            # 转换时间戳为可读格式
            if timestamp:
                try:
                    dt = datetime.fromtimestamp(timestamp)
                    time_str = dt.strftime('%H:%M:%S')
                except:
                    time_str = f"{timestamp:.1f}"
            else:
                time_str = "N/A"
            
            # 不再截断内容，提供完整内容
            conversation_data.append({
                'time': time_str,
                'role': role,
                'agent_id': agent_id,
                'content': content,  # 完整内容
                'preview': content[:200] + '...' if len(content) > 200 else content,  # 预览
                'full_content': content
            })
        
        return conversation_data
    
    def parse_log_conversations(self):
        """从日志中解析对话内容"""
        log_conversations = []
        
        if not hasattr(self, 'log_data') or self.log_data == "日志文件不存在":
            return log_conversations
        
        lines = self.log_data.split('\n')
        
        # 改进的日志解析，提取更多信息
        for i, line in enumerate(lines):
            if 'LLM响应长度:' in line:
                # 提取LLM响应信息
                parts = line.split(' - ')
                if len(parts) >= 3:
                    time_str = parts[0]
                    agent_part = parts[1]
                    response_length = line.split('LLM响应长度: ')[-1].strip()
                    
                    # 查找对应的LLM调用信息和响应内容
                    llm_call_time = time_str
                    response_content = ""
                    
                    # 向前查找LLM调用信息
                    for j in range(max(0, i-10), i):
                        if j < len(lines) and '发起LLM调用' in lines[j] and agent_part in lines[j]:
                            llm_call_time = lines[j].split(' - ')[0] if ' - ' in lines[j] else time_str
                            break
                    
                    # 尝试从实验报告中获取响应内容
                    if hasattr(self, 'experiment_report'):
                        detailed_result = self.experiment_report.get('detailed_result', {})
                        conversation_history = detailed_result.get('conversation_history', [])
                        
                        # 查找对应时间的对话记录
                        for conv in conversation_history:
                            # 修复智能体匹配逻辑
                            conv_agent_id = conv.get('agent_id', '')
                            # 移除Agent.前缀进行比较
                            conv_agent_clean = conv_agent_id.replace('Agent.', '')
                            agent_part_clean = agent_part.replace('Agent.', '')
                            
                            # 直接匹配智能体ID
                            if conv_agent_clean == agent_part_clean:
                                response_content = conv.get('content', '')
                                break
                            # 或者检查是否包含在agent_part中
                            elif conv_agent_clean in agent_part_clean:
                                response_content = conv.get('content', '')
                                break
                    
                    # 如果实验报告中没有，尝试从LLM对话记录中获取响应内容
                    if not response_content and hasattr(self, 'experiment_report'):
                        llm_conversations = self.experiment_report.get('llm_conversations', [])
                        for llm_conv in llm_conversations:
                            llm_agent_id = llm_conv.get('agent_id', '')
                            # 检查是否是目标智能体
                            if agent_part.replace('Agent.', '') in llm_agent_id:
                                response_content = llm_conv.get('assistant_response', '')
                                if response_content:
                                    break
                    
                    # 🔧 新增：优先从LLM对话记录的user_message中提取真实的智能体响应内容
                    if not response_content and hasattr(self, 'experiment_report'):
                        llm_conversations = self.experiment_report.get('llm_conversations', [])
                        for llm_conv in llm_conversations:
                            user_msg = llm_conv.get('user_message', '')
                            
                            # 方法1: 在协调器的LLM对话中查找智能体执行结果
                            if ('assign_task_to_agent' in user_msg and 
                                agent_part.replace('Agent.', '') in user_msg and
                                'response:' in user_msg):
                                
                                # 从user_message中提取真实的agent响应内容
                                try:
                                    # 查找 "response: '" 之后的内容
                                    start_idx = user_msg.find("response: '") + len("response: '")
                                    if start_idx > len("response: '") - 1:
                                        # 查找结束位置
                                        end_markers = ["'[截断]", "'...", "', '"]
                                        end_idx = len(user_msg)
                                        for marker in end_markers:
                                            marker_pos = user_msg.find(marker, start_idx)
                                            if marker_pos > start_idx:
                                                end_idx = marker_pos
                                                break
                                        
                                        # 提取响应内容
                                        extracted_response = user_msg[start_idx:end_idx].strip()
                                        
                                        # 处理转义字符
                                        extracted_response = extracted_response.replace('\\n', '\n').replace('\\t', '\t')
                                        
                                        if extracted_response and len(extracted_response) > 50:
                                            response_content = extracted_response
                                            break
                                        elif extracted_response and len(extracted_response) > 10:
                                            # 短响应也记录，但标注为短响应，并尝试提供更多上下文
                                            additional_info = ""
                                            # 检查是否有生成的文件可以提供更多信息
                                            file_content = self._get_agent_generated_files(agent_part.replace('Agent.', ''))
                                            if file_content:
                                                additional_info = f"\n\n📝 **实际生成的文件内容**:\n{file_content}"
                                            else:
                                                # 提供任务上下文信息
                                                if hasattr(self, 'experiment_report'):
                                                    detailed_result = self.experiment_report.get('detailed_result', {})
                                                    task_context = detailed_result.get('task_context', {})
                                                    agent_interactions = task_context.get('agent_interactions', [])
                                                    for interaction in agent_interactions:
                                                        if interaction.get('target_agent_id') == agent_part.replace('Agent.', ''):
                                                            task_desc = interaction.get('task_description', '')
                                                            exec_time = interaction.get('execution_time', 0)
                                                            additional_info = f"\n\n📋 **任务上下文**:\n任务描述: {task_desc}\n执行时间: {exec_time:.2f} 秒\n任务状态: 成功"
                                                            break
                                            
                                            response_content = f"⚠️ **智能体短响应**（{len(extracted_response)} 字符）:\n\n{extracted_response}{additional_info}"
                                            break
                                except Exception as e:
                                    print(f"解析智能体响应时出错: {e}")
                                    continue
                            
                            # 方法2: 查找包含完整响应的user_message（针对被截断的情况）
                            if (not response_content and 
                                agent_part.replace('Agent.', '') in user_msg and
                                ('✅ 任务完成报告' in user_msg or '### 📌 任务概述' in user_msg or '🧪 仿真结果' in user_msg)):
                                
                                try:
                                    # 查找完整响应的开始和结束
                                    response_markers = ["response: '## ✅", "response: '### 📌", "response: '🧪"]
                                    for marker in response_markers:
                                        if marker in user_msg:
                                            start_idx = user_msg.find(marker) + len("response: '")
                                            # 查找响应结束位置
                                            end_markers = ["'[截断]", "'...", "', '", "'\\n**执行结果**"]
                                            end_idx = len(user_msg)
                                            for end_marker in end_markers:
                                                marker_pos = user_msg.find(end_marker, start_idx)
                                                if marker_pos > start_idx:
                                                    end_idx = marker_pos
                                                    break
                                            
                                            extracted_response = user_msg[start_idx:end_idx].strip()
                                            extracted_response = extracted_response.replace('\\n', '\n').replace('\\t', '\t')
                                            
                                            if extracted_response and len(extracted_response) > 100:
                                                # 添加被截断的提示
                                                if "'[截断]" in user_msg[end_idx:end_idx+10]:
                                                    extracted_response += "\n\n📝 **注意**: 此响应在实验报告中被截断，完整内容可查看实验目录下的相关文件。"
                                                
                                                response_content = extracted_response
                                                break
                                except Exception as e:
                                    print(f"解析完整响应时出错: {e}")
                                    continue
                    
                    # 如果没有找到内容，尝试从智能体交互记录中获取信息
                    if not response_content and hasattr(self, 'experiment_report'):
                        detailed_result = self.experiment_report.get('detailed_result', {})
                        task_context = detailed_result.get('task_context', {})
                        agent_interactions = task_context.get('agent_interactions', [])
                        for interaction in agent_interactions:
                            target_agent = interaction.get('target_agent_id', '')
                            if agent_part.replace('Agent.', '') == target_agent:
                                response_length = interaction.get('response_length', 0)
                                execution_time = interaction.get('execution_time', 0)
                                success = interaction.get('success', False)
                                task_description = interaction.get('task_description', '')
                                
                                # 🆕 新增：如果响应内容很短，尝试从生成的文件中读取实际内容
                                if response_length < 100:  # 响应内容很短
                                    # 尝试读取生成的文件内容
                                    file_content = self._get_agent_generated_files(target_agent)
                                    if file_content:
                                        response_content = f"""LLM响应内容（长度: {response_length} 字符）

任务描述: {task_description}
执行时间: {execution_time:.2f} 秒
执行状态: {'成功' if success else '失败'}

📝 **实际生成的文件内容**:
{file_content}

💡 **说明**: 子智能体的LLM响应内容较短，但已成功生成相关文件。"""
                                    else:
                                        # 创建更详细的占位符内容
                                        response_content = f"""LLM响应内容（长度: {response_length} 字符）

任务描述: {task_description}
执行时间: {execution_time:.2f} 秒
执行状态: {'成功' if success else '失败'}

由于系统架构设计，子智能体的详细响应内容未在此处显示。
子智能体的响应已被协调智能体处理并转换为任务执行结果。

请查看以下位置获取更多信息：
1. 实验报告中的智能体交互记录
2. 生成的设计文件和测试台文件
3. 工作流执行时间线"""
                                else:
                                    # 响应内容较长，使用原来的占位符
                                    response_content = f"""LLM响应内容（长度: {response_length} 字符）

任务描述: {task_description}
执行时间: {execution_time:.2f} 秒
执行状态: {'成功' if success else '失败'}

由于系统架构设计，子智能体的详细响应内容未在此处显示。
子智能体的响应已被协调智能体处理并转换为任务执行结果。

请查看以下位置获取更多信息：
1. 实验报告中的智能体交互记录
2. 生成的设计文件和测试台文件
3. 工作流执行时间线"""
                                break
                    
                    # 如果仍然没有找到内容，使用默认占位符
                    if not response_content:
                        response_content = f"LLM响应内容（长度: {response_length} 字符）\n\n由于日志格式限制，完整的LLM响应内容未在此处显示。\n请查看实验报告中的详细对话历史以获取完整内容。"
                    
                    log_conversations.append({
                        'time': llm_call_time,
                        'agent': agent_part.replace('Agent.', ''),
                        'type': 'LLM调用',
                        'details': f'响应长度: {response_length} 字符',
                        'content': response_content,  # 添加响应内容
                        'preview': response_content[:100] + '...' if len(response_content) > 100 else response_content,
                        'duration': '约4-6秒'
                    })
            
            elif '工具执行成功:' in line:
                # 提取工具执行信息
                parts = line.split(' - ')
                if len(parts) >= 3:
                    time_str = parts[0]
                    agent_part = parts[1]
                    tool_name = line.split('工具执行成功: ')[-1].strip()
                    
                    # 查找工具执行的详细信息
                    tool_details = ""
                    for j in range(i+1, min(len(lines), i+10)):
                        if j < len(lines) and lines[j].strip() and not lines[j].startswith(' - ') and 'Agent.' not in lines[j]:
                            tool_details += lines[j] + '\n'
                        elif j < len(lines) and lines[j].startswith(' - ') and 'Agent.' in lines[j]:
                            break
                    
                    # 如果没有找到详细信息，使用占位符
                    if not tool_details.strip():
                        tool_details = f"工具 {tool_name} 执行成功\n\n执行时间: {time_str}\n智能体: {agent_part.replace('Agent.', '')}"
                    
                    log_conversations.append({
                        'time': time_str,
                        'agent': agent_part.replace('Agent.', ''),
                        'type': '工具执行',
                        'details': f'成功执行: {tool_name}',
                        'content': tool_details.strip(),
                        'preview': tool_details[:100] + '...' if len(tool_details) > 100 else tool_details,
                        'duration': 'N/A'
                    })
            
            elif '工具执行失败:' in line:
                # 提取工具失败信息
                parts = line.split(' - ')
                if len(parts) >= 3:
                    time_str = parts[0]
                    agent_part = parts[1]
                    tool_name = line.split('工具执行失败: ')[-1].strip()
                    
                    # 查找错误详细信息
                    error_details = ""
                    for j in range(i+1, min(len(lines), i+10)):
                        if j < len(lines) and lines[j].strip() and not lines[j].startswith(' - ') and 'Agent.' not in lines[j]:
                            error_details += lines[j] + '\n'
                        elif j < len(lines) and lines[j].startswith(' - ') and 'Agent.' in lines[j]:
                            break
                    
                    # 如果没有找到错误详情，使用占位符
                    if not error_details.strip():
                        error_details = f"工具 {tool_name} 执行失败\n\n执行时间: {time_str}\n智能体: {agent_part.replace('Agent.', '')}\n\n请查看日志文件获取详细错误信息。"
                    
                    log_conversations.append({
                        'time': time_str,
                        'agent': agent_part.replace('Agent.', ''),
                        'type': '工具失败',
                        'details': f'失败: {tool_name}',
                        'content': error_details.strip(),
                        'preview': error_details[:100] + '...' if len(error_details) > 100 else error_details,
                        'duration': 'N/A'
                    })
        
        return log_conversations
    
    def create_conversation_timeline_chart(self):
        """创建对话时间线图表"""
        conversation_data = self.parse_conversation_data()
        log_conversations = self.parse_log_conversations()
        
        if not conversation_data and not log_conversations:
            return None
        
        fig = go.Figure()
        
        # 添加对话历史数据
        for i, conv in enumerate(conversation_data):
            # 设置颜色
            colors = self.config['chart_settings']['colors']
            color = colors.get(conv['role'], '#9E9E9E')
            
            fig.add_trace(go.Scatter(
                x=[conv['time']],
                y=[i],
                mode='markers+text',
                marker=dict(size=12, color=color),
                text=[f"{conv['role']}<br>{conv['agent_id']}"],
                textposition="middle right",
                name=conv['role'],
                hovertemplate=f"<b>{conv['role']}</b><br>" +
                            f"智能体: {conv['agent_id']}<br>" +
                            f"时间: {conv['time']}<br>" +
                            f"内容: {conv['content'][:100]}...<br>" +
                            f"<extra></extra>"
            ))
        
        # 添加日志对话数据
        for i, log_conv in enumerate(log_conversations):
            offset = len(conversation_data) + i
            
            # 设置颜色
            colors = self.config['chart_settings']['colors']
            color = colors.get(log_conv['type'], '#9E9E9E')
            
            fig.add_trace(go.Scatter(
                x=[log_conv['time']],
                y=[offset],
                mode='markers+text',
                marker=dict(size=10, color=color, symbol='diamond'),
                text=[f"{log_conv['type']}<br>{log_conv['agent']}"],
                textposition="middle right",
                name=log_conv['type'],
                hovertemplate=f"<b>{log_conv['type']}</b><br>" +
                            f"智能体: {log_conv['agent']}<br>" +
                            f"时间: {log_conv['time']}<br>" +
                            f"详情: {log_conv['details']}<br>" +
                            f"<extra></extra>"
            ))
        
        fig.update_layout(
            title="💬 对话时间线",
            xaxis_title="时间",
            yaxis_title="对话事件",
            height=self.config['chart_settings']['chart_height'],
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def create_workflow_timeline_chart(self):
        """创建工作流时间线图表"""
        timeline_data = self.experiment_report.get('execution_timeline', [])
        
        if not timeline_data:
            return None
        
        fig = go.Figure()
        
        for i, event in enumerate(timeline_data):
            timestamp = event.get('timestamp', 0)
            event_type = event.get('event_type', 'unknown')
            agent_id = event.get('agent_id', 'unknown')
            description = event.get('description', '')
            
            # 转换时间戳为相对时间（秒）
            relative_time = timestamp - timeline_data[0]['timestamp'] if timeline_data else 0
            
            # 设置颜色
            colors = self.config['chart_settings']['colors']
            color = colors.get(event_type, '#9E9E9E')
            
            fig.add_trace(go.Scatter(
                x=[relative_time],
                y=[i],
                mode='markers+text',
                marker=dict(size=15, color=color),
                text=[f"{agent_id}<br>{description}"],
                textposition="middle right",
                name=event_type,
                hovertemplate=f"<b>{event_type}</b><br>" +
                            f"智能体: {agent_id}<br>" +
                            f"描述: {description}<br>" +
                            f"时间: {relative_time:.1f}s<br>" +
                            f"<extra></extra>"
            ))
        
        fig.update_layout(
            title="🔄 工作流执行时间线",
            xaxis_title="时间 (秒)",
            yaxis_title="事件",
            height=self.config['chart_settings']['timeline_height'],
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def create_agent_performance_chart(self):
        """创建智能体性能图表"""
        agent_interactions = self.experiment_report.get('agent_interactions', [])
        
        if not agent_interactions:
            return None
        
        # 提取数据
        agents = []
        execution_times = []
        response_lengths = []
        
        for interaction in agent_interactions:
            agent_id = interaction.get('target_agent_id', 'unknown')
            execution_time = interaction.get('execution_time', 0)
            response_length = interaction.get('response_length', 0)
            
            agents.append(agent_id)
            execution_times.append(execution_time)
            response_lengths.append(response_length)
        
        # 创建性能对比图
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(
                x=agents,
                y=execution_times,
                name='执行时间 (秒)',
                marker_color='#2196F3'
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=agents,
                y=response_lengths,
                name='响应长度 (字符)',
                marker_color='#FF9800'
            ),
            secondary_y=True
        )
        
        fig.update_layout(
            title="🤖 智能体性能对比",
            xaxis_title="智能体",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        fig.update_yaxes(title_text="执行时间 (秒)", secondary_y=False)
        fig.update_yaxes(title_text="响应长度 (字符)", secondary_y=True)
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def create_performance_summary_chart(self):
        """创建性能摘要图表"""
        workflow_stages = self.experiment_report.get('workflow_stages', [])
        
        if not workflow_stages:
            return None
        
        # 提取数据
        stage_names = []
        durations = []
        success_status = []
        
        for stage in workflow_stages:
            stage_name = stage.get('stage_name', 'unknown')
            duration = stage.get('duration', 0)
            success = stage.get('success', False)
            
            stage_names.append(stage_name)
            durations.append(duration)
            success_status.append('成功' if success else '失败')
        
        # 创建饼图
        fig = go.Figure(data=[go.Pie(
            labels=stage_names,
            values=durations,
            hole=0.3,
            textinfo='label+percent',
            textposition='inside'
        )])
        
        fig.update_layout(
            title="📊 工作流阶段时间分布",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def create_error_analysis_chart(self):
        """创建错误分析图表"""
        # 从日志中提取错误信息
        log_file = "counter_test_utf8_fixed_20250806_145707.txt"
        error_types = {
            '编译失败': 0,
            '工具执行失败': 0,
            '语法错误': 0,
            '其他错误': 0
        }
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                if '编译失败' in line:
                    error_types['编译失败'] += 1
                elif '工具执行失败' in line:
                    error_types['工具执行失败'] += 1
                elif 'syntax error' in line.lower():
                    error_types['语法错误'] += 1
                elif 'ERROR' in line:
                    error_types['其他错误'] += 1
        
        # 创建错误统计图
        fig = go.Figure(data=[go.Bar(
            x=list(error_types.keys()),
            y=list(error_types.values()),
            marker_color=['#F44336', '#FF9800', '#FFC107', '#9E9E9E']
        )])
        
        fig.update_layout(
            title="⚠️ 错误类型统计",
            xaxis_title="错误类型",
            yaxis_title="错误次数",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def generate_html_report(self):
        """生成完整的HTML报告"""
        if not self.load_experiment_data():
            return False
        
        # 生成图表
        conversation_chart = self.create_conversation_timeline_chart()
        timeline_chart = self.create_workflow_timeline_chart()
        performance_chart = self.create_agent_performance_chart()
        summary_chart = self.create_performance_summary_chart()
        error_chart = self.create_error_analysis_chart()
        
        # 解析对话数据
        conversation_data = self.parse_conversation_data()
        log_conversations = self.parse_log_conversations()
        
        # 创建对话内容HTML
        conversation_html = ""
        if conversation_data:
            conversation_html += "<h3>📝 对话历史</h3>"
            for i, conv in enumerate(conversation_data):
                role_icon = "👤" if conv['role'] == 'user' else "🤖" if conv['role'] == 'assistant' else "⚙️"
                has_full_content = len(conv['content']) > 200
                conversation_html += f"""
                <div class="conversation-item">
                    <div class="conversation-header">
                        <span class="role-icon">{role_icon}</span>
                        <span class="role-name">{conv['role'].title()}</span>
                        <span class="agent-id">({conv['agent_id']})</span>
                        <span class="time">{conv['time']}</span>
                        {f'<button class="expand-btn" onclick="toggleContent(\'conv_{i}\')">📖 展开</button>' if has_full_content else ''}
                    </div>
                    <div class="conversation-content">
                        <div class="content-preview">{conv['preview']}</div>
                        {f'<div class="content-full" id="conv_{i}" style="display: none;"><pre>{conv['content']}</pre></div>' if has_full_content else ''}
                    </div>
                </div>
                """
        
        if log_conversations:
            conversation_html += "<h3>📋 交互记录</h3>"
            for i, log_conv in enumerate(log_conversations):
                type_icon = "🧠" if log_conv['type'] == 'LLM调用' else "🔧" if log_conv['type'] == '工具执行' else "❌"
                has_content = log_conv.get('content', '').strip()
                # 确保所有记录都有内容（至少是占位符）
                if not has_content:
                    has_content = log_conv.get('details', '')
                
                conversation_html += f"""
                <div class="conversation-item">
                    <div class="conversation-header">
                        <span class="role-icon">{type_icon}</span>
                        <span class="role-name">{log_conv['type']}</span>
                        <span class="agent-id">({log_conv['agent']})</span>
                        <span class="time">{log_conv['time']}</span>
                        <button class="expand-btn" onclick="toggleContent('log_{i}')">📖 展开</button>
                    </div>
                    <div class="conversation-content">
                        <p class="details">{log_conv['details']}</p>
                        <div class="content-full" id="log_{i}" style="display: none;">
                            <pre>{log_conv.get('content', log_conv['details'])}</pre>
                        </div>
                    </div>
                </div>
                """
        
        # 创建HTML内容
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.config['html_template']['title']}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 40px;
            padding: 25px;
            border-radius: 10px;
            background: #f8f9fa;
            border-left: 5px solid #667eea;
        }}
        .section h2 {{
            color: #333;
            margin-top: 0;
            font-size: 1.8em;
        }}
        .overview-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .overview-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .overview-card h3 {{
            color: #667eea;
            margin: 0 0 10px 0;
        }}
        .overview-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        .overview-card .label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .code-section {{
            background: #2d3748;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            overflow-x: auto;
            margin-bottom: 20px;
        }}
        .code-section h3 {{
            color: #f7fafc;
            margin-top: 0;
        }}
        .file-structure {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            border: 1px solid #dee2e6;
        }}
        .success {{
            color: #28a745;
        }}
        .error {{
            color: #dc3545;
        }}
        .warning {{
            color: #ffc107;
        }}
        .nav-tabs {{
            display: flex;
            border-bottom: 2px solid #dee2e6;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .nav-tab {{
            padding: 10px 20px;
            background: #f8f9fa;
            border: none;
            cursor: pointer;
            border-radius: 5px 5px 0 0;
            margin-right: 5px;
            margin-bottom: 5px;
        }}
        .nav-tab.active {{
            background: #667eea;
            color: white;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        .conversation-item {{
            background: white;
            margin-bottom: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .conversation-header {{
            background: #f8f9fa;
            padding: 10px 15px;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .role-icon {{
            font-size: 1.2em;
        }}
        .role-name {{
            font-weight: bold;
            color: #333;
        }}
        .agent-id {{
            color: #666;
            font-size: 0.9em;
        }}
        .time {{
            margin-left: auto;
            color: #999;
            font-size: 0.8em;
        }}
        .conversation-content {{
            padding: 15px;
        }}
        .conversation-content pre {{
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.4;
        }}
        .conversation-content p {{
            margin: 0;
            line-height: 1.4;
        }}
        .content-preview {{
            font-weight: bold;
            color: #555;
            margin-bottom: 5px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 3px solid #667eea;
        }}
        .content-full {{
            margin-top: 10px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            border: 1px solid #dee2e6;
        }}
        .content-full pre {{
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.4;
            color: #333;
        }}
        .expand-btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 5px 12px;
            border-radius: 15px;
            border: none;
            cursor: pointer;
            font-size: 0.8em;
            margin-left: 10px;
            transition: all 0.3s ease;
        }}
        .expand-btn:hover {{
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}
        .details {{
            font-weight: bold;
            color: #667eea;
            margin-bottom: 8px;
            padding: 8px;
            background: #e3f2fd;
            border-radius: 4px;
        }}
        @media (max-width: 768px) {{
            .overview-grid {{
                grid-template-columns: 1fr;
            }}
            .header h1 {{
                font-size: 2em;
            }}
            .nav-tabs {{
                flex-direction: column;
            }}
            .nav-tab {{
                border-radius: 5px;
                margin-bottom: 2px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self.config['html_template']['title']}</h1>
            <p>{self.config['html_template']['subtitle']}</p>
            <p>实验ID: {self.experiment_report.get('experiment_id', 'N/A')} | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="content">
            <!-- 实验概览 -->
            <div class="section">
                <h2>📊 实验概览</h2>
                <div class="overview-grid">
                    <div class="overview-card">
                        <h3>执行状态</h3>
                        <div class="value {'success' if self.experiment_report.get('success') else 'error'}">
                            {'✅ 成功' if self.experiment_report.get('success') else '❌ 失败'}
                        </div>
                    </div>
                    <div class="overview-card">
                        <h3>任务耗时</h3>
                        <div class="value">{self.experiment_report.get('task_duration', 0):.2f}s</div>
                        <div class="label">总执行时间</div>
                    </div>
                    <div class="overview-card">
                        <h3>智能体交互</h3>
                        <div class="value">{self.experiment_report.get('agent_interaction_count', 0)}</div>
                        <div class="label">交互次数</div>
                    </div>
                    <div class="overview-card">
                        <h3>工作流阶段</h3>
                        <div class="value">{self.experiment_report.get('workflow_stage_count', 0)}</div>
                        <div class="label">阶段数量</div>
                    </div>
                </div>
            </div>
            
            <!-- 导航标签 -->
            <div class="nav-tabs">
                <button class="nav-tab active" onclick="showTab('conversations')">💬 对话内容</button>
                <button class="nav-tab" onclick="showTab('workflow')">🔄 工作流分析</button>
                <button class="nav-tab" onclick="showTab('performance')">📈 性能分析</button>
                <button class="nav-tab" onclick="showTab('code')">💻 代码展示</button>
                <button class="nav-tab" onclick="showTab('errors')">⚠️ 错误分析</button>
                <button class="nav-tab" onclick="showTab('files')">📁 文件结构</button>
            </div>
            
            <!-- 对话内容标签页 -->
            <div id="conversations" class="tab-content active">
                <div class="section">
                    <h2>💬 对话内容分析</h2>
                    <div class="chart-container">
                        {conversation_chart if conversation_chart else '<p>暂无对话数据</p>'}
                    </div>
                </div>
                <div class="section">
                    <h2>📝 详细对话记录</h2>
                    <div class="conversation-list">
                        {conversation_html if conversation_html else '<p>暂无对话记录</p>'}
                    </div>
                </div>
            </div>
            
            <!-- 工作流分析标签页 -->
            <div id="workflow" class="tab-content">
                <div class="section">
                    <h2>🔄 工作流执行时间线</h2>
                    <div class="chart-container">
                        {timeline_chart if timeline_chart else '<p>暂无时间线数据</p>'}
                    </div>
                </div>
            </div>
            
            <!-- 性能分析标签页 -->
            <div id="performance" class="tab-content">
                <div class="section">
                    <h2>🤖 智能体性能对比</h2>
                    <div class="chart-container">
                        {performance_chart if performance_chart else '<p>暂无性能数据</p>'}
                    </div>
                </div>
                <div class="section">
                    <h2>📊 工作流阶段时间分布</h2>
                    <div class="chart-container">
                        {summary_chart if summary_chart else '<p>暂无阶段数据</p>'}
                    </div>
                </div>
            </div>
            
            <!-- 代码展示标签页 -->
            <div id="code" class="tab-content">
                <div class="section">
                    <h2>💻 Verilog设计代码</h2>
                    <div class="code-section">
                        <h3>counter_v2.v</h3>
                        <pre>{self.design_code}</pre>
                    </div>
                </div>
                <div class="section">
                    <h2>🧪 测试台代码</h2>
                    <div class="code-section">
                        <h3>testbench_counter.v</h3>
                        <pre>{self.testbench_code[:1000]}{'...' if len(self.testbench_code) > 1000 else ''}</pre>
                    </div>
                </div>
            </div>
            
            <!-- 错误分析标签页 -->
            <div id="errors" class="tab-content">
                <div class="section">
                    <h2>⚠️ 错误类型统计</h2>
                    <div class="chart-container">
                        {error_chart if error_chart else '<p>暂无错误数据</p>'}
                    </div>
                </div>
                <div class="section">
                    <h2>🔍 错误详情分析</h2>
                    <div class="overview-card">
                        <h3>主要问题</h3>
                        <ul>
                            <li><strong>仿真编译失败</strong>：run_simulation 工具调用时出现语法错误</li>
                            <li><strong>错误信息</strong>：temp_testbench.v:1: syntax error</li>
                            <li><strong>影响</strong>：无法完成功能验证，任务流程未完全闭环</li>
                        </ul>
                        <h3>解决方案建议</h3>
                        <ul>
                            <li>检查 run_simulation 工具的语法处理逻辑</li>
                            <li>改进测试台代码生成的质量控制</li>
                            <li>增加错误恢复机制</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <!-- 文件结构标签页 -->
            <div id="files" class="tab-content">
                <div class="section">
                    <h2>📁 实验文件结构</h2>
                    <div class="file-structure">
                        📂 llm_experiments/
                        <div style="margin-left: 20px;">
                            📂 {self.experiment_path.name}/
                            <div style="margin-left: 20px;">
                                {self._generate_file_structure_html(self.file_structure)}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {{
            // 隐藏所有标签页内容
            var tabContents = document.getElementsByClassName('tab-content');
            for (var i = 0; i < tabContents.length; i++) {{
                tabContents[i].classList.remove('active');
            }}
            
            // 移除所有标签的active类
            var navTabs = document.getElementsByClassName('nav-tab');
            for (var i = 0; i < navTabs.length; i++) {{
                navTabs[i].classList.remove('active');
            }}
            
            // 显示选中的标签页
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }}

        function toggleContent(id) {{
            const contentFull = document.getElementById(id);
            if (contentFull) {{
                contentFull.style.display = contentFull.style.display === 'none' ? 'block' : 'none';
            }}
        }}
    </script>
</body>
</html>
        """
        
        # 保存HTML文件
        output_path = self.output_dir / self.config['output']['filename_template'].format(experiment_name=self.experiment_path.name)
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML报告已生成: {output_path}")
        return output_path

def main():
    """主函数"""
    print("🎯 开始生成V-Agent实验可视化HTML报告...")
    
    import argparse
    parser = argparse.ArgumentParser(description="生成V-Agent实验可视化HTML报告")
    parser.add_argument("--experiment-path", type=str, help="实验路径，例如：./llm_experiments/my_experiment")
    parser.add_argument("--output-dir", type=str, help="输出目录，例如：./reports")
    parser.add_argument("--config-file", type=str, help="自定义配置文件路径")
    
    args = parser.parse_args()
    
    experiment_path = args.experiment_path if args.experiment_path else None
    output_dir = args.output_dir if args.output_dir else None
    config_file = args.config_file if args.config_file else None
    
    visualizer = HTMLVisualizer(experiment_path=experiment_path, output_dir=output_dir, config_file=config_file)
    output_file = visualizer.generate_html_report()
    
    if output_file:
        print(f"\n🎉 报告生成成功！")
        print(f"📄 文件路径: {output_file}")
        print(f"🌐 请在浏览器中打开该文件查看完整报告")
        print(f"\n💡 提示:")
        print(f"   - 双击HTML文件即可在浏览器中打开")
        print(f"   - 报告包含交互式图表，可以缩放、悬停查看详情")
        print(f"   - 使用标签页切换不同的分析视图")
        print(f"   - 新增了对话内容展示功能")
    else:
        print("❌ 报告生成失败，请检查实验数据文件")

if __name__ == "__main__":
    main() 