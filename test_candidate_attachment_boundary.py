import ast
import unittest
from pathlib import Path


PACKAGE_PATH = Path(
    "app/intelligence/candidate_attachment"
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
    "SIGNAL",
    "SCORE",
    "RANK",
)

FORBIDDEN_IMPORT_ROOTS = (
    "requests",
    "aiohttp",
    "ccxt",
    "sqlite3",
    "telegram",
    "pymongo",
)


class TestCandidateAttachmentBoundary(unittest.TestCase):

    def test_no_trading_or_decision_logic(self) -> None:
        violations = []

        for path in PACKAGE_PATH.glob("*.py"):
            source = path.read_text(
                encoding="utf-8"
            )

            normalized = source.upper()

            for term in FORBIDDEN_TERMS:
                if term in normalized:
                    violations.append(
                        f"{path}: {term}"
                    )

        self.assertEqual(
            violations,
            [],
            msg="\n".join(violations),
        )

    def test_no_external_dependencies(self) -> None:
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
                        alias.name.split(".")[0]
                        for alias in node.names
                    ]

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports = [
                            node.module.split(".")[0]
                        ]

                for item in imports:
                    if item in FORBIDDEN_IMPORT_ROOTS:
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
