import json
import sys
from parser import Parser
from semantic import SemanticAnalyzer
from codegen import CCodeGenerator


# Arquivo de entrada
input_file = "tests/exemplo_loops.mini" if len(sys.argv) < 2 else sys.argv[1]
output_file = input_file.replace(".mini", ".c")

# Parse
parser = Parser(input_file)
ast = parser.start()

# Análise semântica
analyzer = SemanticAnalyzer(ast)
analyzer.cont_erros()

# Geração de código C
generator = CCodeGenerator()
c_code = generator.generate(ast)

# Salva código C em arquivo
with open(output_file, "w", encoding="utf-8") as f:
    f.write(c_code)

print(f"✓ Código C gerado com sucesso: {output_file}")
print("\n--- Código gerado ---")
print(c_code)