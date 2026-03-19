from abc import ABC, abstractmethod

class ASTNode(ABC):
    """Classe base para todos os nós da Árvore Sintática Abstrata."""
    @abstractmethod
    def to_dict(self):
        pass

# --- Nós de Estrutura de Alto Nível ---

class ProgramNode(ASTNode):
    def __init__(self, statements):
        self.statements = statements

    def to_dict(self):
        return {"Program": [s.to_dict() for s in self.statements]}

class BlockNode(ASTNode):
    def __init__(self, statements):
        self.statements = statements

    def to_dict(self):
        return {"Block": [s.to_dict() for s in self.statements]}

# --- Nós de Declaração e Atribuição ---

class VarDeclNode(ASTNode):
    def __init__(self, id_node, type_node, expr_node):
        self.id_node = id_node
        self.type_node = type_node
        self.expr_node = expr_node

    def to_dict(self):
        return {
            "VariableDeclaration": {
                "id": self.id_node.to_dict(),
                "type": self.type_node.to_dict(),
                "value": self.expr_node.to_dict()
            }
        }

class AssignmentNode(ASTNode):
    def __init__(self, id_node, expr_node):
        self.id_node = id_node
        self.expr_node = expr_node

    def to_dict(self):
        return {
            "Assignment": {
                "id": self.id_node.to_dict(),
                "value": self.expr_node.to_dict()
            }
        }

# --- Nós de Função ---

class FunctionDeclNode(ASTNode):
    def __init__(self, id_node, parameters, return_type_node, body_node):
        self.id_node = id_node
        self.parameters = parameters
        self.return_type_node = return_type_node
        self.body_node = body_node

    def to_dict(self):
        return {
            "FunctionDeclaration": {
                "name": self.id_node.to_dict(),
                "params": [p.to_dict() for p in self.parameters],
                "return_type": self.return_type_node.to_dict(),
                "body": self.body_node.to_dict()
            }
        }

class FormalParamNode(ASTNode):
    def __init__(self, id_node, type_node):
        self.id_node = id_node
        self.type_node = type_node

    def to_dict(self):
        return {"Param": {"id": self.id_node.to_dict(), "type": self.type_node.to_dict()}}

class FunctionCallNode(ASTNode):
    def __init__(self, id_node, args):
        self.id_node = id_node
        self.args = args

    def to_dict(self):
        return {
            "FunctionCall": {
                "name": self.id_node.to_dict(),
                "arguments": [a.to_dict() for a in self.args]
            }
        }

# --- Nós de Controle de Fluxo ---

class IfNode(ASTNode):
    def __init__(self, condition, then_block, else_block=None):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block

    def to_dict(self):
        return {
            "IfStatement": {
                "condition": self.condition.to_dict(),
                "then": self.then_block.to_dict(),
                "else": self.else_block.to_dict() if self.else_block else None
            }
        }

class WhileNode(ASTNode):
    def __init__(self, condition, block):
        self.condition = condition
        self.block = block

    def to_dict(self):
        return {
            "WhileStatement": {
                "condition": self.condition.to_dict(),
                "body": self.block.to_dict()
            }
        }

class ReturnNode(ASTNode):
    def __init__(self, expression):
        self.expression = expression

    def to_dict(self):
        return {"ReturnStatement": self.expression.to_dict()}

class PrintNode(ASTNode):
    def __init__(self, string_node):
        self.string_node = string_node

    def to_dict(self):
        return {"PrintStatement": self.string_node.to_dict()}

# --- Nós de Expressão e Operações ---

class BinaryOpNode(ASTNode):
    def __init__(self, operator, left, right):
        self.operator = operator
        self.left = left
        self.right = right

    def to_dict(self):
        # Converte operadores do tipo Enum ou caractere simples para string
        op_str = self.operator.name if hasattr(self.operator, 'name') else str(self.operator)
        return {
            "BinaryOp": {
                "left": self.left.to_dict(),
                "operator": op_str,
                "right": self.right.to_dict()
            }
        }

class UnaryOpNode(ASTNode):
    def __init__(self, operator, expression):
        self.operator = operator
        self.expression = expression

    def to_dict(self):
        op_str = self.operator.name if hasattr(self.operator, 'name') else str(self.operator)
        return {"UnaryOp": {"operator": op_str, "expression": self.expression.to_dict()}}

# --- Nós Terminais (Folhas) ---

class IdentifierNode(ASTNode):
    def __init__(self, name):
        self.name = name

    def to_dict(self):
        return {"Identifier": self.name}

class LiteralNode(ASTNode):
    def __init__(self, value, tag):
        self.value = value
        self.tag = tag

    def to_dict(self):
        tag_name = self.tag.name if hasattr(self.tag, 'name') else str(self.tag)
        return {"Literal": {"value": self.value, "type": tag_name}}

class StringLiteralNode(ASTNode):
    def __init__(self, value):
        self.value = value

    def to_dict(self):
        return {"StringLiteral": self.value}

class TypeNode(ASTNode):
    def __init__(self, type_name):
        self.type_name = type_name

    def to_dict(self):
        return {"Type": self.type_name}