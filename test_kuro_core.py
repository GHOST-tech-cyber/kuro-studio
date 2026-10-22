
import unittest

from kuro_core import (
    PrideKernel,
    SystemState,
    AgentStatus,
)


class TestPrideKernel(unittest.TestCase):

    def setUp(self):
        self.pride = PrideKernel()

    def test_registers_15_positions(self):
        self.assertEqual(len(self.pride.agents), 15)

    def test_starts_in_normal_state(self):
        self.assertEqual(self.pride.state, SystemState.NORMAL)

    def test_known_permission_is_allowed(self):
        allowed, _ = self.pride.authorize(
            "KURO-07", "research.search"
        )
        self.assertTrue(allowed)

    def test_unauthorized_permission_is_denied(self):
        allowed, _ = self.pride.authorize(
            "KURO-07", "security.admin"
        )
        self.assertFalse(allowed)

    def test_quarantined_agent_is_blocked(self):
        self.pride.quarantine("KURO-07", "Test only")
        allowed, _ = self.pride.authorize(
            "KURO-07", "research.search"
        )
        self.assertFalse(allowed)

    def test_lockdown_blocks_normal_authorization(self):
        self.pride.set_system_state(SystemState.LOCKDOWN)
        allowed, _ = self.pride.authorize(
            "KURO-07", "research.search"
        )
        self.assertFalse(allowed)

    def test_invalid_state_is_rejected(self):
        result = self.pride.set_system_state("UNKNOWN")
        self.assertFalse(result["ok"])

    def test_unknown_agent_is_rejected(self):
        allowed, _ = self.pride.authorize(
            "KURO-99", "research.search"
        )
        self.assertFalse(allowed)


if __name__ == "__main__":
    unittest.main()
