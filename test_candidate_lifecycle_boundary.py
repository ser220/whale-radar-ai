import ast
import unittest
from pathlib import Path


class TestCandidateLifecycleBoundary(unittest.TestCase):

    def test_no_trading_logic(self):
        package = Path(
            "app/intelligence/candidate_lifecycle"
        )

        forbidden = {
            "BUY",
            "SELL",
            "LONG",
            "SHORT",
            "ENTRY_ORDER",
            "TAKE_PROFIT",
            "STOP_LOSS",
            "PREDICT",
        }

        for path in package.rglob("*.py"):
            content = path.read_text(
                encoding="utf-8"
            ).upper()

            for item in forbidden:
                self.assertNotIn(
                    item,
                    content,
                    msg=f"{item} found in {path}",
                )

    def test_no_external_dependencies(self):
        package = Path(
            "app/intelligence/candidate_lifecycle"
        )

        forbidden = {
            "requests",
            "aiohttp",
            "ccxt",
            "sqlite3",
            "telegram",
            "pymongo",
        }

        for path in package.rglob("*.py"):
            tree = ast.parse(
                path.read_text(
                    encoding="utf-8"
                )
            )

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = [
                        item.name
                        for item in node.names
                    ]
                elif isinstance(node, ast.ImportFrom):
                    modules = [
                        node.module or ""
                    ]
                else:
                    continue

                for module in modules:
                    for forbidden_module in forbidden:
                        self.assertNotIn(
                            forbidden_module,
                            module,
                            msg=(
                                f"{forbidden_module} "
                                f"found in {path}"
                            ),
                        )


if __name__ == "__main__":
    unittest.main()
