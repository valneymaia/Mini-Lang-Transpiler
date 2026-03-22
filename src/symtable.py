class Symbol:
    """
    Representa um símbolo da linguagem (variável ou função).
    """
    def __init__(self, var, type, arity=None):
        self.var = var
        self.type = type
        self.arity = arity

    def __repr__(self):
        return f"Symbol(var='{self.var}', type='{self.type}', arity={self.arity})"
    
class SymTable:
    def __init__(self, prev=None):
        """
        Cria uma tabela de símbolos.
        Se prev for None, estamos no escopo global.
        Caso contrário, é um escopo aninhado.
        """
        self.table = {}
        self.prev = prev

    def insert(self, s: str, symb: Symbol):
        """
        Insere um símbolo no escopo atual.
        Retorna False se o nome já existir neste escopo.
        
        :param self: Descrição
        :param s: Descrição
        :type s: str
        :param symb: Descrição
        :type symb: symbol
        :rtype: bool
        """
        if s in self.table:
            return False
        
        self.table[s] = symb
        return True
    
    def find(self, s):
        """
        Docstring para find
        
        :param self: Descrição
        :param s: Descrição
        :return: Descrição
        :rtype: Any | None
        """
        # Busca primeiro no escopo atual.
        current_scope = self

        # Se não achar, sobe para os escopos anteriores.
        while current_scope is not None:
            if s in current_scope.table:
                return current_scope.table[s]
            
            current_scope = current_scope.prev
            
        return None