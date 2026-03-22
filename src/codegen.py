from ast_nodes import *

class CCodeGenerator:
    """
    Gera código C a partir da AST da Mini-Lang.

    A geração separa declarações globais de comandos executáveis.
    Comandos globais são movidos para dentro da main para manter
    o C final válido.
    """
    
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
        """
        Converte tipos da Mini-Lang para tipos em C.
        Tipos fora do mapa caem em int por padrão.
        """
        type_map = {
            "int": "int",
            "real": "float",
            "bool": "int",
            "string": "char*"
        }
        return type_map.get(type_name, "int")
    
    def generate(self, ast_node):
        """
          Gera o código C completo do programa.
          Primeiro classifica os nós e depois emite em etapas:
          forward declarations, variáveis globais, funções e main.
        """
        self.code = []
        self.indent_level = 0
        
        self.emit("#include <stdio.h>")
        self.emit("#include <stdlib.h>")
        self.emit("#include <stdbool.h>")
        self.emit("")
        
        if isinstance(ast_node, ProgramNode):
            # 1) Classificação dos statements do programa.
            var_declarations = []
            function_declarations = []
            executables = []
            main_function = None
            
            for stmt in ast_node.statements:
                if isinstance(stmt, FunctionDeclNode):
                    self.collect_function(stmt)

                    if stmt.id_node.name == "main":
                        main_function = stmt
                    else:
                        function_declarations.append(stmt)
                        
                elif isinstance(stmt, VarDeclNode):
                    var_declarations.append(stmt)
                    
                else:
                    executables.append(stmt)

            # 2) Forward declarations.
            
            for func_name, (params, return_type) in self.functions.items():
                param_decls = ", ".join(
                    f"{self.get_c_type(p.type_node.type_name)} {p.id_node.name}"
                    for p in params
                ) if params else "void"
                self.emit(f"{self.get_c_type(return_type)} {func_name}({param_decls});")
            
            if self.functions:
                self.emit("")
            
            # 3) Variáveis globais.
            
            for stmt in var_declarations:
                self.generate_var_decl(stmt)
                self.emit("")
            
            # 4) Funções (exceto main).
            
            for stmt in function_declarations:
                self.generate_function(stmt)
                self.emit("")
            
            # 5) Main: usa a do usuário ou cria uma.
            
            if executables or "main" not in self.functions:
                if main_function:
                    self._generate_main_with_executables(main_function, executables)
                else:
                    self.emit("int main() {")
                    self.indent()
                    for stmt in executables:
                        self.generate_statement(stmt)
                    self.emit("return 0;")
                    self.dedent()
                    self.emit("}")
            else:
                self.generate_function(main_function)
        
        return "\n".join(self.code)
    
    def collect_function(self, node):
        """Coleta informações de funções para forward declarations."""
        if isinstance(node, FunctionDeclNode):
            func_name = node.id_node.name
            return_type = node.return_type_node.type_name
            self.functions[func_name] = (node.parameters, return_type)
    
    def _generate_main_with_executables(self, main_node, executables):
        """
        Monta a main usando primeiro os comandos globais executáveis
        e depois o corpo original da função main do usuário.
        """
        return_type = self.get_c_type(main_node.return_type_node.type_name)
        func_name = main_node.id_node.name
        
        params = []
        for param in main_node.parameters:
            param_type = self.get_c_type(param.type_node.type_name)
            param_name = param.id_node.name
            params.append(f"{param_type} {param_name}")
        
        param_str = ", ".join(params) if params else "void"

        self.emit(f"{return_type} {func_name}({param_str}) {{")
        self.indent()

        # Comandos globais primeiro.
        for stmt in executables:
            self.generate_statement(stmt)

        # Depois vem o corpo da main original.
        if isinstance(main_node.body_node, BlockNode):
            for stmt in main_node.body_node.statements:
                self.generate_statement(stmt)
        else:
            self.generate_statement(main_node.body_node)

        self.dedent()
        self.emit("}")
    
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
            # Escapa aspas para manter string válida em C.
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
            if expr.tag.name in ("BOOL", "TRUE", "FALSE"):
                # Em C, bool literal vira 1/0.
                return "1" if str(expr.value).lower() == "true" else "0"
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
