
"""PRIDE Kernel v0.2
A local, simulated agent-management foundation for KURO.
Not a production security or malware-detection system.
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from typing import Optional


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


class Rank(str, Enum):
    COLONEL = "colonel"
    TEAM_LEADER = "team_leader"
    SENIOR = "senior_employee"
    EMPLOYEE = "employee"
    JUNIOR = "junior_employee"
    INTERN = "intern"


REPORT_TYPES = {
    "health", "task", "bug", "security", "diagnostic"
}

# Rank alone does not grant permissions. Every agent has an
# explicit permission list, checked for every authorized action.
RANK_PERMISSIONS = {
    Rank.COLONEL: {
        "registry.read", "routing.manage", "reports.read",
        "security.coordinate", "workforce.reassign",
    },
    Rank.TEAM_LEADER: {
        "personal.coordinate", "gaming.coordinate",
        "creator.coordinate", "reports.read",
    },
    Rank.SENIOR: {
        "diagnostics.run", "patch.propose", "tests.run",
        "reports.read",
    },
    Rank.EMPLOYEE: set(),
    Rank.JUNIOR: {"reports.submit", "tests.run"},
    Rank.INTERN: {"reports.submit", "health.check"},
}


@dataclass
class Agent:
    agent_id: str
    name: str
    rank: Rank
    role: str
    leader_id: Optional[str] = None
    permissions: set[str] = field(default_factory=set)
    status: AgentStatus = AgentStatus.READY
    original_rank: Optional[Rank] = None


class PrideKernel:
    """PRIDE: registry, permissions, reports and containment."""

    def __init__(self):
        self.state = SystemState.NORMAL
        self.agents: dict[str, Agent] = {}
        self.reports: list[dict] = []
        self.audit_log: list[dict] = []
        self._register_workforce()

    def _log(self, event, details):
        self.audit_log.append({
            "time": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "details": str(details)[:1000],
        })

    def _add(self, agent_id, name, rank, role,
             leader_id=None, permissions=None):
        if agent_id in self.agents:
            raise ValueError(f"Duplicate agent ID: {agent_id}")

        rank = Rank(rank)
        assigned = set(permissions or [])
        assigned.update(RANK_PERMISSIONS[rank])

        self.agents[agent_id] = Agent(
            agent_id=agent_id,
            name=name,
            rank=rank,
            role=role,
            leader_id=leader_id,
            permissions=assigned,
        )

    def _register_workforce(self):
        self._add(
            "KURO-01", "PRIDE", Rank.COLONEL,
            "Kernel Commander",
            permissions={
                "registry.read", "routing.manage", "reports.read",
                "security.coordinate", "workforce.reassign",
            },
        )

        self._add(
            "KURO-02", "ENVY", Rank.TEAM_LEADER,
            "Personal Operations", "KURO-01",
            {"personal.coordinate"},
        )
        self._add(
            "KURO-03", "WRATH", Rank.TEAM_LEADER,
            "Gaming and Creator Operations", "KURO-01",
            {"gaming.coordinate", "creator.coordinate"},
        )

        self._add(
            "KURO-04", "Senior A", Rank.SENIOR,
            "Diagnostics and Recovery Support", "KURO-01",
        )
        self._add(
            "KURO-05", "Senior B", Rank.SENIOR,
            "Quality Assurance and Testing", "KURO-01",
        )

        employees = [
            ("KURO-06", "GREED", "Personal Life Agent", "KURO-02",
             {"personal.tasks", "reminders.manage"}),
            ("KURO-07", "SLOTH", "Research Agent", "KURO-02",
             {"research.search", "research.summarize"}),
            ("KURO-08", "GLUTTONY", "Travel and Orders Agent", "KURO-02",
             {"travel.search", "orders.prepare"}),
            ("KURO-09", "LUST", "PC Operations Agent", "KURO-03",
             {"pc.tasks.request", "apps.manage"}),
            ("KURO-10", "KURO", "Gaming Strategist", "KURO-03",
             {"gaming.research", "gaming.plan"}),
        ]
        for aid, name, role, leader, permissions in employees:
            self._add(
                aid, name, Rank.EMPLOYEE, role, leader, permissions
            )

        self._add(
            "KURO-11", "SHINIGAMI", Rank.JUNIOR,
            "Creator Studio Agent", "KURO-03",
            {"creator.draft", "creator.research"},
        )
        self._add(
            "KURO-12", "GHOST", Rank.JUNIOR,
            "Channel Analysis and Learning Coach", "KURO-03",
            {"learning.explain", "analytics.analyze"},
        )
        self._add(
            "KURO-13", "Junior C", Rank.JUNIOR,
            "Task Testing and Support", "KURO-02",
        )

        self._add(
            "KURO-14", "Intern A", Rank.INTERN,
            "Bug Reproduction", "KURO-01",
            {"diagnostics.basic"},
        )
        self._add(
            "KURO-15", "Intern B", Rank.INTERN,
            "Health Checks", "KURO-01",
        )

        self._log("workforce_registered", f"{len(self.agents)} agents")

    def authorize(self, agent_id, permission):
        agent = self.agents.get(agent_id)
        if agent is None:
            return False, "Unknown agent"

        if self.state != SystemState.NORMAL:
            return False, f"System state is {self.state.value}"

        if agent.status in {
            AgentStatus.UNRESPONSIVE,
            AgentStatus.QUARANTINED,
            AgentStatus.RECOVERY,
        }:
            return False, f"Agent status is {agent.status.value}"

        if permission not in agent.permissions:
            return False, "Permission denied"

        return True, "Authorized"

    def submit_report(self, agent_id, report_type, details):
        agent = self.agents.get(agent_id)
        if agent is None:
            return {"ok": False, "error": "Unknown agent"}

        if agent.status == AgentStatus.QUARANTINED:
            return {"ok": False, "error": "Agent is quarantined"}

        if report_type not in REPORT_TYPES:
            return {"ok": False, "error": "Invalid report type"}

        report = {
            "agent_id": agent_id,
            "type": report_type,
            "details": str(details)[:1000],
            "time": datetime.now(timezone.utc).isoformat(),
        }
        self.reports.append(report)
        self._log("report_received", f"{agent_id}: {report_type}")
        return {"ok": True, "report": report}

    def quarantine(self, agent_id, reason):
        agent = self.agents.get(agent_id)
        if agent is None:
            return {"ok": False, "error": "Unknown agent"}

        agent.status = AgentStatus.QUARANTINED
        self._log("agent_quarantined", f"{agent_id}: {reason}")
        return {"ok": True, "status": agent.status.value}

    def set_system_state(self, state):
        try:
            new_state = SystemState(state)
        except (ValueError, TypeError):
            return {"ok": False, "error": "Invalid system state"}

        self.state = new_state
        self._log("system_state_changed", new_state.value)
        return {"ok": True, "state": self.state.value}

    def reassign_rank(self, actor_id, target_id, new_rank,
                      reason, recovery_verified=False):
        """Simulated rank change; not a secure remote authorization API."""
        actor = self.agents.get(actor_id)
        target = self.agents.get(target_id)

        if actor is None or target is None:
            return {"ok": False, "error": "Unknown agent"}

        if actor_id != "KURO-01":
            return {"ok": False, "error": "Kernel approval required"}

        if self.state != SystemState.NORMAL:
            return {"ok": False, "error": "System is not in NORMAL state"}

        try:
            new_rank = Rank(new_rank)
        except (ValueError, TypeError):
            return {"ok": False, "error": "Invalid rank"}

        if target_id == "KURO-01":
            return {"ok": False, "error": "Kernel rank cannot be reassigned"}

        if target.status in {
            AgentStatus.QUARANTINED,
            AgentStatus.RECOVERY,
        } and not recovery_verified:
            return {
                "ok": False,
                "error": "Verify recovery before reassignment",
            }

        old_rank = target.rank
        target.original_rank = target.original_rank or old_rank
        target.rank = new_rank

        # Rebuild permissions from the new rank and retain only
        # explicitly approved permissions appropriate to the role.
        rank_defaults = RANK_PERMISSIONS[new_rank]
        target.permissions.intersection_update(rank_defaults)
        target.permissions.update(rank_defaults)

        self._log(
            "rank_reassigned",
            f"{target_id}: {old_rank.value} -> {new_rank.value}; "
            f"reason={reason}",
        )
        return {
            "ok": True,
            "agent_id": target_id,
            "old_rank": old_rank.value,
            "new_rank": new_rank.value,
        }

    def begin_recovery(self, agent_id):
        agent = self.agents.get(agent_id)
        if agent is None:
            return {"ok": False, "error": "Unknown agent"}

        agent.status = AgentStatus.RECOVERY
        self.state = SystemState.RECOVERY
        self._log("recovery_started", agent_id)
        return {"ok": True, "status": agent.status.value}

    def complete_recovery(self, agent_id, verified=False):
        agent = self.agents.get(agent_id)
        if agent is None:
            return {"ok": False, "error": "Unknown agent"}

        if not verified:
            return {
                "ok": False,
                "error": "Independent verification required",
            }

        agent.status = AgentStatus.READY
        self._log("recovery_verified", agent_id)
        return {"ok": True, "status": agent.status.value}

    def workforce_report(self):
        return [
            {
                "id": agent.agent_id,
                "name": agent.name,
                "rank": agent.rank.value,
                "role": agent.role,
                "leader": agent.leader_id,
                "status": agent.status.value,
                "permissions": sorted(agent.permissions),
            }
            for agent in self.agents.values()
        ]


if __name__ == "__main__":
    pride = PrideKernel()
    print("PRIDE Kernel v0.2")
    print("System state:", pride.state.value)
    print("Registered positions:", len(pride.agents))
    for agent in pride.workforce_report():
        print(
            agent["id"], "|", agent["name"],
            "|", agent["rank"], "|", agent["status"]
        )
