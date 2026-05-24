import sys
import os

from cronos.lexer import build_lexer
from cronos.parser import build_parser, processa_jobs, executa_loop, lista_jobs


def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py <arquivo.cronos>")
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.exists(input_path):
        print(f"Arquivo '{input_path}' nao encontrado.")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        source = f.read()

    lexer = build_lexer()
    parser = build_parser()
    parser.parse(source, lexer=lexer)

    if not lista_jobs:
        print("Nenhum job declarado.")
        sys.exit(1)

    processa_jobs()
    print(f"{len(lista_jobs)} job(s) agendado(s). Ctrl+C pra parar.")
    try:
        executa_loop()
    except KeyboardInterrupt:
        print("\nEncerrado.")


if __name__ == '__main__':
    main()
