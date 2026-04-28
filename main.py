#!/usr/bin/env python3
"""
main.py - Interface de linha de comando da Cronos DSL

Uso:
    python main.py <arquivo.cronos> [saida.py]

Exemplos:
    python main.py examples/exemplo_basico.cronos
    python main.py meus_jobs.cronos agendador.py
"""

import sys
import os

from cronos.lexer import build_lexer
from cronos.parser import build_parser
from cronos.codegen import generate


def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py <arquivo.cronos> [saida.py]")
        print("Exemplo: python main.py examples/exemplo_basico.cronos")
        sys.exit(1)

    input_path = sys.argv[1]

    if not os.path.exists(input_path):
        print(f"Erro: arquivo '{input_path}' não encontrado.")
        sys.exit(1)

    # Se não informar saída, usa o mesmo nome do arquivo de entrada com .py
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        base = os.path.splitext(input_path)[0]
        output_path = base + '.py'

    # Lê o código fonte .cronos
    with open(input_path, 'r', encoding='utf-8') as f:
        source = f.read()

    # Pipeline: lexer -> parser -> codegen
    lexer = build_lexer()
    parser = build_parser()

    ast = parser.parse(source, lexer=lexer)

    if ast is None:
        print("Erro: falha na análise do arquivo. Verifique a sintaxe.")
        sys.exit(1)

    # Gera o script Python e salva no arquivo de saída
    code = generate(ast)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(code)

    print(f"Script gerado com sucesso: {output_path}")
    print(f"Para executar: python {output_path}")


if __name__ == '__main__':
    main()
