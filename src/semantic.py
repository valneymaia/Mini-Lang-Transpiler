from parser import Parser
from ast_nodes import *
from symtable import SymTable, Symbol


class SemanticAnalyzer:
    def __init__(self, ast):
        self.ast = ast
        self.global_scope = SymTable()  # Tabela de símbolos para o escopo global
        self.current_scope = self.global_scope  # Escopo atual, começa no global

    def visit(self, node):
        