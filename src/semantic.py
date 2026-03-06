from ast_nodes import *
from symtable import SymTable, Symbol

class SemanticAnalyzer:
    def __init__(self, ast=None):
        #Inicializa o analisador com a AST, cria a tabela de símbolos global e a lista de erros.
        self.ast = ast 
        self.current_scope = SymTable() # Escopo Global  
        self.errors = [] #Lista de erros para inserir todos os erros semnaticos encintrados pelo analisador semnatico 


    #Função para registra mensagens de erro
    def report_erros(self, message, lineno=None): 
        msg = f"Erro Semântico: {message}"
        if msg not in self.errors:
            self.errors.append(msg)

    #Direciona cada nó da AST para sua respectiva função de visita
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
    
    #Inicia a análise percorrendo todos os statements globais do programa.
    def visit_ProgramNode(self, node):
        return self.visit(node.statements)

    def visit_BlockNode(self, node):
        return self.visit(node.statements)
    """
    Valida a declaração de variáveis
    Essa dunção impede que redeclarações sejam realizadas e chega a compatilidade dos tpos
    """
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
    #Verifica se o identificador existe na tabela de símbolos e retorna seu tipo
    def visit_IdentifierNode(self, node):
        symbol = self.current_scope.find(node.name)
        if symbol is None:
            self.report_erros(f"Variável '{node.name}' não declarada.")
            return 'unknown'
        return symbol.type 

    def visit_BinaryOpNode(self, node):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        
        # Regra: Impedir operações entre tipos diferentes 
        if left_type != right_type and 'unknown' not in [left_type, right_type]:
            self.report_erros(f"Operação inválida entre tipos {left_type} e {right_type}")
            return 'unknown'
        
        return left_type

    def visit_FunctionDeclNode(self, node):
        # Armazenamos o tipo de retorno no Símbolo da função para uso futuro
        ret_type = getattr(node.return_type_node, 'type_name', 'int')
        self.current_scope.insert(node.id_node.name, Symbol(node.id_node.name, ret_type))

        old_scope = self.current_scope
        self.current_scope = SymTable(prev=old_scope)
        
        for param in node.parameters:
            p_node = param.Param if hasattr(param, 'Param') else param
            p_name = p_node.id_node.name
            p_type = getattr(p_node.type_node, 'type_name', 'int')
            self.current_scope.insert(p_name, Symbol(p_name, p_type))
        
        self.visit(node.body_node)
        self.current_scope = old_scope
        return ret_type
    
    #Verifica se a função chamada existe e visita seus argumentos
    def visit_FunctionCallNode(self, node):
        symbol = self.current_scope.find(node.id_node.name)
        if symbol is None:
            self.report_erros(f"Função '{node.id_node.name}' não declarada.")
            return 'unknown'
        
        # Visita os argumentos 
        self.visit(getattr(node, 'arguments', []))
    
        # RETORNA o tipo que estava salvo na tabela 
        return symbol.type

    def visit_LiteralNode(self, node):
        val = node.value
        # Se for booleano ou a string 'true'/'false'
        if isinstance(val, bool) or str(val).lower() in ['true', 'false']:
            return 'bool'
        # Se for dígito ou int puro
        if isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
            return 'int'
        return 'unknown'

    def visit_StringLiteralNode(self, node):
        return 'string'

    def visit_ReturnNode(self, node):
        return self.visit(node.expression)
    
     
    """
    Função para retornar todos os erros semânticos observados no documento de entrada 
    ou retorna que a analise semnatica não observou nenhum erro semantico
    """
    def cont_erros(self):

        if not self.ast:
            return

        self.visit(self.ast)

        if self.errors:
            print(f"Foram encontrados {len(self.errors)} erros semanticos:")
            for err in enumerate(self.errors, 1):
                print(err)
        else:
            print("\nAnálise semântica concluída com sucesso. (0 erros)")
    
