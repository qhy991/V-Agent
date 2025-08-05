#!/usr/bin/env python3
"""
对话显示优化器
解决对话历史拼接导致输出越来越长的问题
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime


class ConversationDisplayOptimizer:
    """对话显示优化器 - 只显示最新一轮对话，避免输出冗余"""
    
    def __init__(self, max_display_rounds: int = 1, enable_compact_mode: bool = True):
        """
        初始化对话显示优化器
        
        Args:
            max_display_rounds: 最大显示轮数，默认只显示当前轮
            enable_compact_mode: 是否启用紧凑模式
        """
        self.max_display_rounds = max_display_rounds
        self.enable_compact_mode = enable_compact_mode
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def display_current_round_only(self, 
                                 user_request: str, 
                                 ai_response: str, 
                                 iteration_count: int = 1,
                                 agent_id: str = "unknown",
                                 additional_info: Optional[Dict[str, Any]] = None) -> str:
        """
        只显示当前轮次的对话，避免历史累积
        
        Args:
            user_request: 用户请求
            ai_response: AI响应 
            iteration_count: 迭代次数
            agent_id: 智能体ID
            additional_info: 额外信息
            
        Returns:
            格式化的当前轮次显示内容
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 构建显示内容
        display_parts = []
        
        # 标题
        display_parts.append(f"\n{'='*60}")
        display_parts.append(f"🔄 第 {iteration_count} 轮对话 | {agent_id} | {timestamp}")
        display_parts.append(f"{'='*60}")
        
        # 用户请求（如果启用紧凑模式，则截断长内容）
        if self.enable_compact_mode and len(user_request) > 200:
            truncated_request = user_request[:200] + "...[截断]"
            display_parts.append(f"📤 用户请求: {truncated_request}")
        else:
            display_parts.append(f"📤 用户请求: {user_request}")
        
        # AI响应（如果启用紧凑模式，则截断长内容）
        if self.enable_compact_mode and len(ai_response) > 500:
            truncated_response = ai_response[:500] + "...[截断]"
            display_parts.append(f"📥 AI响应: {truncated_response}")
        else:
            display_parts.append(f"📥 AI响应: {ai_response}")
        
        # 额外信息
        if additional_info:
            display_parts.append(f"📊 额外信息:")
            for key, value in additional_info.items():
                display_parts.append(f"   - {key}: {value}")
        
        display_parts.append(f"🔚 第 {iteration_count} 轮完成")
        display_parts.append(f"{'='*60}\n")
        
        return "\n".join(display_parts)
    
    def optimize_conversation_history(self, 
                                    conversation_history: List[Dict[str, str]], 
                                    keep_last_n_turns: int = 2) -> List[Dict[str, str]]:
        """
        优化对话历史，只保留最近N轮对话
        
        Args:
            conversation_history: 完整对话历史
            keep_last_n_turns: 保留最近N轮对话
            
        Returns:
            优化后的对话历史
        """
        if not conversation_history:
            return conversation_history
        
        # 找到system prompt
        system_messages = [msg for msg in conversation_history if msg.get("role") == "system"]
        non_system_messages = [msg for msg in conversation_history if msg.get("role") != "system"]
        
        # 只保留最近的N轮对话（每轮包含user和assistant消息）
        if len(non_system_messages) > keep_last_n_turns * 2:
            recent_messages = non_system_messages[-(keep_last_n_turns * 2):]
        else:
            recent_messages = non_system_messages
        
        # 重新组合：system messages + 最近的对话
        optimized_history = system_messages + recent_messages
        
        self.logger.info(f"🔧 对话历史优化: {len(conversation_history)} -> {len(optimized_history)} 条消息")
        
        return optimized_history
    
    def create_conversation_summary(self, 
                                  conversation_history: List[Dict[str, str]]) -> str:
        """
        创建对话历史摘要，用于替代完整历史
        
        Args:
            conversation_history: 对话历史
            
        Returns:
            对话摘要
        """
        if not conversation_history:
            return "无对话历史"
        
        non_system_messages = [msg for msg in conversation_history if msg.get("role") != "system"]
        
        if len(non_system_messages) <= 4:  # 2轮对话以内
            return "对话较短，保留完整历史"
        
        # 统计信息
        user_messages = len([msg for msg in non_system_messages if msg.get("role") == "user"])
        assistant_messages = len([msg for msg in non_system_messages if msg.get("role") == "assistant"])
        
        # 获取第一轮和最后一轮的主题
        first_user_msg = next((msg for msg in non_system_messages if msg.get("role") == "user"), {})
        last_user_msg = next((msg for msg in reversed(non_system_messages) if msg.get("role") == "user"), {})
        
        first_topic = first_user_msg.get("content", "")[:50] + "..." if len(first_user_msg.get("content", "")) > 50 else first_user_msg.get("content", "")
        last_topic = last_user_msg.get("content", "")[:50] + "..." if len(last_user_msg.get("content", "")) > 50 else last_user_msg.get("content", "")
        
        summary = f"""
📋 对话历史摘要:
- 总轮数: {user_messages} 轮
- 用户消息: {user_messages} 条
- AI响应: {assistant_messages} 条
- 首轮主题: {first_topic}
- 末轮主题: {last_topic}
- 状态: 保留最近2轮完整对话，其余已压缩
        """.strip()
        
        return summary
    
    def apply_display_optimization(self, 
                                 original_output: str, 
                                 current_round_info: Dict[str, Any]) -> str:
        """
        应用显示优化，替换原始输出中的冗余内容
        
        Args:
            original_output: 原始输出内容
            current_round_info: 当前轮次信息
            
        Returns:
            优化后的输出内容
        """
        # 如果原始输出过长，使用优化显示
        if len(original_output) > 2000:
            self.logger.info("🔧 检测到输出过长，应用显示优化")
            return self.display_current_round_only(
                user_request=current_round_info.get("user_request", ""),
                ai_response=current_round_info.get("ai_response", "")[:500] + "...[已优化显示]",
                iteration_count=current_round_info.get("iteration_count", 1),
                agent_id=current_round_info.get("agent_id", "unknown"),
                additional_info={
                    "原始长度": f"{len(original_output)} 字符",
                    "优化状态": "已应用显示优化"
                }
            )
        
        return original_output


