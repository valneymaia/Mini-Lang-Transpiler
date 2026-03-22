from ast_nodes import *
from symtable import SymTable, Symbol

class SemanticAnalyzer:
    """
     Faz a verificação semântica da AST da Mini-Lang.
     Checa escopo, compatibilidade de tipos e regras de função.
    """
    
    def __init__(self, ast=None):
        self.ast = ast 
        self.current_scope = SymTable()
        self.errors = []
        self._analyzed = False

        # Guarda o tipo de retorno da função atual durante a visita.
        self._current_function_return_type = None


    # Adiciona erro semântico sem duplicar mensagens iguais.
    def report_erros(self, message, lineno=None): 
        msg = f"Erro Semântico: {message}"
        if msg not in self.errors:
            self.errors.append(msg)

    # Despacha para o método visit_<TipoDoNo>.
    def visit(self, node): 
        if node is None: return None
        if isinstance(node, list):
            last_type = None
            for item in node: last_type = self.visit(item)
            return last_type

        cls_name = type(node).__name__
        method_name = f'visit_{cls_name}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node):
        for attr in vars(node):
            child = getattr(node, attr)
            if isinstance(child, list):
                for item in child: self.visit(item)
            elif hasattr(child, '__class__'): 
                self.visit(child)
        return None
    
    # Percorre os nós do programa no escopo global.
    def visit_ProgramNode(self, node):
        return self.visit(node.statements)

    def visit_BlockNode(self, node):
        return self.visit(node.statements)
    """Valida declaração de variável e o tipo da expressão atribuída."""
    def visit_VarDeclNode(self, node):
        var_name = node.id_node.name
        var_type = getattr(node.type_node, 'type_name', 'unknown')
        
        if not self.current_scope.insert(var_name, Symbol(var_name, var_type)):
            self.report_erros(f"A variável '{var_name}' já foi declarada.")
        
        expr = getattr(node, 'expr_node', getattr(node, 'value', None))
        if expr:
            assigned_type = self.visit(expr)
            if assigned_type and var_type != assigned_type and assigned_type != 'unknown':
                self.report_erros(f"Tipo incompatível na declaração: '{var_name}' é {var_type} mas recebeu {assigned_type}")
        
        return var_type

    def visit_AssignmentNode(self, node):
        var_name = node.id_node.name
        symbol = self.current_scope.find(var_name)
        
        if symbol is None:
            self.report_erros(f"Variável '{var_name}' não declarada antes da atribuição.")
            return 'unknown'
        
        target_type = symbol.type
        expr = getattr(node, 'expr_node', getattr(node, 'value', None))
        value_type = self.visit(expr)

        if value_type and target_type != value_type and value_type != 'unknown':
            self.report_erros(f"Não é possível atribuir '{value_type}' à variável '{var_name}' do tipo '{target_type}'.")
        
        return target_type
    # Procura o identificador na tabela de símbolos.
    def visit_IdentifierNode(self, node):
        symbol = self.current_scope.find(node.name)
        if symbol is None:
            self.report_erros(f"Variável '{node.name}' não declarada.")
            return 'unknown'
        return symbol.type 

    def visit_BinaryOpNode(self, node):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        if 'unknown' in [left_type, right_type]:
            return 'unknown'

        op = node.operator.name if hasattr(node.operator, 'name') else str(node.operator)

        def is_numeric(t):
            return t in ('int', 'real')

        # Operadores aritméticos.
        if op in ('+', '-', '*', '/'):
            if not (is_numeric(left_type) and is_numeric(right_type)):
                self.report_erros(f"Operação aritmética inválida entre tipos {left_type} e {right_type}")
                return 'unknown'
            return 'real' if 'real' in (left_type, right_type) else 'int'

        # Operadores lógicos.
        if op in ('AND', 'OR'):
            if left_type != 'bool' or right_type != 'bool':
                self.report_erros(f"Operação lógica inválida entre tipos {left_type} e {right_type}")
                return 'unknown'
            return 'bool'

        # Operadores de igualdade.
        if op in ('EQ', 'NEQ', '==', '!='):
            same_type = left_type == right_type
            numeric_mix = is_numeric(left_type) and is_numeric(right_type)
            if not (same_type or numeric_mix):
                self.report_erros(f"Comparação inválida entre tipos {left_type} e {right_type}")
                return 'unknown'
            return 'bool'

        # Operadores relacionais.
        if op in ('<', '>', 'GTE', 'LTE', '<=', '>='):
            if not (is_numeric(left_type) and is_numeric(right_type)):
                self.report_erros(f"Comparação relacional inválida entre tipos {left_type} e {right_type}")
                return 'unknown'
            return 'bool'

        # Caso apareça operador fora dos grupos acima.
        if left_type != right_type:
            self.report_erros(f"Operação inválida entre tipos {left_type} e {right_type}")
            return 'unknown'

        return left_type

    def visit_UnaryOpNode(self, node):
        operand_type = self.visit(node.expression)

        if operand_type == 'unknown':
            return 'unknown'

        op = node.operator.name if hasattr(node.operator, 'name') else str(node.operator)

        # not só faz sentido para bool.
        if op in ('NOT', 'not'):
            if operand_type != 'bool':
                self.report_erros(f"Operação lógica unária inválida para tipo {operand_type}")
                return 'unknown'
            return 'bool'

        # + e - unários só fazem sentido para números.
        if op in ('+', '-'):
            if operand_type not in ('int', 'real'):
                self.report_erros(f"Operação aritmética unária inválida para tipo {operand_type}")
                return 'unknown'
            return operand_type

        self.report_erros(f"Operador unário inválido: {op}")
        return 'unknown'

    def visit_FunctionDeclNode(self, node):
        """
        Registra função no escopo global, valida parâmetros
        e analisa o corpo em escopo próprio.
        """
        func_name = node.id_node.name
        ret_type = getattr(node.return_type_node, 'type_name', 'void')
        num_params = len(node.parameters)
        
        # Impede duas funções com o mesmo nome no mesmo escopo.
        if not self.current_scope.insert(func_name, Symbol(func_name, ret_type, arity=num_params)):
            self.report_erros(f"A função '{func_name}' já foi declarada.")

        # Valida duplicação de parâmetros na assinatura.
        param_names = set()
        for param in node.parameters:
            p_name = param.id_node.name
            if p_name in param_names:
                self.report_erros(f"Parâmetro duplicado '{p_name}' na função '{func_name}'.")
            param_names.add(p_name)

        # Abre escopo local da função.
        old_scope = self.current_scope
        self.current_scope = SymTable(prev=old_scope)
        
        # Salva o tipo de retorno esperado para validar os returns.
        old_return_type = self._current_function_return_type
        self._current_function_return_type = ret_type

        # Registra os parâmetros no escopo local.
        for param in node.parameters:
            p_name = param.id_node.name
            p_type = getattr(param.type_node, 'type_name', 'int')
            self.current_scope.insert(p_name, Symbol(p_name, p_type))

        # Analisa o corpo da função.
        self.visit(node.body_node)
        
        # Fecha escopo local.
        self.current_scope = old_scope
        
        # Restaura contexto de retorno anterior.
        self._current_function_return_type = old_return_type
        
        return ret_type
    
    # Verifica chamada de função e aridade.
    def visit_FunctionCallNode(self, node):
        func_name = node.id_node.name
        symbol = self.current_scope.find(func_name)

        if symbol is None:
            self.report_erros(f"Função '{func_name}' não declarada.")
            return 'unknown'

        args_enviados = getattr(node, 'args', [])
        if symbol.arity is not None and len(args_enviados) != symbol.arity:
            self.report_erros(f"Chamada incorreta: '{func_name}' espera {symbol.arity} argumento(s), mas recebeu {len(args_enviados)}.")

        for arg in args_enviados:
            self.visit(arg)

        return symbol.type

    def visit_LiteralNode(self, node):
        t = str(node.tag).upper()
        if "INTEGER" in t: return "int"
        if "REAL" in t: return "real"
        if "BOOL" in t or "TRUE" in t or "FALSE" in t: return "bool"
        return "unknown"

    def visit_StringLiteralNode(self, node):
        return 'string'

    def visit_ReturnNode(self, node):
        """Valida se o tipo retornado bate com o tipo da função atual."""
        return_expr_type = self.visit(node.expression)
        
        # Se estamos dentro de uma função, confere o tipo do retorno.
        if self._current_function_return_type is not None:
            expected_type = self._current_function_return_type
            
            # Ignora unknown para não poluir com erros em cascata.
            if (return_expr_type and 
                expected_type != return_expr_type and 
                return_expr_type != 'unknown'):
                self.report_erros(
                    f"Tipo de retorno incompatível: "
                    f"esperado '{expected_type}', "
                    f"mas encontrou '{return_expr_type}'."
                )
        
        return return_expr_type
    
     
    """Executa a análise semântica e devolve True se não houver erros."""
    def analyze(self):
        if self._analyzed:
            return len(self.errors) == 0

        if not self.ast:
            self._analyzed = True
            return False

        self.visit(self.ast)
        self._analyzed = True
        return len(self.errors) == 0

    def cont_erros(self):
        ok = self.analyze()

        if not self.ast:
            print("Erro Semântico: AST vazia ou inválida.")
            return

        if not ok:
            print(f"Foram encontrados {len(self.errors)} erros semanticos:")
            for idx, err in enumerate(self.errors, 1):
                print(f"{idx}. {err}")
        else:
            print("\nAnálise semântica concluída com sucesso. (0 erros)")
    
