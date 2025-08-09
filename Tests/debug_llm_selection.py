#!/usr/bin/env python3
"""
Debug script for testing LLM-based agent selection logic.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.llm_coordinator_agent import LLMCoordinatorAgent
from core.base_agent import BaseAgent
from core.enums import AgentCapability, AgentStatus
from config.config import FrameworkConfig, CoordinatorConfig

# Configure logging to see all debug messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MockLLMClient:
    """Mock LLM client that logs prompts and returns predictable responses."""
    
    def __init__(self):
        self.call_count = 0
        self.last_prompt = None
    
    async def send_prompt(self, prompt: str, temperature: float = 0.1, max_tokens: int = 100, json_mode: bool = False):
        """Mock send_prompt that logs the prompt and returns a realistic response."""
        self.call_count += 1
        self.last_prompt = prompt
        
        print(f"\n{'='*80}")
        print(f"🤖 MOCK LLM CALL #{self.call_count}")
        print(f"📥 PROMPT RECEIVED:")
        print(f"{'-'*40}")
        print(prompt)
        print(f"{'-'*40}")
        print(f"🎛️ Parameters: temperature={temperature}, max_tokens={max_tokens}, json_mode={json_mode}")
        
        # More realistic agent selection logic
        response = "none"
        
        if json_mode:
            # This is a task analysis request, return JSON
            if "design" in prompt.lower():
                response = '{"task_type": "design", "complexity": 6, "required_capabilities": ["code_generation", "module_design"], "estimated_hours": 3, "priority": "medium", "dependencies": []}'
            elif "review" in prompt.lower():
                response = '{"task_type": "review", "complexity": 4, "required_capabilities": ["code_review", "quality_analysis"], "estimated_hours": 2, "priority": "medium", "dependencies": []}'
            else:
                response = '{"task_type": "unknown", "complexity": 5, "required_capabilities": ["code_generation"], "estimated_hours": 2.5, "priority": "medium", "dependencies": []}'
        else:
            # This is agent selection - analyze the prompt more carefully
            prompt_lower = prompt.lower()
            
            # Parse task type from the prompt
            if "task type: review" in prompt_lower and "code_review" in prompt_lower:
                # For review tasks, select the review agent
                if "real_code_review_agent" in prompt:
                    response = "real_code_review_agent"
                else:
                    response = "none"
            elif "task type: design" in prompt_lower and ("code_generation" in prompt_lower or "module_design" in prompt_lower):
                # For design tasks, select the design agent
                if "real_verilog_design_agent" in prompt:
                    response = "real_verilog_design_agent"
                else:
                    response = "none"
            elif "task type: testing" in prompt_lower:
                response = "none"  # No testing agent available
            else:
                # Default to design agent if available
                if "real_verilog_design_agent" in prompt:
                    response = "real_verilog_design_agent"
                else:
                    response = "none"
        
        print(f"📤 MOCK RESPONSE: '{response}'")
        print(f"{'='*80}\n")
        
        return response

class MockVerilogAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="real_verilog_design_agent",
            role="verilog_designer",
            capabilities={AgentCapability.CODE_GENERATION, AgentCapability.MODULE_DESIGN}
        )
    
    def get_capabilities(self):
        return {AgentCapability.CODE_GENERATION, AgentCapability.MODULE_DESIGN}
    
    def get_specialty_description(self) -> str:
        return "Verilog code generation and digital circuit design"
    
    async def execute_enhanced_task(self, enhanced_prompt: str, original_message, file_contents):
        return {"success": True, "message": "Mock execution"}

class MockReviewAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="real_code_review_agent",
            role="code_reviewer",
            capabilities={AgentCapability.CODE_REVIEW, AgentCapability.QUALITY_ANALYSIS}
        )
    
    def get_capabilities(self):
        return {AgentCapability.CODE_REVIEW, AgentCapability.QUALITY_ANALYSIS}
    
    def get_specialty_description(self) -> str:
        return "Code review and quality analysis for Verilog designs"
    
    async def execute_enhanced_task(self, enhanced_prompt: str, original_message, file_contents):
        return {"success": True, "message": "Mock execution"}

async def test_llm_agent_selection():
    """Test the LLM-based agent selection logic with debug output."""
    
    print("🚀 Starting LLM Agent Selection Debug Test")
    
    # Create mock configuration
    coordinator_config = CoordinatorConfig(
        max_conversation_iterations=5,
        conversation_timeout=300,
        analysis_temperature=0.1,
        analysis_max_tokens=1000,
        decision_temperature=0.1,
        decision_max_tokens=100
    )
    
    framework_config = FrameworkConfig(
        coordinator=coordinator_config,
        model_name="gpt-3.5-turbo",
        api_key="mock-key",
        temperature=0.1
    )
    
    # Create Mock LLM client
    mock_llm_client = MockLLMClient()
    
    # Create coordinator with LLM client
    coordinator = LLMCoordinatorAgent(framework_config, mock_llm_client)
    
    # Register mock agents
    verilog_agent = MockVerilogAgent()
    review_agent = MockReviewAgent()
    
    coordinator.register_agent(verilog_agent)
    coordinator.register_agent(review_agent)
    
    print(f"\n📊 Team Status:")
    team_status = coordinator.get_team_status()
    for key, value in team_status.items():
        print(f"  {key}: {value}")
    
    # Test different task scenarios
    test_scenarios = [
        {
            "name": "Verilog Design Task",
            "task": "Design a 32-bit ALU in Verilog with arithmetic and logic operations"
        },
        {
            "name": "Code Review Task", 
            "task": "Review the Verilog code for syntax errors and design quality"
        },
        {
            "name": "Ambiguous Task",
            "task": "Help me with this circuit implementation and ensure it's correct"
        },
    ]
    
    print(f"\n🧪 Testing LLM Agent Selection Scenarios:")
    
    for scenario in test_scenarios:
        print(f"\n" + "="*60)
        print(f"🔬 Test Scenario: {scenario['name']}")
        print(f"📝 Task: {scenario['task']}")
        print("-" * 60)
        
        try:
            # Analyze task requirements
            task_analysis = await coordinator.analyze_task_requirements(scenario['task'])
            print(f"📊 Task Analysis Result:")
            for key, value in task_analysis.items():
                print(f"  {key}: {value}")
            
            # Select best agent (this should trigger LLM call)
            selected_agent = await coordinator.select_best_agent(task_analysis)
            print(f"\n🎯 Selected Agent: {selected_agent}")
            
            if selected_agent:
                agent_info = coordinator.registered_agents[selected_agent]
                print(f"📋 Agent Details:")
                print(f"  Role: {agent_info.role}")
                print(f"  Capabilities: {[cap.value for cap in agent_info.capabilities]}")
                print(f"  Specialty: {agent_info.specialty_description}")
            
        except Exception as e:
            print(f"❌ Error in scenario '{scenario['name']}': {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📈 Mock LLM Statistics:")
    print(f"  Total LLM calls made: {mock_llm_client.call_count}")
    print(f"\n✅ LLM Agent Selection Debug Test Complete")

if __name__ == "__main__":
    asyncio.run(test_llm_agent_selection())