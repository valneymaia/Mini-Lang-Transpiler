# Mini-Lang Transpiler

Projeto da disciplina de Compiladores.

A ideia aqui foi fazer um transpilador da linguagem Mini-Lang usando Python. O processo é:
1. Análise léxica
2. Análise sintática (gera AST)
3. Análise semântica
4. Geração de código C

## Estrutura

- `src/lexer.py`: analisador léxico
- `src/parser.py`: parser e construção da AST
- `src/semantic.py`: validações semânticas
- `src/codegen.py`: geração de código C
- `src/main.py`: arquivo principal para executar o fluxo
- `tests/`: exemplos de entrada `.mini`

## Como rodar

No terminal, na raiz do projeto:

```bash
python src/main.py tests/exemplo_simple.mini
```

Isso vai gerar um arquivo C na pasta `tests` (ex: `exemplo_simple.c`).

Para compilar:

```bash
gcc tests/exemplo_simple.c -o tests/exemplo_simple.exe
```

Para executar:

```bash
./tests/exemplo_simple.exe
```

## Observação

Alguns arquivos de teste foram feitos para provocar erro semântico de propósito, então nem todo `.mini` vai passar sem erro.
