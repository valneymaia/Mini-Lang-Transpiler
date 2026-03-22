import os
import sys
from lexer import LexerError
from parser import Parser, ParseError
from semantic import SemanticAnalyzer
from codegen import CCodeGenerator


def main():
    # Se não vier argumento, usa um arquivo de exemplo.
    input_file = "tests/exemplo2.mini" if len(sys.argv) < 2 else sys.argv[1]
    output_file = input_file.replace(".mini", ".c")

    def cleanup_output():
        # Remove o .c se a execução falhar no meio.
        if os.path.exists(output_file):
            os.remove(output_file)

    # Parsing: análise léxica + sintática.
    try:
        parser = Parser(input_file)
        ast = parser.start()
    except FileNotFoundError:
        print(f"Erro: arquivo não encontrado: {input_file}")
        cleanup_output()
        return 1
    except (LexerError, ParseError) as err:
        print(err)
        print("Transpilação interrompida: não foi possível gerar código C.")
        cleanup_output()
        return 1

    if ast is None:
        print("Erro: não foi possível construir a AST.")
        print("Transpilação interrompida: não foi possível gerar código C.")
        cleanup_output()
        return 1

    # Análise semântica.
    analyzer = SemanticAnalyzer(ast)
    if not analyzer.analyze():
        analyzer.cont_erros()
        print("Transpilação interrompida: código Mini-Lang contém erros semânticos.")
        cleanup_output()
        return 1

    analyzer.cont_erros()

    # Geração de código C (só roda sem erros anteriores).
    generator = CCodeGenerator()
    c_code = generator.generate(ast)

    # Grava o código C no disco.
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(c_code)

    print(f"✓ Código C gerado com sucesso: {output_file}")
    print("\n--- Código gerado ---")
    print(c_code)
    return 0


if __name__ == "__main__":
    sys.exit(main())
