
"""PRIDE Kernel v0.2 — Initial Stress Tests
Safe, simulated tests only. No real malware is executed.
"""

import unittest

from kuro_core import PrideKernel, SystemState, AgentStatus


class PrideStressTests(unittest.TestCase):

    def setUp(self):
        # Give every test a fresh kernel.
        self.kernel = PrideKernel()

    def test_01_workforce_survives_repeated_checks(self):
        for _ in range(1000):
            self.assertEqual(len(self.kernel.agents), 15)

    def test_02_mass_report_submission(self):
        # Simulate a burst of 1000 ordinary reports.
        initial_count = len(self.kernel.reports)

        for i in range(1000):
            self.kernel.submit_report(
                "KURO-07",
                "diagnostic",
                f"Simulated stress report {i}"
            )

        self.assertEqual(
            len(self.kernel.reports),
            initial_count + 1000
        )

    def test_03_quarantined_agent_is_restricted(self):
        self.kernel.quarantine("KURO-07", "Simulated stress test")

        self.assertEqual(
            self.kernel.agents["KURO-07"].status,
            AgentStatus.QUARANTINED
        )

        self.assertFalse(
            self.kernel.authorize("KURO-07", "routing.manage")
        )

    def test_04_lockdown_blocks_authorized_operations(self):
        self.kernel.set_system_state(SystemState.LOCKDOWN)

        self.assertFalse(
            self.kernel.authorize("KURO-01", "registry.read")
        )

    def test_05_repeated_state_changes(self):
        for _ in range(100):
            self.kernel.set_system_state(SystemState.LOCKDOWN)
            self.kernel.set_system_state(SystemState.NORMAL)

        self.assertEqual(self.kernel.state, SystemState.NORMAL)


if __name__ == "__main__":
    unittest.main(verbosity=2)
