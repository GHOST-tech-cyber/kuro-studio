
import unittest

from kuro_core import (
    PrideKernel,
    SystemState,
    AgentStatus,
    Rank,
)


class TestPrideKernel(unittest.TestCase):

    def setUp(self):
        self.pride = PrideKernel()

    def test_registers_all_15_agents(self):
        self.assertEqual(len(self.pride.agents), 15)

    def test_agent_ids_are_unique(self):
        ids = list(self.pride.agents.keys())
        self.assertEqual(len(ids), len(set(ids)))

    def test_starts_in_normal_state(self):
        self.assertEqual(self.pride.state, SystemState.NORMAL)

    def test_agent_names_and_ranks_exist(self):
        pride = self.pride.agents["KURO-01"]
        envy = self.pride.agents["KURO-02"]
        self.assertEqual(pride.name, "PRIDE")
        self.assertEqual(pride.rank, Rank.COLONEL)
        self.assertEqual(envy.name, "ENVY")
        self.assertEqual(envy.rank, Rank.TEAM_LEADER)

    def test_authorized_research_permission(self):
        allowed, message = self.pride.authorize(
            "KURO-07", "research.search"
        )
        self.assertTrue(allowed, message)

    def test_unauthorized_permission_is_denied(self):
        allowed, _ = self.pride.authorize(
            "KURO-07", "security.admin"
        )
        self.assertFalse(allowed)

    def test_unknown_agent_is_denied(self):
        allowed, _ = self.pride.authorize(
            "KURO-99", "research.search"
        )
        self.assertFalse(allowed)

    def test_quarantined_agent_is_blocked(self):
        self.pride.quarantine("KURO-07", "Test quarantine")
        allowed, _ = self.pride.authorize(
            "KURO-07", "research.search"
        )
        self.assertFalse(allowed)

    def test_quarantined_agent_cannot_submit_report(self):
        self.pride.quarantine("KURO-07", "Test quarantine")
        result = self.pride.submit_report(
            "KURO-07", "bug", "Test report"
        )
        self.assertFalse(result["ok"])

    def test_lockdown_blocks_authorization(self):
        self.pride.set_system_state(SystemState.LOCKDOWN)
        allowed, _ = self.pride.authorize(
            "KURO-07", "research.search"
        )
        self.assertFalse(allowed)

    def test_invalid_system_state_is_rejected(self):
        result = self.pride.set_system_state("UNKNOWN")
        self.assertFalse(result["ok"])

    def test_valid_bug_report_is_recorded(self):
        result = self.pride.submit_report(
            "KURO-07", "bug", "Test bug details"
        )
        self.assertTrue(result["ok"])
        self.assertEqual(len(self.pride.reports), 1)

    def test_invalid_report_type_is_rejected(self):
        result = self.pride.submit_report(
            "KURO-07", "made_up_type", "Test"
        )
        self.assertFalse(result["ok"])

    def test_rank_reassignment_requires_kernel_approval(self):
        result = self.pride.reassign_rank(
            "KURO-02", "KURO-04",
            Rank.JUNIOR, "Test"
        )
        self.assertFalse(result["ok"])

    def test_kernel_cannot_reassign_its_own_rank(self):
        result = self.pride.reassign_rank(
            "KURO-01", "KURO-01",
            Rank.INTERN, "Test"
        )
        self.assertFalse(result["ok"])

    def test_reassignment_is_recorded(self):
        result = self.pride.reassign_rank(
            "KURO-01", "KURO-04",
            Rank.JUNIOR, "Simulated security test"
        )
        self.assertTrue(result["ok"])
        self.assertEqual(
            self.pride.agents["KURO-04"].rank,
            Rank.JUNIOR,
        )
        self.assertTrue(
            any(
                item["event"] == "rank_reassigned"
                for item in self.pride.audit_log
            )
        )

    def test_recovery_requires_verification(self):
        self.pride.begin_recovery("KURO-07")
        result = self.pride.complete_recovery(
            "KURO-07", verified=False
        )
        self.assertFalse(result["ok"])

    def test_verified_recovery_restores_agent_status(self):
        self.pride.begin_recovery("KURO-07")
        result = self.pride.complete_recovery(
            "KURO-07", verified=True
        )
        self.assertTrue(result["ok"])
        self.assertEqual(
            self.pride.agents["KURO-07"].status,
            AgentStatus.READY,
        )


if __name__ == "__main__":
    unittest.main()
