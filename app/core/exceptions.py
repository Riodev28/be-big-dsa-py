class ParseTreeError(Exception):
    """Throws when: try to parse code to tree node using AST"""

    pass


class NormalizeCodeError(Exception):
    """Throws when: fail to normalize code"""

    pass


class CodeNotNormalizedError(Exception):
    """Throws when: code was not normalized before run another method"""

    pass


class FailedDatabaseConnection(Exception):
    """Throws when: failed to connect to database"""
