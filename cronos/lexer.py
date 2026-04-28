"""
lexer.py - Analisador léxico da Cronos DSL

Transforma o texto de entrada em uma sequência de tokens usando PLY.
O PLY usa expressões regulares associadas a funções t_* pra reconhecer cada token.

Tokens reconhecidos:
  Palavras-chave : JOB, EVERY, AT, IF, RUN, DISK, CPU, MEMORY
  Comparadores  : GTE (>=), LTE (<=), EQ (==), GT (>), LT (<)
  Literais      : DURATION (ex: 1h, 30m), TIME (ex: 08:00), INTEGER, STRING, IDENTIFIER
"""

import ply.lex as lex

# Palavras reservadas — mapeamos lowercase pra o tipo de token correspondente
_reserved = {
    'job':    'JOB',
    'every':  'EVERY',
    'at':     'AT',
    'if':     'IF',
    'run':    'RUN',
    'disk':   'DISK',
    'cpu':    'CPU',
    'memory': 'MEMORY',
}

# O PLY exige que 'tokens' seja uma lista no módulo do lexer
tokens = [
    'IDENTIFIER',
    'INTEGER',
    'STRING',
    'TIME',
    'DURATION',
    'GTE',
    'LTE',
    'EQ',
    'GT',
    'LT',
] + list(_reserved.values())


# ATENÇÃO: a ordem das funções t_* importa no PLY!
# Funções são testadas na ordem em que aparecem no arquivo.
# Regras de string são ordenadas por comprimento (maior primeiro).
# Por isso os comparadores de dois chars vêm antes dos de um char,
# e TIME/DURATION vêm antes de INTEGER.


def t_GTE(t):
    r'>='
    return t


def t_LTE(t):
    r'<='
    return t


def t_EQ(t):
    r'=='
    return t


def t_GT(t):
    r'>'
    return t


def t_LT(t):
    r'<'
    return t


def t_TIME(t):
    r'[0-2][0-9]:[0-5][0-9]'
    # Precisa vir antes de INTEGER porque '08:00' começa com dígitos
    return t


def t_DURATION(t):
    r'[0-9]+[smhd]'
    # Precisa vir antes de INTEGER pelo mesmo motivo acima
    # Separa número e unidade: '30m' -> (30, 'm')
    unit = t.value[-1]
    amount = int(t.value[:-1])
    t.value = (amount, unit)
    return t


def t_STRING(t):
    r'"[^"\n]*"'
    # Remove as aspas — o valor já chega sem elas pro parser
    t.value = t.value[1:-1]
    return t


def t_INTEGER(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t


def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    # Checa se é palavra reservada (case-insensitive pra aceitar EVERY e every)
    t.type = _reserved.get(t.value.lower(), 'IDENTIFIER')
    return t


def t_COMMENT(t):
    r'\#[^\n]*'
    # Comentários no estilo shell/Python — simplesmente ignora
    pass


# Espaços, tabs e quebras de linha são ignorados
t_ignore = ' \t\n\r'


def t_error(t):
    print(f"[Lexer] Caractere inválido: '{t.value[0]}' na posição {t.lexpos}")
    t.lexer.skip(1)


def build_lexer():
    """Constrói e retorna uma instância do lexer PLY."""
    return lex.lex()
