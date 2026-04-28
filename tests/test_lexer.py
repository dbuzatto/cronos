"""
test_lexer.py - Testes unitários do analisador léxico

Verifica se o lexer gera os tokens corretos pra diferentes entradas.
Roda com: python -m unittest tests/test_lexer.py
"""

import unittest
from cronos.lexer import build_lexer


def tokenize(text):
    """Helper: retorna lista de (tipo, valor) dos tokens gerados pelo lexer."""
    lexer = build_lexer()
    lexer.input(text)
    return [(tok.type, tok.value) for tok in lexer]


class TestLexerPalavrasChave(unittest.TestCase):
    """Testa se as palavras-chave são reconhecidas corretamente."""

    def test_keyword_job(self):
        tokens = tokenize('job')
        self.assertEqual(tokens, [('JOB', 'job')])

    def test_keyword_every(self):
        tokens = tokenize('every')
        self.assertEqual(tokens, [('EVERY', 'every')])

    def test_keyword_at(self):
        tokens = tokenize('at')
        self.assertEqual(tokens, [('AT', 'at')])

    def test_keyword_if(self):
        tokens = tokenize('if')
        self.assertEqual(tokens, [('IF', 'if')])

    def test_keyword_run(self):
        tokens = tokenize('run')
        self.assertEqual(tokens, [('RUN', 'run')])

    def test_keywords_metricas(self):
        # As três métricas suportadas
        tokens = tokenize('disk cpu memory')
        tipos = [t for t, _ in tokens]
        self.assertEqual(tipos, ['DISK', 'CPU', 'MEMORY'])

    def test_keywords_case_insensitive(self):
        # A linguagem aceita EVERY, Every, every — tudo vira o mesmo token
        tokens_upper = tokenize('EVERY')
        tokens_lower = tokenize('every')
        self.assertEqual(tokens_upper[0][0], tokens_lower[0][0])


class TestLexerLiterais(unittest.TestCase):
    """Testa reconhecimento de literais: duração, horário, número, string, identificador."""

    def test_duracao_horas(self):
        tokens = tokenize('1h')
        self.assertEqual(tokens, [('DURATION', (1, 'h'))])

    def test_duracao_minutos(self):
        tokens = tokenize('30m')
        self.assertEqual(tokens, [('DURATION', (30, 'm'))])

    def test_duracao_segundos(self):
        tokens = tokenize('10s')
        self.assertEqual(tokens, [('DURATION', (10, 's'))])

    def test_duracao_dias(self):
        tokens = tokenize('7d')
        self.assertEqual(tokens, [('DURATION', (7, 'd'))])

    def test_horario(self):
        # TIME deve ser reconhecido antes de INTEGER (ambos começam com dígitos)
        tokens = tokenize('08:00')
        self.assertEqual(tokens, [('TIME', '08:00')])

    def test_horario_23h(self):
        tokens = tokenize('23:59')
        self.assertEqual(tokens, [('TIME', '23:59')])

    def test_inteiro(self):
        tokens = tokenize('80')
        self.assertEqual(tokens, [('INTEGER', 80)])

    def test_string_com_espacos(self):
        tokens = tokenize('"tar -czf /tmp/backup.tar.gz /data"')
        self.assertEqual(tokens, [('STRING', 'tar -czf /tmp/backup.tar.gz /data')])

    def test_string_simples(self):
        tokens = tokenize('"echo ok"')
        self.assertEqual(tokens, [('STRING', 'echo ok')])

    def test_identificador_simples(self):
        tokens = tokenize('backup')
        self.assertEqual(tokens, [('IDENTIFIER', 'backup')])

    def test_identificador_com_underscore(self):
        tokens = tokenize('health_check')
        self.assertEqual(tokens, [('IDENTIFIER', 'health_check')])

    def test_identificador_com_numero(self):
        tokens = tokenize('job2')
        self.assertEqual(tokens, [('IDENTIFIER', 'job2')])


class TestLexerComparadores(unittest.TestCase):
    """Testa reconhecimento dos operadores de comparação."""

    def test_maior(self):
        self.assertEqual(tokenize('>'), [('GT', '>')])

    def test_menor(self):
        self.assertEqual(tokenize('<'), [('LT', '<')])

    def test_maior_igual(self):
        # GTE precisa ser reconhecido antes de GT+EQ separados
        self.assertEqual(tokenize('>='), [('GTE', '>=')])

    def test_menor_igual(self):
        self.assertEqual(tokenize('<='), [('LTE', '<=')])

    def test_igual(self):
        self.assertEqual(tokenize('=='), [('EQ', '==')])


class TestLexerIgnorados(unittest.TestCase):
    """Testa que comentários e espaços são silenciosamente ignorados."""

    def test_comentario_ignorado(self):
        tokens = tokenize('# este é um comentário\njob')
        self.assertEqual(tokens, [('JOB', 'job')])

    def test_espacos_ignorados(self):
        tokens = tokenize('  job   ')
        self.assertEqual(tokens, [('JOB', 'job')])

    def test_multiplas_linhas(self):
        src = 'job\n  EVERY\n  RUN'
        tokens = tokenize(src)
        tipos = [t for t, _ in tokens]
        self.assertEqual(tipos, ['JOB', 'EVERY', 'RUN'])


if __name__ == '__main__':
    unittest.main()
