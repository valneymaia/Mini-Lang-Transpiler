from ast_nodes import *

class CCodeGenerator:
    """Gerador de código C a partir da AST."""
    
    def __init__(self):
        self.code = []
        self.indent_level = 0
        self.functions = {}
        self.globals = {}
    
    def indent(self):
        """Aumenta o nível de indentação."""
        self.indent_level += 1
    
    def dedent(self):
        """Diminui o nível de indentação."""
        self.indent_level -= 1
    
    def emit(self, line):
        """Emite uma linha de código com indentação apropriada."""
        if line.strip():  
            self.code.append("    " * self.indent_level + line)
        else:
            self.code.append("")
    
    def get_c_type(self, type_name):
        """Converte tipos Mini-Lang para tipos C."""
        type_map = {
            "int": "int",
            "bool": "int",
            "float": "float",
            "string": "char*"
        }
        return type_map.get(type_name, "int")
    
    def generate(self, ast_node):
        """Gera código C a partir da AST."""
        self.code = []
        self.indent_level = 0
        
        self.emit("#include <stdio.h>")
        self.emit("#include <stdlib.h>")
        self.emit("#include <stdbool.h>")
        self.emit("")
        
        if isinstance(ast_node, ProgramNode):
            # Primeira passagem: coleta declarações de função (para forward declarations)
            for stmt in ast_node.statements:
                if isinstance(stmt, FunctionDeclNode):
                    self.collect_function(stmt)
            
            # Emite forward declarations
            for func_name, (params, return_type) in self.functions.items():
                param_decls = ", ".join(
                    f"{self.get_c_type(p.type_node.type_name)} {p.id_node.name}"
                    for p in params
                ) if params else "void"
                self.emit(f"{self.get_c_type(return_type)} {func_name}({param_decls});")
            
            if self.functions:
                self.emit("")
            
            # Segunda passagem: gera código completo
            for stmt in ast_node.statements:
                self.generate_statement(stmt)
                self.emit("")
            
            # Função main se não existir
            if "main" not in self.functions:
                self.emit("int main() {")
                self.indent()
                self.emit("return 0;")
                self.dedent()
                self.emit("}")
        
        return "\n".join(self.code)
    
    def collect_function(self, node):
        """Coleta informações de funções para forward declarations."""
        if isinstance(node, FunctionDeclNode):
            func_name = node.id_node.name
            return_type = node.return_type_node.type_name
            self.functions[func_name] = (node.parameters, return_type)
    
    def generate_statement(self, stmt):
        """Gera código para um statement."""
        if isinstance(stmt, VarDeclNode):
            self.generate_var_decl(stmt)
        elif isinstance(stmt, AssignmentNode):
            self.generate_assignment(stmt)
        elif isinstance(stmt, FunctionDeclNode):
            self.generate_function(stmt)
        elif isinstance(stmt, IfNode):
            self.generate_if(stmt)
        elif isinstance(stmt, WhileNode):
            self.generate_while(stmt)
        elif isinstance(stmt, ReturnNode):
            self.generate_return(stmt)
        elif isinstance(stmt, PrintNode):
            self.generate_print(stmt)
        elif isinstance(stmt, BlockNode):
            self.generate_block(stmt)
        elif isinstance(stmt, FunctionCallNode):
            expr = self.generate_expression(stmt)
            self.emit(f"{expr};")
    
    def generate_var_decl(self, node):
        """Gera declaração de variável."""
        type_name = self.get_c_type(node.type_node.type_name)
        var_name = node.id_node.name
        value = self.generate_expression(node.expr_node)
        self.emit(f"{type_name} {var_name} = {value};")
    
    def generate_assignment(self, node):
        """Gera atribuição de variável."""
        var_name = node.id_node.name
        value = self.generate_expression(node.expr_node)
        self.emit(f"{var_name} = {value};")
    
    def generate_function(self, node):
        """Gera definição de função."""
        func_name = node.id_node.name
        return_type = self.get_c_type(node.return_type_node.type_name)
        
        
        params = []
        for param in node.parameters:
            param_type = self.get_c_type(param.type_node.type_name)
            param_name = param.id_node.name
            params.append(f"{param_type} {param_name}")
        
        param_str = ", ".join(params) if params else "void"
        
        self.emit(f"{return_type} {func_name}({param_str}) {{")
        self.indent()
        
        
        if isinstance(node.body_node, BlockNode):
            for stmt in node.body_node.statements:
                self.generate_statement(stmt)
        else:
            self.generate_statement(node.body_node)
        
        self.dedent()
        self.emit("}")
    
    def generate_if(self, node):
        """Gera condicional if."""
        condition = self.generate_expression(node.condition)
        self.emit(f"if ({condition}) {{")
        self.indent()
        
        if isinstance(node.then_block, BlockNode):
            for stmt in node.then_block.statements:
                self.generate_statement(stmt)
        else:
            self.generate_statement(node.then_block)
        
        self.dedent()
        
        if node.else_block:
            self.emit("} else {")
            self.indent()
            
            if isinstance(node.else_block, BlockNode):
                for stmt in node.else_block.statements:
                    self.generate_statement(stmt)
            else:
                self.generate_statement(node.else_block)
            
            self.dedent()
            self.emit("}")
        else:
            self.emit("}")
    
    def generate_while(self, node):
        """Gera loop while."""
        condition = self.generate_expression(node.condition)
        self.emit(f"while ({condition}) {{")
        self.indent()
        
        if isinstance(node.block, BlockNode):
            for stmt in node.block.statements:
                self.generate_statement(stmt)
        else:
            self.generate_statement(node.block)
        
        self.dedent()
        self.emit("}")
    
    def generate_return(self, node):
        """Gera return."""
        expr = self.generate_expression(node.expression)
        self.emit(f"return {expr};")
    
    def generate_print(self, node):
        """Gera print (usa printf em C)."""
        if isinstance(node.string_node, StringLiteralNode):
            string_val = node.string_node.value
            # Escapa caracteres especiais para C
            string_val = string_val.replace('"', '\\"')
            self.emit(f'printf("%s\\n", "{string_val}");')
        else:
            expr = self.generate_expression(node.string_node)
            self.emit(f'printf("%d\\n", {expr});')
    
    def generate_block(self, node):
        """Gera bloco de código."""
        for stmt in node.statements:
            self.generate_statement(stmt)
    
    def generate_expression(self, expr):
        """Gera expressão."""
        if isinstance(expr, LiteralNode):
            if expr.tag.name == "BOOL":
                # Mini-Lang usa true/false, C usa 1/0
                return "1" if expr.value == "true" else "0"
            return str(expr.value)
        
        elif isinstance(expr, StringLiteralNode):
            return f'"{expr.value}"'
        
        elif isinstance(expr, IdentifierNode):
            return expr.name
        
        elif isinstance(expr, BinaryOpNode):
            left = self.generate_expression(expr.left)
            right = self.generate_expression(expr.right)
            op = self.get_c_operator(expr.operator)
            return f"({left} {op} {right})"
        
        elif isinstance(expr, UnaryOpNode):
            operand = self.generate_expression(expr.expression)
            op = self.get_c_operator(expr.operator)
            return f"({op}{operand})"
        
        elif isinstance(expr, FunctionCallNode):
            func_name = expr.id_node.name
            args = [self.generate_expression(arg) for arg in expr.args]
            args_str = ", ".join(args) if args else ""
            return f"{func_name}({args_str})"
        
        return "0"
    
    def get_c_operator(self, operator):
        """Converte operador Mini-Lang para C."""
        if hasattr(operator, 'name'):
            op_name = operator.name
        else:
            op_name = str(operator)
        
        op_map = {
            "PLUS": "+",
            "MINUS": "-",
            "MULT": "*",
            "DIV": "/",
            "MOD": "%",
            "EQ": "==",
            "NEQ": "!=",
            "LT": "<",
            "LTE": "<=",
            "GT": ">",
            "GTE": ">=",
            "AND": "&&",
            "OR": "||",
            "NOT": "!",
            "+": "+",
            "-": "-",
            "*": "*",
            "/": "/",
            "%": "%",
            "==": "==",
            "!=": "!=",
            "<": "<",
            "<=": "<=",
            ">": ">",
            ">=": ">=",
            "&&": "&&",
            "||": "||",
            "!": "!"
        }
        
        return op_map.get(op_name, op_name)
