import ast
import unittest
from pathlib import Path


PACKAGE_PATH = Path(
    "app/intelligence/candidate_completeness"
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
    "CONFIDENCE_SCORE",
    "RANKING",
)

FORBIDDEN_IMPORT_ROOTS = (
    "requests",
    "aiohttp",
    "ccxt",
    "sqlite3",
    "telegram",
    "pymongo",
)


class TestCandidateCompletenessBoundary(unittest.TestCase):
    def test_no_trading_or_scoring_logic(self) -> None:
        violations = []

        for path in PACKAGE_PATH.glob("*.py"):
            source = path.read_text(encoding="utf-8")
            normalized_source = source.upper()

            for term in FORBIDDEN_TERMS:
                if term in normalized_source:
                    violations.append(
                        f"{path}: forbidden term {term}"
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
                path.read_text(encoding="utf-8"),
                filename=str(path),
            )

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots = [
                        alias.name.split(".")[0]
                        for alias in node.names
                    ]
                elif isinstance(node, ast.ImportFrom):
                    imported_roots = (
                        [node.module.split(".")[0]]
                        if node.module
                        else []
                    )
                else:
                    imported_roots = []

                for imported_root in imported_roots:
                    if imported_root in FORBIDDEN_IMPORT_ROOTS:
                        violations.append(
                            f"{path}: forbidden import "
                            f"{imported_root}"
                        )

        self.assertEqual(
            violations,
            [],
            msg="\n".join(violations),
        )


if __name__ == "__main__":
    unittest.main()
