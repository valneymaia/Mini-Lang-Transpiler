import json
from parser import Parser
from semantic import SemanticAnalyzer


parser = Parser("tests/exemplo1.mini")
ast = parser.start()

analyzer = SemanticAnalyzer(ast)
analyzer.cont_erros(); 

# Gera o JSON indentado conforme exigido
#print(json.dumps(ast.to_dict(), indent=4, ensure_ascii=False))