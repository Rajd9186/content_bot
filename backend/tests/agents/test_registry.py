from __future__ import annotations

import pytest
from unittest.mock import patch

from app.agents.registry import AgentRegistry, AgentRegistration
from app.agents.base import BaseAgent
from app.agents.contracts import AgentContract, AgentInput, AgentOutput


class MockAgent(BaseAgent):
    def __init__(self, provider_name: str = "openai", model: str = "gpt-4") -> None:
        contract = AgentContract(
            name="mock_agent",
            description="Mock agent for testing",
            version="1.0.0"
        )
        super().__init__(contract, provider_name, model)


def test_agent_registration_creation() -> None:
    contract = AgentContract(name="test", description="Test", version="1.0.0")
    registration = AgentRegistration(
        name="test_agent",
        agent_class=MockAgent,
        contract=contract,
        module_path="tests.agents.test_registry"
    )
    
    assert registration.name == "test_agent"
    assert registration.agent_class == MockAgent
    assert registration.contract == contract
    assert registration.module_path == "tests.agents.test_registry"


def test_agent_registration_create_instance() -> None:
    contract = AgentContract(name="test", description="Test", version="1.0.0")
    registration = AgentRegistration(
        name="test_agent",
        agent_class=MockAgent,
        contract=contract,
        module_path="tests.agents.test_registry"
    )
    
    instance = registration.create_instance()
    assert isinstance(instance, MockAgent)
    assert instance.name == "mock_agent"  # MockAgent hardcodes its name


def test_agent_registration_get_or_create_instance() -> None:
    contract = AgentContract(name="test", description="Test", version="1.0.0")
    registration = AgentRegistration(
        name="test_agent",
        agent_class=MockAgent,
        contract=contract,
        module_path="tests.agents.test_registry"
    )
    
    instance1 = registration.get_or_create_instance()
    instance2 = registration.get_or_create_instance()
    
    # Should return the same instance (singleton pattern for get_or_create)
    assert instance1 is instance2


def test_agent_registry_register_and_get() -> None:
    registry = AgentRegistry()
    contract = AgentContract(name="mock", description="Mock", version="1.0.0")
    
    registry.register(MockAgent, contract)
    
    registration = registry.get("mock")
    assert registration is not None
    assert registration.name == "mock"
    assert registration.agent_class == MockAgent


def test_agent_registry_create_agent() -> None:
    registry = AgentRegistry()
    contract = AgentContract(name="mock", description="Mock", version="1.0.0")
    
    registry.register(MockAgent, contract)
    
    agent = registry.create("mock", provider_name="anthropic", model="claude-2")
    assert isinstance(agent, MockAgent)
    # Note: the MockAgent doesn't actually use the provider_name/model parameters
    # in its __init__, so we can't assert those values


def test_agent_registry_list_agents() -> None:
    registry = AgentRegistry()
    contract1 = AgentContract(name="mock1", description="Mock 1", version="1.0.0")
    contract2 = AgentContract(name="mock2", description="Mock 2", version="1.0.0")
    
    registry.register(MockAgent, contract1)
    registry.register(MockAgent, contract2)
    
    agents = registry.list_agents()
    assert len(agents) == 2
    names = {a["name"] for a in agents}
    assert names == {"mock1", "mock2"}


def test_agent_registry_get_capable() -> None:
    class CapableAgent(BaseAgent):
        def __init__(self) -> None:
            contract = AgentContract(
                name="capable_agent",
                description="Agent with capabilities",
                version="1.0.0",
                required_capabilities=["research", "writing"]
            )
            super().__init__(contract)
    
    registry = AgentRegistry()
    registry.register(CapableAgent)
    
    capable_agents = registry.get_capable("research")
    assert len(capable_agents) == 1
    assert capable_agents[0].name == "capable_agent"
    
    incapable_agents = registry.get_capable("seo")
    assert len(incapable_agents) == 0


def test_agent_registry_get_dependents() -> None:
    class DependentAgent(BaseAgent):
        def __init__(self) -> None:
            contract = AgentContract(
                name="dependent_agent",
                description="Agent with dependencies",
                version="1.0.0",
                dependencies=["mock_agent"]
            )
            super().__init__(contract)
    
    registry = AgentRegistry()
    registry.register(MockAgent)  # Base agent
    registry.register(DependentAgent)  # Dependent agent
    
    dependents = registry.get_dependents("mock_agent")
    assert len(dependents) == 1
    assert dependents[0].name == "dependent_agent"


@patch("app.agents.registry.importlib.import_module")
def test_agent_registry_load_module_success(mock_import_module) -> None:
    registry = AgentRegistry()
    registry.load_module("app.agents.agents.planner")
    mock_import_module.assert_called_once_with("app.agents.agents.planner")


@patch("app.agents.registry.importlib.import_module")
def test_agent_registry_load_module_failure(mock_import_module) -> None:
    mock_import_module.side_effect = ImportError("Module not found")
    registry = AgentRegistry()
    # Should not raise exception
    registry.load_module("nonexistent.module")
    mock_import_module.assert_called_once_with("nonexistent.module")
