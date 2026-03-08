class Symbol:
    """
    Estrutura para salvar o nome de uma variável e o tipo
    """
    class Symbol:
    def __init__(self, var, type, arity=None):
        self.var = var
        self.type = type
        self.arity = arity

    def __repr__(self):
        return f"Symbol(var='{self.var}', type='{self.type}', arity={self.arity})"
    
class SymTable:
    def __init__(self, prev=None):
        """
        Construtor do SymTable.
        Se prev for None, essa é uma tabela global (escopo mais externo)
        Se 'prev' for passado, é uma nova tabela aninhada a ser criada 
        dentro do escopo de 'prev'
        """
        self.table = {} # tabela inicia vazia
        self.prev = prev

    def insert(self, s: str, symb: Symbol):
        """
        Função para inseir um símbolo na tabela atual
        Retorna True se inseriu com sucesso, False se já
         existia a entrada na tabela
        
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
        #começa a busca na tabela atual
        current_scope = self

        # percorre as referÊncias para prev
        while current_scope is not None:
            if s in current_scope.table:
                return current_scope.table[s]
            
            # sobe para o escopo anterior
            current_scope = current_scope.prev
            
        return None