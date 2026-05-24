import unittest
from cronos.lexer import build_lexer


def tokenize(text):
    lexer = build_lexer()
    lexer.input(text)
    return [(tok.type, tok.value) for tok in lexer]


class TestLexerPalavrasChave(unittest.TestCase):
    def test_keyword_job(self):
        self.assertEqual(tokenize('job'), [('JOB', 'job')])

    def test_keyword_every(self):
        self.assertEqual(tokenize('every'), [('EVERY', 'every')])

    def test_keyword_at(self):
        self.assertEqual(tokenize('at'), [('AT', 'at')])

    def test_keyword_if(self):
        self.assertEqual(tokenize('if'), [('IF', 'if')])

    def test_keyword_run(self):
        self.assertEqual(tokenize('run'), [('RUN', 'run')])

    def test_keywords_metricas(self):
        tokens = tokenize('disk cpu memory')
        tipos = [t for t, _ in tokens]
        self.assertEqual(tipos, ['DISK', 'CPU', 'MEMORY'])

    def test_keywords_case_insensitive(self):
        self.assertEqual(tokenize('EVERY')[0][0], tokenize('every')[0][0])


class TestLexerLiterais(unittest.TestCase):
    def test_duracao_horas(self):
        self.assertEqual(tokenize('1h'), [('DURATION', (1, 'h'))])

    def test_duracao_minutos(self):
        self.assertEqual(tokenize('30m'), [('DURATION', (30, 'm'))])

    def test_duracao_segundos(self):
        self.assertEqual(tokenize('10s'), [('DURATION', (10, 's'))])

    def test_duracao_dias(self):
        self.assertEqual(tokenize('7d'), [('DURATION', (7, 'd'))])

    def test_horario(self):
        self.assertEqual(tokenize('08:00'), [('TIME', '08:00')])

    def test_horario_23h(self):
        self.assertEqual(tokenize('23:59'), [('TIME', '23:59')])

    def test_inteiro(self):
        self.assertEqual(tokenize('80'), [('INTEGER', 80)])

    def test_string_com_espacos(self):
        self.assertEqual(tokenize('"tar -czf /tmp/backup.tar.gz /data"'),
                         [('STRING', 'tar -czf /tmp/backup.tar.gz /data')])

    def test_string_simples(self):
        self.assertEqual(tokenize('"echo ok"'), [('STRING', 'echo ok')])

    def test_identificador_simples(self):
        self.assertEqual(tokenize('backup'), [('IDENTIFIER', 'backup')])

    def test_identificador_com_underscore(self):
        self.assertEqual(tokenize('health_check'), [('IDENTIFIER', 'health_check')])

    def test_identificador_com_numero(self):
        self.assertEqual(tokenize('job2'), [('IDENTIFIER', 'job2')])


class TestLexerComparadores(unittest.TestCase):
    def test_maior(self):
        self.assertEqual(tokenize('>'), [('GT', '>')])

    def test_menor(self):
        self.assertEqual(tokenize('<'), [('LT', '<')])

    def test_maior_igual(self):
        self.assertEqual(tokenize('>='), [('GTE', '>=')])

    def test_menor_igual(self):
        self.assertEqual(tokenize('<='), [('LTE', '<=')])

    def test_igual(self):
        self.assertEqual(tokenize('=='), [('EQ', '==')])


class TestLexerIgnorados(unittest.TestCase):
    def test_comentario_ignorado(self):
        self.assertEqual(tokenize('# comentario\njob'), [('JOB', 'job')])

    def test_espacos_ignorados(self):
        self.assertEqual(tokenize('  job   '), [('JOB', 'job')])

    def test_multiplas_linhas(self):
        tokens = tokenize('job\n  EVERY\n  RUN')
        tipos = [t for t, _ in tokens]
        self.assertEqual(tipos, ['JOB', 'EVERY', 'RUN'])


if __name__ == '__main__':
    unittest.main()
