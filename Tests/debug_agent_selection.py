#!/usr/bin/env python3
"""
Debug script for testing agent selection logic in the centralized coordinator.
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
from llm_integration.enhanced_llm_client import EnhancedLLMClient

# Configure logging to see all debug messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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

async def test_agent_selection():
    """Test the agent selection logic with debug output."""
    
    print("🚀 Starting Agent Selection Debug Test")
    
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
    
    # Create LLM client (you can use None to test simple selection)
    llm_client = None  # Set to None to test simple selection first
    # Uncomment the next line to test with LLM selection (need real API key)
    # llm_client = EnhancedLLMClient(framework_config)
    
    # Create coordinator
    coordinator = LLMCoordinatorAgent(framework_config, llm_client)
    
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
            "name": "Generic Task",
            "task": "Help me with this circuit"
        },
        {
            "name": "Complex Design Task",
            "task": "Create a complex multi-stage pipeline processor with hazard detection and forwarding units in Verilog HDL"
        }
    ]
    
    print(f"\n🧪 Testing Agent Selection Scenarios:")
    
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
            
            # Select best agent
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
    
    print(f"\n✅ Agent Selection Debug Test Complete")

if __name__ == "__main__":
    asyncio.run(test_agent_selection())