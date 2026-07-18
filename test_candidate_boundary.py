import ast
import unittest
from pathlib import Path


class TestCandidateBoundary(unittest.TestCase):

    def test_candidate_package_has_no_trading_logic(self):
        package = Path(
            "app/intelligence/candidates"
        )

        forbidden = {
            "BUY",
            "SELL",
            "LONG",
            "SHORT",
            "ENTRY",
            "TARGET",
            "STOP",
        }

        for path in package.rglob("*.py"):
            content = path.read_text(
                encoding="utf-8"
            )

            for word in forbidden:
                self.assertNotIn(
                    word,
                    content.upper(),
                    msg=f"{word} found in {path}",
                )

    def test_candidate_package_imports_are_safe(self):
        package = Path(
            "app/intelligence/candidates"
        )

        forbidden = {
            "requests",
            "aiohttp",
            "ccxt",
            "sqlite3",
            "telegram",
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
                        x.name for x in node.names
                    ]
                elif isinstance(node, ast.ImportFrom):
                    modules = [
                        node.module or ""
                    ]
                else:
                    continue

                for module in modules:
                    for item in forbidden:
                        self.assertNotIn(
                            item,
                            module,
                            msg=f"{item} found in {path}",
                        )


if __name__ == "__main__":
    unittest.main()
