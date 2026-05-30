from __future__ import annotations

import importlib
import logging
import time
from typing import Any, Optional

from app.agents.base import BaseAgent
from app.agents.contracts import AgentContract, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class AgentRegistration:
    def __init__(
        self,
        name: str,
        agent_class: type[BaseAgent],
        contract: AgentContract,
        module_path: str,
    ) -> None:
        self.name = name
        self.agent_class = agent_class
        self.contract = contract
        self.module_path = module_path
        self._instance: Optional[BaseAgent] = None
        self._health_status: str = "unknown"
        self._last_health_check: float = 0.0

    def create_instance(
        self, provider_name: str = "openai", model: Optional[str] = None,
    ) -> BaseAgent:
        return self.agent_class(provider_name=provider_name, model=model)

    def get_or_create_instance(
        self, provider_name: str = "openai", model: Optional[str] = None,
    ) -> BaseAgent:
        if self._instance is None:
            self._instance = self.create_instance(provider_name, model)
        return self._instance

    @property
    def health(self) -> str:
        return self._health_status

    def check_health(self) -> str:
        self._last_health_check = time.time()
        try:
            inst = self.create_instance()
            if inst is not None:
                self._health_status = "healthy"
            else:
                self._health_status = "degraded"
        except Exception as e:
            self._health_status = "unhealthy"
            logger.error("Health check failed for %s: %s", self.name, e)
        return self._health_status

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.contract.version,
            "description": self.contract.description,
            "health": self._health_status,
            "module_path": self.module_path,
            "capabilities": self.contract.required_capabilities,
            "dependencies": self.contract.dependencies,
            "retry_policy": self.contract.retry_policy.model_dump(),
            "timeout_policy": self.contract.timeout_policy.model_dump(),
        }


class AgentRegistry:
    def __init__(self) -> None:
        self._registrations: dict[str, AgentRegistration] = {}

    def register(
        self,
        agent_class: type[BaseAgent],
        contract: Optional[AgentContract] = None,
    ) -> None:
        if contract is None:
            instance = agent_class()
            contract = instance.contract
        name = contract.name
        module_path = f"{agent_class.__module__}.{agent_class.__qualname__}"

        if name in self._registrations:
            logger.warning("Overwriting existing agent registration: %s", name)

        self._registrations[name] = AgentRegistration(
            name=name,
            agent_class=agent_class,
            contract=contract,
            module_path=module_path,
        )
        logger.info("Registered agent: %s (v%s)", name, contract.version)

    def get(self, name: str) -> Optional[AgentRegistration]:
        return self._registrations.get(name)

    def create(
        self,
        name: str,
        provider_name: str = "openai",
        model: Optional[str] = None,
    ) -> BaseAgent:
        registration = self.get(name)
        if registration is None:
            raise ValueError(f"Unknown agent: {name}")
        return registration.create_instance(
            provider_name=provider_name, model=model,
        )

    def get_or_create(
        self,
        name: str,
        provider_name: str = "openai",
        model: Optional[str] = None,
    ) -> BaseAgent:
        registration = self.get(name)
        if registration is None:
            raise ValueError(f"Unknown agent: {name}")
        return registration.get_or_create_instance(
            provider_name=provider_name, model=model,
        )

    def list_agents(self) -> list[dict[str, Any]]:
        return [
            reg.to_dict()
            for reg in sorted(
                self._registrations.values(), key=lambda r: r.name
            )
        ]

    def check_all_health(self) -> dict[str, str]:
        results = {}
        for name, reg in self._registrations.items():
            results[name] = reg.check_health()
        return results

    def get_capable(self, capability: str) -> list[AgentRegistration]:
        return [
            reg for reg in self._registrations.values()
            if capability in reg.contract.required_capabilities
        ]

    def get_dependents(self, agent_name: str) -> list[AgentRegistration]:
        return [
            reg for reg in self._registrations.values()
            if agent_name in reg.contract.dependencies
        ]

    def load_module(self, module_path: str) -> None:
        try:
            module = importlib.import_module(module_path)
            logger.info("Loaded module: %s", module_path)
        except ImportError as e:
            logger.error("Failed to load module %s: %s", module_path, e)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agents": self.list_agents(),
            "count": len(self._registrations),
        }


agent_registry = AgentRegistry()
