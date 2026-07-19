import ast
import unittest
from pathlib import Path


PACKAGE_PATH = Path(
    "app/intelligence/candidate_compatibility"
)


FORBIDDEN_TERMS = (
    "BUY",
    "SELL",
    "LONG",
    "SHORT",
    "ENTRY_ORDER",
    "TAKE_PROFIT",
    "STOP_LOSS",
    "PREDICT",
    "SCORE",
    "RANK",
    "EXECUTE",
    "MIGRATE",
    "AUTO_UPGRADE",
)


FORBIDDEN_IMPORTS = (
    "requests",
    "aiohttp",
    "ccxt",
    "sqlite3",
    "telegram",
)


class TestCandidateCompatibilityBoundary(unittest.TestCase):

    def test_no_decision_or_execution_logic(self):
        violations = []

        for path in PACKAGE_PATH.glob("*.py"):
            source = path.read_text(
                encoding="utf-8"
            )

            upper = source.upper()

            for term in FORBIDDEN_TERMS:
                if term in upper:
                    violations.append(
                        f"{path}: {term}"
                    )

        self.assertEqual(
            violations,
            [],
            msg="\n".join(violations),
        )


    def test_no_external_dependencies(self):
        violations = []

        for path in PACKAGE_PATH.glob("*.py"):

            tree = ast.parse(
                path.read_text(
                    encoding="utf-8"
                ),
                filename=str(path),
            )

            for node in ast.walk(tree):

                imports = []

                if isinstance(node, ast.Import):
                    imports = [
                        item.name.split(".")[0]
                        for item in node.names
                    ]

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports = [
                            node.module.split(".")[0]
                        ]

                for item in imports:
                    if item in FORBIDDEN_IMPORTS:
                        violations.append(
                            f"{path}: {item}"
                        )

        self.assertEqual(
            violations,
            [],
            msg="\n".join(violations),
        )


if __name__ == "__main__":
    unittest.main()
