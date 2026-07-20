import ast
import pathlib
import unittest


PACKAGE_DIR = pathlib.Path(
    "app/intelligence/decision_input_consumer"
)


class TestDecisionInputConsumerBoundary(unittest.TestCase):

    def test_package_has_no_external_dependencies(self):
        allowed_roots = {
            "__future__",
            "dataclasses",
            "datetime",
            "enum",
            "typing",
            "app",
        }

        for path in PACKAGE_DIR.glob("*.py"):
            tree = ast.parse(
                path.read_text(encoding="utf-8"),
                filename=str(path),
            )

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root = alias.name.split(".", 1)[0]

                        self.assertIn(
                            root,
                            allowed_roots,
                            msg=(
                                f"{path} imports external dependency: "
                                f"{alias.name}"
                            ),
                        )

                elif isinstance(node, ast.ImportFrom):
                    if node.level > 0 or node.module is None:
                        continue

                    root = node.module.split(".", 1)[0]

                    self.assertIn(
                        root,
                        allowed_roots,
                        msg=(
                            f"{path} imports external dependency: "
                            f"{node.module}"
                        ),
                    )

    def test_package_contains_no_decision_or_execution_logic(self):
        forbidden_identifiers = {
            "buy",
            "sell",
            "trade",
            "order",
            "execute",
            "execution",
            "recommend",
            "recommendation",
            "rank",
            "ranking",
            "score",
            "position",
            "leverage",
            "take_profit",
            "stop_loss",
            "decision_record",
            "basis_record",
        }

        for path in PACKAGE_DIR.glob("*.py"):
            tree = ast.parse(
                path.read_text(encoding="utf-8"),
                filename=str(path),
            )

            identifiers = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    identifiers.add(node.id.lower())

                elif isinstance(node, ast.Attribute):
                    identifiers.add(node.attr.lower())

                elif isinstance(
                    node,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                        ast.ClassDef,
                    ),
                ):
                    identifiers.add(node.name.lower())

            violations = sorted(
                forbidden_identifiers.intersection(identifiers)
            )

            self.assertEqual(
                violations,
                [],
                msg=(
                    f"{path} contains forbidden boundary "
                    f"identifiers: {violations}"
                ),
            )


if __name__ == "__main__":
    unittest.main()
