import ply.lex as lex

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


# comparadores de dois chars antes dos de um char
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

# TIME e DURATION antes de INTEGER (começam com dígitos)
def t_TIME(t):
    r'[0-2][0-9]:[0-5][0-9]'
    return t

def t_DURATION(t):
    r'[0-9]+[smhd]'
    unit = t.value[-1]
    amount = int(t.value[:-1])
    t.value = (amount, unit)
    return t

def t_STRING(t):
    r'"[^"\n]*"'
    t.value = t.value[1:-1]
    return t

def t_INTEGER(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = _reserved.get(t.value.lower(), 'IDENTIFIER')
    return t

def t_COMMENT(t):
    r'\#[^\n]*'
    pass

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore = ' \t\r'


def t_error(t):
    print(f"Caractere invalido: '{t.value[0]}' na posicao {t.lexpos}")
    t.lexer.skip(1)


def build_lexer():
    return lex.lex()
