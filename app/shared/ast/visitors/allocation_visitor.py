import ast


class AllocationVisitors(ast.NodeVisitor):
    def __init__(self):
        self.total_allocations = 0

        self.list_allocations = 0
        self.dict_allocations = 0
        self.set_allocations = 0
        self.tuple_allocations = 0

        self.list_comprehensions = 0
        self.dict_comprehensions = 0
        self.set_comprehensions = 0

        self.generator_expressions = 0

    # -------------------------
    # BASIC STRUCTURES
    # -------------------------

    def visit_List(self, node):
        """Visit declared lists in the algorithm"""
        self.list_allocations += 1
        self.total_allocations += 1
        self.generic_visit(node)

    def visit_Dict(self, node):
        """Visit declared dictionaries in the algorithm"""
        self.dict_allocations += 1
        self.total_allocations += 1
        self.generic_visit(node)

    def visit_Set(self, node):
        """Visit declared sets in the algorithm"""
        self.set_allocations += 1
        self.total_allocations += 1
        self.generic_visit(node)

    def visit_Tuple(self, node):
        """Visit declared tuples in the algorithm"""
        self.tuple_allocations += 1
        self.total_allocations += 1
        self.generic_visit(node)

    # -------------------------
    # COMPREHENSIONS
    # -------------------------

    def visit_ListComp(self, node):
        """Visit list comprehensions in the algorithm"""
        self.list_comprehensions += 1
        self.total_allocations += 1
        self.generic_visit(node)

    def visit_DictComp(self, node):
        """Visit dictionary comprehensions in the algorithm"""
        self.dict_comprehensions += 1
        self.total_allocations += 1
        self.generic_visit(node)

    def visit_SetComp(self, node):
        """Visit set comprehensions in the algorithm"""
        self.set_comprehensions += 1
        self.total_allocations += 1
        self.generic_visit(node)

    # -------------------------
    # GENERATORS
    # -------------------------

    def visit_GeneratorExp(self, node):
        """Visit generators in the algorithm"""
        self.generator_expressions += 1
        self.generic_visit(node)
