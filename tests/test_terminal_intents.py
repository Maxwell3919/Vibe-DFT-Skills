from __future__ import annotations

import copy
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import operation_routes
import skill_registry


ROUTES = operation_routes.load_registry()
SKILLS = skill_registry.load_registry()

PHASE_A1_BLOCKED_INTENTS = {
    "scheduler-submit",
    "scheduler-control",
    "execution-authorization",
    "scientific-acceptance-decision",
    "structure-export",
    "structure-transformation",
    "scientific-report",
    "review-response",
    "literature-plan",
}


class TerminalIntentTests(unittest.TestCase):
    def _codes(self, data: dict[str, object]) -> set[str]:
        return {
            finding["code"]
            for finding in operation_routes.terminal_intent_findings(
                data,
                skill_data=SKILLS,
            )
        }

    def test_canonical_terminal_intents_are_consistent(self) -> None:
        self.assertEqual(
            operation_routes.terminal_intent_findings(
                ROUTES,
                skill_data=SKILLS,
            ),
            [],
        )
        policy = ROUTES["response_policy"]
        targets = policy["terminal_intent_routes"]
        reasons = policy["terminal_intent_blocked_reasons"]
        self.assertTrue(PHASE_A1_BLOCKED_INTENTS <= set(targets))
        for intent in PHASE_A1_BLOCKED_INTENTS:
            self.assertIsNone(targets[intent])
            self.assertIn(intent, reasons)
        self.assertEqual(
            reasons["scientific-acceptance-decision"],
            "human-scientific-decision-required",
        )
        for reason in reasons.values():
            self.assertRegex(reason, re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$"))

    def test_nonactive_terminal_target_is_rejected(self) -> None:
        mutated = copy.deepcopy(ROUTES)
        mutated["response_policy"]["terminal_intent_routes"][
            "scheduler-submit"
        ] = "dft-hpc-execution"
        del mutated["response_policy"]["terminal_intent_blocked_reasons"][
            "scheduler-submit"
        ]
        self.assertIn("ROUTE_TERMINAL_TARGET_NOT_ACTIVE", self._codes(mutated))

    def test_nonroutable_terminal_target_is_rejected(self) -> None:
        mutated = copy.deepcopy(ROUTES)
        target = "qe-rigorous-calculations"
        mutated["response_policy"]["terminal_intent_routes"][
            "scheduler-submit"
        ] = target
        del mutated["response_policy"]["terminal_intent_blocked_reasons"][
            "scheduler-submit"
        ]
        mutated["routes"][target]["routable"] = False
        self.assertIn("ROUTE_TERMINAL_TARGET_NOT_ROUTABLE", self._codes(mutated))

    def test_actionless_terminal_target_is_rejected(self) -> None:
        mutated = copy.deepcopy(ROUTES)
        target = "qe-rigorous-calculations"
        mutated["response_policy"]["terminal_intent_routes"][
            "scheduler-submit"
        ] = target
        del mutated["response_policy"]["terminal_intent_blocked_reasons"][
            "scheduler-submit"
        ]
        mutated["routes"][target]["actions"] = {}
        self.assertIn("ROUTE_TERMINAL_TARGET_ACTIONLESS", self._codes(mutated))

    def test_terminal_target_without_reachable_action_is_rejected(self) -> None:
        mutated = copy.deepcopy(ROUTES)
        target = "qe-rigorous-calculations"
        mutated["response_policy"]["terminal_intent_routes"][
            "scheduler-submit"
        ] = target
        del mutated["response_policy"]["terminal_intent_blocked_reasons"][
            "scheduler-submit"
        ]
        mutated["routes"][target]["tool_sequence"] = {}
        self.assertIn(
            "ROUTE_TERMINAL_TARGET_ACTION_UNREACHABLE",
            self._codes(mutated),
        )

    def test_null_terminal_target_requires_stable_blocked_reason(self) -> None:
        mutated = copy.deepcopy(ROUTES)
        del mutated["response_policy"]["terminal_intent_blocked_reasons"][
            "scheduler-submit"
        ]
        self.assertIn(
            "ROUTE_TERMINAL_BLOCKED_REASON_MISSING",
            self._codes(mutated),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
