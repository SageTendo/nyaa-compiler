import json
from typing import Optional

from src.core.CacheMemory import cache_mem
from src.core.Token import Token


class Node:
    def __init__(self, node_label: str):
        self.label = node_label
        self.start_pos: tuple = (-1, -1)
        self.end_pos: tuple = (-1, -1)

    def accept(self, visitor):
        """Invokes visitor method on node"""
        if cached_visit := cache_mem.get(self):
            return cached_visit(self)
        return visitor.visit(self)

    def to_json(self) -> dict:
        """Represent AST/Node as dictionary"""
        node_map = self.__dict__.copy()
        node_map["start_pos"] = self.start_pos
        node_map["end_pos"] = self.end_pos

        for k, v in node_map.items():
            if v is None:
                continue

            node_map[k] = "true" if v is True else "false"

            if isinstance(v, list):
                node_map[k] = [item.to_json() for item in v]

            if isinstance(v, dict):
                node_map[k] = {}
                for key, value in v.items():
                    if value:
                        node_map[k][key] = value.to_json()

            if isinstance(v, Node):
                node_map[k] = v.to_json()
        return node_map

    def encode_json(self) -> str:
        return json.dumps(self.to_json(), indent=2)


class ConditionalNode(Node):
    def __init__(self, expr, body=None, label="Conditional"):
        super().__init__(label)
        self.expr = expr
        self.body = body


class ProgramNode(Node):
    def __init__(self):
        super().__init__("program")

        self.functions = []
        self.body: Optional[BodyNode] = None
        self.eof = False

    def set_eof(self):
        self.eof = True

    def append_func(self, func: "FuncDefNode"):
        self.functions.append(func)

    def set_body(self, body: "BodyNode"):
        self.body = body


class FuncDefNode(Node):
    def __init__(self, identifier: str, args: Optional["ArgsNode"], body: "BodyNode"):
        super().__init__("func_def")
        self.identifier = identifier
        self.args = args
        self.body = body


class BodyNode(Node):
    def __init__(self):
        super().__init__("body")
        self.statements = []

    def append(self, statement: Node):
        self.statements.append(statement)


class BreakNode(Node):
    def __init__(self):
        super().__init__("break")


class ContinueNode(Node):
    def __init__(self):
        super().__init__("continue")


class ReturnNode(Node):
    def __init__(self):
        super().__init__("return")
        self.expr = None

    def set_expr(self, expr: "ExprNode"):
        self.expr = expr


class ArgsNode(Node):
    def __init__(self):
        super().__init__("args")
        self.children = []

    def append(self, argument: "ExprNode"):
        self.children.append(argument)


class WhileNode(ConditionalNode):
    def __init__(self, expr, body):
        super().__init__(expr, body, "while")


class ForNode(Node):
    def __init__(self, identifier, range_start, range_end, body):
        super().__init__("for")
        self.identifier = identifier
        self.range_start = range_start
        self.range_end = range_end
        self.body = body


class IfNode(ConditionalNode):
    def __init__(self, expr, body):
        super().__init__(expr, body, "if")
        self.else_if_statements = []
        self.else_body = None

    def append_else_if(self, statement):
        self.else_if_statements.append(statement)

    def set_else_body(self, body):
        self.else_body = body


class ElifNode(ConditionalNode):
    def __init__(self, expr, body):
        super().__init__(expr, body, "elif")


class ElseNode(ConditionalNode):
    def __init__(self, body):
        super().__init__(None, body, "else")


class AssignmentNode(Node):
    def __init__(self, left, right):
        super().__init__("assignment")
        self.left = left
        self.right = right


class ExprNode(Node):
    def __init__(self, label: str = "expr"):
        super().__init__(label)

        self._left = None
        self._right = None
        self._operator = None

    @property
    def left(self):
        return self._left

    @left.setter
    def left(self, value):
        self._left = value

    @property
    def right(self):
        return self._right

    @right.setter
    def right(self, value):
        self._right = value

    @property
    def operator(self):
        return self._operator

    @operator.setter
    def operator(self, value):
        self._operator = value


class CallNode(ExprNode):
    def __init__(self, identifier, args):
        super().__init__("call")
        self.identifier = identifier
        self.args = args


class InputNode(ExprNode):
    def __init__(self, msg=None):
        super().__init__("input")
        self.message = msg if msg else ""


class PrintNode(ExprNode):
    def __init__(self, args, print_ln=False):
        super().__init__("print")
        self.args = args
        self.println = print_ln


class PostfixExprNode(ExprNode):
    def __init__(self, left: ExprNode, op=None):
        super().__init__("postfix_expr")
        self.left = left
        self.operator = op


class SimpleExprNode(ExprNode):
    def __init__(self, left: ExprNode, right: ExprNode, op=None):
        super().__init__("simple_expr")
        self.left = left
        self.right = right
        self.operator = op


class TermNode(ExprNode):
    def __init__(self, left, right=None, op=None):
        super().__init__("term")
        self.left = left
        self.right = right
        self.operator = op


class FactorNode(ExprNode):
    def __init__(self, left, right=None):
        super().__init__("factor")
        self.left = left
        self.right = right


class ArrayNode(Node):
    def __init__(
        self,
        label: str,
        identifier: str,
        index: Optional[ExprNode] = None,
        size: Optional[ExprNode] = None,
        value: Optional[ExprNode] = None,
        initial_values: Optional[list[ExprNode]] = None,
    ):
        super().__init__(label)
        self.identifier = identifier
        self.index = index
        self.size = size
        self.value = value
        self.initial_values = initial_values


class IdentifierNode(ExprNode):
    def __init__(self, token):
        super().__init__("identifier")
        self.value = token.word


class NumericLiteralNode(ExprNode):
    def __init__(self, token: Token):
        super().__init__("numeric_literal")

        self.type = token.type
        self.value = token.number

    def to_json(self):
        return {"type": str(self.type), "value": str(self.value)}


class StringLiteralNode(ExprNode):
    def __init__(self, token):
        super().__init__("string_literal")
        self.value = token.word


class BooleanNode(ExprNode):
    def __init__(self, boolean_value):
        super().__init__("boolean_literal")
        self.value = boolean_value

    def to_json(self):
        return {"value": str(self.value)}


class OperatorNode(Node):
    def __init__(self, value):
        super().__init__("operator")
        self.value = value
