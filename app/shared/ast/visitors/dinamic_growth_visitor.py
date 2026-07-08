import ast


class DynamicGrowthVisitor(ast.NodeVisitor):
    def __init__(self):
        self.append_calls = 0
        self.dict_updates = 0

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "append":
                self.append_calls += 1

        self.generic_visit(node)
