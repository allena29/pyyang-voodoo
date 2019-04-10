
class NodeHasNoValue(Exception):

    """
    Raised when accessing a non-presence container, list, or anything which does not
    have a value.
    A decendent node is could be fetched.
    """

    def __init__(self, nodetype, xpath):
        super().__init__("The node: %s at %s has no value" % (nodetype, xpath))


class NodeNotAList(Exception):

    def __init__(self, xpath):
        super().__init__("The path: %s is not a list" % (xpath))


class ListWrongNumberOfKeys(Exception):

    def __init__(self, xpath, require, given):
        super().__init__("The path: %s is a list requiring %s keys but was given %s keys" % (xpath, require, given))


class NonExistingNode(Exception):

    def __init__(self, xpath):
        super().__init__("The path: %s does not point of a valid schema node in the yang module" % (xpath))


class CommitFailed(Exception):

    def __init__(self, message):
        super().__init__("The commit failed.\n%s" % (message))