# 全局优化器实例
conversation_optimizer = ConversationDisplayOptimizer(
    max_display_rounds=1,
    enable_compact_mode=True
)


def optimize_agent_output(agent_id: str, 
                         user_request: str, 
                         ai_response: str, 
                         iteration_count: int = 1) -> str:
    """
    便捷函数：优化智能体输出显示
    
    Args:
        agent_id: 智能体ID
        user_request: 用户请求
        ai_response: AI响应
        iteration_count: 迭代次数
        
    Returns:
        优化后的显示内容
    """
    return conversation_optimizer.display_current_round_only(
        user_request=user_request,
        ai_response=ai_response,
        iteration_count=iteration_count,
        agent_id=agent_id
    )


def optimize_conversation_for_ollama(conversation_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    便捷函数：为Ollama优化对话历史格式
    
    Args:
        conversation_history: 原始对话历史
        
    Returns:
        优化后的对话历史
    """
    return conversation_optimizer.optimize_conversation_history(
        conversation_history=conversation_history,
        keep_last_n_turns=2  # Ollama通常不需要太长的历史
    )


if __name__ == "__main__":
    # 测试显示优化器
    optimizer = ConversationDisplayOptimizer()
    
    # 测试当前轮显示
    display_content = optimizer.display_current_round_only(
        user_request="设计一个计数器模块",
        ai_response="我将为您设计一个8位计数器模块...",
        iteration_count=1,
        agent_id="verilog_agent",
        additional_info={"执行时间": "1.5秒", "工具调用": "write_file"}
    )
    
    print(display_content)
    
    # 测试对话历史优化
    sample_history = [
        {"role": "system", "content": "你是一个Verilog设计助手"},
        {"role": "user", "content": "设计ALU"},
        {"role": "assistant", "content": "好的，我将设计ALU..."},
        {"role": "user", "content": "添加测试台"},
        {"role": "assistant", "content": "我将添加测试台..."},
        {"role": "user", "content": "修复错误"},
        {"role": "assistant", "content": "我将修复错误..."}
    ]
    
    optimized_history = optimizer.optimize_conversation_history(sample_history)
    print(f"\n历史优化: {len(sample_history)} -> {len(optimized_history)} 条消息")
    
    summary = optimizer.create_conversation_summary(sample_history)
    print(f"\n{summary}")