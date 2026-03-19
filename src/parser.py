import sys
from lexer import Lexer, Token, TAG
from ast_nodes import *

# Definimos uma exceção personalizada para evitar confusão 
# com o "SyntaxError" nativo do Python
class ParseError(Exception):
    pass

class Parser:
    def __init__(self, filename: str):
        self._lexer = Lexer(filename)
        self.lookahead = Token('')
    

    def start(self):
        """Inicia o processo de análise lendo o primeiro caractere."""
        # lê próximo token
        self.lookahead = self._lexer.scan()
        if self.lookahead is not None:
            return self.program()
        
        # Verifica se o último caractere é uma quebra de linha
        # if self.lookahead != '\n':
        #     raise ParseError()


    def program(self):
        """
        Regra: <program> -> { <statement> }
        """
        statements = []

        while self.lookahead.tag is not None:  # Enquanto não chegar ao EOF:
            stmt_node = self.statement()

            if stmt_node:
                statements.append(stmt_node)
            else:
                raise ParseError(f"Erro de sintaxe na linha {self._lexer.get_line()}")
            
        return ProgramNode(statements)


    def block(self):
        """
        Regra:  <block> -> "{" {<statement>} "}"
        """
        statements = []

        self.match('{')
        while self.lookahead.tag != '}':
            stmt_node = self.statement()
            statements.append(stmt_node)
        
        self.match('}')

        return BlockNode(statements)
    

    def statement(self):
        """
        Regra: <statement> -> = < variable - decl > ";"
                                | < assignment > ";"
                                | < print - statement > ";"
                                | <if - statement >
                                | < while - statement >
                                | < return - statement > ";"
                                | < function - decl >
                                | < block >

        """
        if self.lookahead.tag == TAG.VAR:
            vrbl_decl_node = self.variable_decl()
            self.match(';')
            return vrbl_decl_node
        elif self.lookahead.tag == TAG.SET:
            assign_node = self.assignment()
            self.match(';')
            return assign_node
        elif self.lookahead.tag == TAG.PRINT:
            print_node = self.print_statement()
            self.match(';')
            return print_node
        elif self.lookahead.tag == TAG.IF:
            return self.if_statement()
        elif self.lookahead.tag == TAG.WHILE:
            return self.while_statement()
        elif self.lookahead.tag == TAG.RETURN:
            return_node = self.return_statement()
            self.match(';')
            return return_node
        elif self.lookahead.tag == TAG.DEF:
            return self.function_decl()
        elif self.lookahead.tag == '{':
            return self.block()
        else:
            raise ParseError(f"Erro de sintaxe: token inesperado '{self.lookahead.lexeme}' na linha {self._lexer.get_line()}")


    def function_decl(self):
        """
        Regra: <function - decl> -> "def" <identifier> "(" [<formal - params>] ")" ":" <type> <block>
        """
        self.match(TAG.DEF)
        func_name_node = self.identifier()
        self.match('(')
        parameters = []
        if self.lookahead.tag != ')':
            parameters = self.formal_params()
        self.match(')')
        self.match(':')
        return_type_node = self.type()
        body_node = self.block()

        return FunctionDeclNode(func_name_node, parameters, return_type_node, body_node)
    

    def formal_params(self):
        """
        Regra: <formal - params> -> < formal - param > { " ," < formal - param > }
        """
        params = []
        param_node = self.formal_param()
        params.append(param_node)
        while self.lookahead.tag == ',':
            self.match(',')
            param_node = self.formal_param()
            params.append(param_node)
        
        return params 
    

    def formal_param(self):
        """
        Regra: <formal - param> -> <identifier> ":" <type>
        """
        id_node = self.identifier()
        self.match(':')
        type_node = self.type()

        return FormalParamNode(id_node, type_node)
    

    def while_statement(self):
        """
        Regra: <while - statement> -> " while " "(" < expression > ") " < block >
        """
        self.match(TAG.WHILE)
        self.match('(')
        condition_node = self.expression()
        self.match(')')
        block_node = self.block()

        return WhileNode(condition_node, block_node)
    

    def if_statement(self):
        """
        Regra: <if - statement> -> " if " "(" < expression > ") " < block > [ " else " < block > ]
        """
        self.match(TAG.IF)
        self.match('(')
        condition_node = self.expression()
        self.match(')')
        then_block_node = self.block()

        else_block_node = None
        if self.lookahead.tag == TAG.ELSE:
            self.match(TAG.ELSE)
            else_block_node = self.block()

        return IfNode(condition_node, then_block_node, else_block_node)
    

    def return_statement(self):
        """
        Regra: <return - statement> -> " return " < expression >
        """
        self.match(TAG.RETURN)
        expr_node = self.expression()

        return ReturnNode(expr_node)
    
    
    def print_statement(self):
        """
        Regra: <print - statement> -> " print " < string - literal >
        """
        self.match(TAG.PRINT)
        str_lit_node = self.string_literal()

        return PrintNode(str_lit_node)
    

    def type(self):
        """
        Regra: <type> -> " int " | " real " | " bool " | " void "
        """
        if self.lookahead.tag == TAG.TYPE:
            type_node = TypeNode(self.lookahead.lexeme)
            self.match(self.lookahead.tag)
            return type_node
        else:
            raise ParseError(f"Erro de sintaxe: tipo esperado na linha {self._lexer.get_line()}")
        

    def variable_decl(self):
        """
        Regra: <variable - decl> -> " var " <identifier> ":" <type> "=" < expression >
        """
        self.match(TAG.VAR)
        id_node = self.identifier()
        self.match(':')
        type_node = self.type()
        self.match('=')
        expr_node = self.expression()

        return VarDeclNode(id_node, type_node, expr_node)
    

    def assignment(self):
        """
        Regra: <assignment> -> " set " <identifier> "=" < expression >
        """
        self.match(TAG.SET)
        id_node = self.identifier()
        self.match('=')
        expr_node = self.expression()

        return AssignmentNode(id_node, expr_node)
    

    def expression(self):
        """
        Regra: < expression> -> < simple - expression > { < relational -op > < simple - expression > }
        """
        left_node = self.simple_expression()

        while self.lookahead.tag in [TAG.EQ, TAG.NEQ, '<', '>', TAG.GTE, TAG.LTE]:
            op_node = self.relational_op()
            right_node = self.simple_expression()
            left_node = BinaryOpNode(op_node, left_node, right_node)

        return left_node
    

    def simple_expression(self):
        """
        Regra: < simple - expression > -> < term > { < additive - op > <term > }
        """
        left_node = self.term()

        while self.lookahead.tag in ['+', '-', TAG.OR]:
            op_node = self.additive_op()
            right_node = self.term()
            left_node = BinaryOpNode(op_node, left_node, right_node)

        return left_node


    def term(self):
        """
        Regra: <term > = < factor > { < multiplicative - op > < factor > }
        """
        left_node = self.factor()

        while self.lookahead.tag in ['*', '/', TAG.AND]:
            op_node = self.multiplicative_op()
            right_node = self.factor()
            left_node = BinaryOpNode(op_node, left_node, right_node)

        return left_node
    

    def factor(self):
        """
        Regra: < factor > -> < literal >
                            | < identifier >
                            | < function - call >
                            | < sub - expression >
                            | < unary >
        """
        if self.lookahead.tag in [TAG.INTEGER, TAG.REAL, TAG.TRUE, TAG.FALSE]:
            literal_node = self.literal()
            return literal_node
        elif self.lookahead.tag == TAG.ID:
            id_node = self.identifier()
            if self.lookahead.tag == '(':  # Chamada de função
                return self.function_call(id_node)
            else:
                return id_node
        elif self.lookahead.tag == '(':
            return self.sub_expression()
        elif self.lookahead.tag in ['+', '-', TAG.NOT]:
            return self.unary()
        else:
            raise ParseError(f"Erro de sintaxe: token inesperado '{self.lookahead.lexeme}' na linha {self._lexer.get_line()}")


    def unary(self):
        """
        Regra: < unary > -> ( "+" | "-" | " not " ) < expression >
        """
        op_node = self.lookahead.tag
        if self.lookahead.tag in ['+', '-', TAG.NOT]:
            self.match(self.lookahead.tag)
            expr_node = self.expression()
            return UnaryOpNode(op_node, expr_node)
        else:
            raise ParseError(f"Erro de sintaxe: operador unário esperado na linha {self._lexer.get_line()}")
        

    def sub_expression(self):
        """
        Regra: < sub - expression > -> "(" < expression > ")"
        """
        self.match('(')
        expr_node = self.expression()
        self.match(')')
        return expr_node
    

    def function_call(self, id_node):
        """
        Regra: < function - call > -> < identifier > "(" [ < actual_params > ] ")"
        """
        self.match('(')
        args = []
        if self.lookahead.tag != ')':
            args = self.actual_params()
        self.match(')')

        return FunctionCallNode(id_node, args)
    

    def actual_params(self):
        """
        Regra: < actual_params > -> < expression > { "," < expression > }
        """
        args = []
        expr_node = self.expression()
        args.append(expr_node)
        while self.lookahead.tag == ',':
            self.match(',')
            expr_node = self.expression()
            args.append(expr_node)

        return args


    def relational_op(self):
        """
        Regra: < relational - op > -> "==" | "!=" | "<" | ">" | "<=" | ">="
        """
        if self.lookahead.tag in [TAG.EQ, TAG.NEQ, '<', '>', TAG.GTE, TAG.LTE]:
            op_node = self.lookahead.tag
            self.match(self.lookahead.tag)
            return op_node
        else:
            raise ParseError(f"Erro de sintaxe: operador relacional esperado na linha {self._lexer.get_line()}")
        

    def additive_op(self):
        """
        Regra: < additive - op > -> "+" | "-" | " or "
        """
        if self.lookahead.tag in ['+', '-', TAG.OR]:
            op_node = self.lookahead.tag
            self.match(self.lookahead.tag)
            return op_node
        else:
            raise ParseError(f"Erro de sintaxe: operador aditivo esperado na linha {self._lexer.get_line()}")
        
    
    def multiplicative_op(self):    
        """
        Regra: < multiplicative - op > -> "*" | "/" | " and "
        """
        if self.lookahead.tag in ['*', '/', TAG.AND]:
            op_node = self.lookahead.tag
            self.match(self.lookahead.tag)
            return op_node
        else:
            raise ParseError(f"Erro de sintaxe: operador multiplicativo esperado na linha {self._lexer.get_line()}")
        

    def identifier(self):
        """
        Regra: < identifier > -> ( "_ " | < letter > ) { "_" | < letter > | < digit > }
        """
        if self.lookahead.tag == TAG.ID:
            id_node = IdentifierNode(self.lookahead.lexeme)
            self.match(TAG.ID)
            return id_node
        else:
            raise ParseError(f"Erro de sintaxe: identificador esperado na linha {self._lexer.get_line()}")
        

    def literal(self):
        """
        Regra: < literal > -> < integer - literal > | < real - literal > | "true" | "false"
        """
        if self.lookahead.tag in [TAG.INTEGER, TAG.REAL, TAG.TRUE, TAG.FALSE]:
            literal_node = LiteralNode(self.lookahead.lexeme, self.lookahead.tag)
            self.match(self.lookahead.tag)
            return literal_node
        else:
            raise ParseError(f"Erro de sintaxe: literal esperado na linha {self._lexer.get_line()}")
        

    def string_literal(self):
        """
        Regra: < string - literal > -> " <string> "
        """
        if self.lookahead.tag == TAG.STRING:
            str_lit_node = StringLiteralNode(self.lookahead.lexeme)
            self.match(TAG.STRING)
            return str_lit_node
        else:
            raise ParseError(f"Erro de sintaxe: literal de string esperado na linha {self._lexer.get_line()}")


    def match(self, t: TAG):
        """Verifica se o caractere atual corresponde ao esperado e avança."""
        if t == self.lookahead.tag:
            self.lookahead = self._lexer.scan()
        else:
            raise ParseError(f"Erro de sintaxe: Esperado '{t}', mas encontrou '{self.lookahead.lexeme}' na linha {self._lexer.get_line()}")

