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

EXPECTED_READINESS_CLASSES = {
    "external-publish": "intentionally-disabled",
    "destructive-delete": "intentionally-disabled",
    "scheduler-submit": "missing-route",
    "scheduler-control": "missing-route",
    "execution-authorization": "human-boundary",
    "scientific-acceptance-decision": "human-boundary",
    "structure-export": "missing-route",
    "structure-transformation": "missing-route",
    "scientific-report": "missing-route",
    "review-response": "missing-route",
    "literature-plan": "missing-route",
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
        requirements = policy["terminal_intent_requirements"]
        self.assertTrue(PHASE_A1_BLOCKED_INTENTS <= set(targets))
        self.assertEqual(set(requirements), set(targets))
        for intent in PHASE_A1_BLOCKED_INTENTS:
            self.assertIsNone(targets[intent])
            self.assertIn(intent, reasons)
        self.assertEqual(
            {
                intent: requirement["readiness_class"]
                for intent, requirement in requirements.items()
            },
            EXPECTED_READINESS_CLASSES,
        )
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

    def test_scheduler_submit_rejects_reachable_non_scheduler_action(self) -> None:
        mutated = copy.deepcopy(ROUTES)
        target = "qe-rigorous-calculations"
        mutated["response_policy"]["terminal_intent_routes"][
            "scheduler-submit"
        ] = target
        del mutated["response_policy"]["terminal_intent_blocked_reasons"][
            "scheduler-submit"
        ]
        self.assertTrue(mutated["routes"][target]["actions"])
        self.assertTrue(mutated["routes"][target]["tool_sequence"])
        self.assertIn(
            "ROUTE_TERMINAL_TARGET_CAPABILITY_MISMATCH",
            self._codes(mutated),
        )

    def test_route_level_scheduler_effect_cannot_replace_action_capability(
        self,
    ) -> None:
        mutated = copy.deepcopy(ROUTES)
        target = "qe-rigorous-calculations"
        mutated["response_policy"]["terminal_intent_routes"][
            "scheduler-submit"
        ] = target
        del mutated["response_policy"]["terminal_intent_blocked_reasons"][
            "scheduler-submit"
        ]
        mutated["routes"][target]["side_effects"].append("scheduler-submit")
        self.assertIn(
            "ROUTE_TERMINAL_TARGET_CAPABILITY_MISMATCH",
            self._codes(mutated),
        )

    def test_human_boundary_rejects_non_null_skill_target(self) -> None:
        mutated = copy.deepcopy(ROUTES)
        mutated["response_policy"]["terminal_intent_routes"][
            "scientific-acceptance-decision"
        ] = "qe-rigorous-calculations"
        del mutated["response_policy"]["terminal_intent_blocked_reasons"][
            "scientific-acceptance-decision"
        ]
        self.assertIn(
            "ROUTE_TERMINAL_TARGET_CAPABILITY_MISMATCH",
            self._codes(mutated),
        )

    def test_intentionally_disabled_intent_rejects_non_null_target(self) -> None:
        mutated = copy.deepcopy(ROUTES)
        mutated["response_policy"]["terminal_intent_routes"][
            "external-publish"
        ] = "qe-rigorous-calculations"
        del mutated["response_policy"]["terminal_intent_blocked_reasons"][
            "external-publish"
        ]
        self.assertIn(
            "ROUTE_TERMINAL_TARGET_CAPABILITY_MISMATCH",
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
