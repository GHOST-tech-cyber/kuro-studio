
"""PRIDE: KURO's first kernel prototype.
This version manages simulated agents only.
It does not execute agent code or control external services.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class SystemState(str, Enum):
    NORMAL = "NORMAL"
    LOCKDOWN = "LOCKDOWN"
    RECOVERY = "RECOVERY"


class AgentStatus(str, Enum):
    READY = "READY"
    BUSY = "BUSY"
    UNRESPONSIVE = "UNRESPONSIVE"
    QUARANTINED = "QUARANTINED"
    RECOVERY = "RECOVERY"


@dataclass
class Agent:
    agent_id: str
    name: str
    rank: str
    role: str
    leader_id: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.READY


class PrideKernel:
    """Central registry and basic permission gate."""

    def __init__(self):
        self.state = SystemState.NORMAL
        self.agents: Dict[str, Agent] = {}
        self.reports: List[dict] = []
        self._register_workforce()

    def _register_workforce(self):
        # Colonel / Kernel
        self._add("KURO-01", "PRIDE", "colonel", "Kernel Commander",
                  None, ["registry.read", "routing.manage",
                         "reports.read", "security.coordinate"])

        # Team leaders
        self._add("KURO-02", "ENVY", "team_leader",
                  "Personal Operations", "KURO-01",
                  ["personal.coordinate", "reports.read"])
        self._add("KURO-03", "WRATH", "team_leader",
                  "Gaming and Creator Operations", "KURO-01",
                  ["gaming.coordinate", "creator.coordinate",
                   "reports.read"])

        # Two senior employees
        self._add("KURO-04", "Senior A", "senior_employee",
                  "Diagnostics and Recovery Support", "KURO-01",
                  ["diagnostics.run", "patch.propose", "reports.read"])
        self._add("KURO-05", "Senior B", "senior_employee",
                  "Quality Assurance and Testing", "KURO-01",
                  ["tests.run", "diagnostics.run", "reports.read"])

        # Five employees
        employee_roles = [
            ("KURO-06", "GREED", "Personal Life Agent", "KURO-02",
             ["personal.tasks", "reminders.manage"]),
            ("KURO-07", "SLOTH", "Research Agent", "KURO-02",
             ["research.search", "research.summarize"]),
            ("KURO-08", "GLUTTONY", "Travel and Orders Agent", "KURO-02",
             ["travel.search", "orders.prepare"]),
            ("KURO-09", "LUST", "PC Operations Agent", "KURO-03",
             ["pc.tasks.request", "apps.manage"]),
            ("KURO-10", "KURO", "Gaming Strategist", "KURO-03",
             ["gaming.research", "gaming.plan"]),
        ]
        for agent_id, name, role, leader_id, permissions in employee_roles:
            self._add(agent_id, name, "employee", role, leader_id, permissions)

        # Three junior employees
        self._add("KURO-11", "SHINIGAMI", "junior_employee",
                  "Creator Studio Agent", "KURO-03",
                  ["creator.draft", "creator.research"])
        self._add("KURO-12", "GHOST", "junior_employee",
                  "Channel Analysis and Learning Coach", "KURO-03",
                  ["learning.explain", "analytics.analyze"])
        self._add("KURO-13", "Junior C", "junior_employee",
                  "Task Testing and Support", "KURO-02",
                  ["tests.run", "reports.submit"])

        # Two interns
        self._add("KURO-14", "Intern A", "intern",
                  "Bug Reproduction", "KURO-01",
                  ["diagnostics.basic", "reports.submit"])
        self._add("KURO-15", "Intern B", "intern",
                  "Health Checks", "KURO-01",
                  ["health.check", "reports.submit"])

    def _add(self, agent_id, name, rank, role, leader_id, permissions):
        if agent_id in self.agents:
            raise ValueError(f"Duplicate agent ID: {agent_id}")
        self.agents[agent_id] = Agent(
            agent_id=agent_id,
            name=name,
            rank=rank,
            role=role,
            leader_id=leader_id,
            permissions=list(permissions),
        )

    def submit_report(self, agent_id, report_type, details):
        agent = self.agents.get(agent_id)
        if not agent:
            return {"ok": False, "error": "Unknown agent"}
        if agent.status == AgentStatus.QUARANTINED:
            return {"ok": False, "error": "Agent is quarantined"}

        report = {
            "agent_id": agent_id,
            "type": report_type,
            "details": str(details)[:1000],
        }
        self.reports.append(report)
        return {"ok": True, "report": report}

    def authorize(self, agent_id, permission):
        agent = self.agents.get(agent_id)
        if not agent:
            return False, "Unknown agent"
        if self.state != SystemState.NORMAL:
            return False, f"System state is {self.state.value}"
        if agent.status in (
            AgentStatus.UNRESPONSIVE,
            AgentStatus.QUARANTINED,
            AgentStatus.RECOVERY,
        ):
            return False, f"Agent status is {agent.status.value}"
        if permission not in agent.permissions:
            return False, "Permission denied"
        return True, "Authorized"

    def quarantine(self, agent_id, reason):
        agent = self.agents.get(agent_id)
        if not agent:
            return {"ok": False, "error": "Unknown agent"}

        agent.status = AgentStatus.QUARANTINED
        self.reports.append({
            "agent_id": agent_id,
            "type": "security",
            "details": f"Quarantined: {str(reason)[:500]}",
        })
        return {"ok": True, "status": agent.status.value}

    def set_system_state(self, state):
        try:
            new_state = SystemState(state)
        except ValueError:
            return {"ok": False, "error": "Invalid system state"}

        self.state = new_state
        return {"ok": True, "state": self.state.value}

    def workforce_report(self):
        return [
            {
                "id": agent.agent_id,
                "name": agent.name,
                "rank": agent.rank,
                "role": agent.role,
                "leader": agent.leader_id,
                "status": agent.status.value,
                "permissions": list(agent.permissions),
            }
            for agent in self.agents.values()
        ]


if __name__ == "__main__":
    pride = PrideKernel()
    print("PRIDE kernel prototype started.")
    print("System state:", pride.state.value)
    print("Registered positions:", len(pride.agents))
    for agent in pride.workforce_report():
        print(agent["id"], "-", agent["name"], "|", agent["rank"])
