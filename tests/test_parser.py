"""
test_parser.py - Testes unitários do analisador sintático

Verifica se o parser constrói a AST correta pra diferentes programas Cronos.
Roda com: python -m unittest tests/test_parser.py
"""

import unittest
from cronos.lexer import build_lexer
from cronos.parser import build_parser
from cronos.ast_nodes import (
    Program, JobDecl,
    ScheduleEvery, ScheduleAt,
    Condition, RunClause,
)


def parse(text):
    """Helper: faz o parse completo de um texto e retorna a AST."""
    lexer = build_lexer()
    parser = build_parser()
    return parser.parse(text, lexer=lexer)


class TestParserJobSimples(unittest.TestCase):
    """Testa parsing de jobs básicos sem condição."""

    def test_job_every_sem_condicao(self):
        src = 'job backup\n  EVERY 1h\n  RUN "tar -czf /tmp/bkp.tar.gz /data"'
        ast = parse(src)

        self.assertIsInstance(ast, Program)
        self.assertEqual(len(ast.jobs), 1)

        job = ast.jobs[0]
        self.assertIsInstance(job, JobDecl)
        self.assertEqual(job.name, 'backup')
        self.assertIsNone(job.condition)

    def test_agendamento_every_horas(self):
        src = 'job x\n  EVERY 1h\n  RUN "echo ok"'
        job = parse(src).jobs[0]
        self.assertIsInstance(job.schedule, ScheduleEvery)
        self.assertEqual(job.schedule.amount, 1)
        self.assertEqual(job.schedule.unit, 'h')

    def test_agendamento_every_minutos(self):
        src = 'job x\n  EVERY 30m\n  RUN "echo ok"'
        job = parse(src).jobs[0]
        self.assertEqual(job.schedule.amount, 30)
        self.assertEqual(job.schedule.unit, 'm')

    def test_agendamento_at(self):
        src = 'job health_check\n  AT 08:00\n  RUN "curl -f http://localhost/health"'
        job = parse(src).jobs[0]
        self.assertIsInstance(job.schedule, ScheduleAt)
        self.assertEqual(job.schedule.time, '08:00')

    def test_run_command(self):
        src = 'job x\n  EVERY 5m\n  RUN "ls -la"'
        job = parse(src).jobs[0]
        self.assertIsInstance(job.run, RunClause)
        self.assertEqual(job.run.command, 'ls -la')


class TestParserCondicao(unittest.TestCase):
    """Testa parsing da cláusula IF com métricas e comparadores."""

    def _parse_condicao(self, metrica, op, val):
        src = f'job teste\n  EVERY 1m\n  IF {metrica} {op} {val}\n  RUN "echo ok"'
        ast = parse(src)
        return ast.jobs[0].condition

    def test_condicao_presente(self):
        src = 'job limpar\n  EVERY 30m\n  IF disk > 80\n  RUN "rm -rf /tmp/old"'
        job = parse(src).jobs[0]
        self.assertIsNotNone(job.condition)
        self.assertIsInstance(job.condition, Condition)

    def test_metrica_disk(self):
        cond = self._parse_condicao('disk', '>', 80)
        self.assertEqual(cond.metric, 'disk')

    def test_metrica_cpu(self):
        cond = self._parse_condicao('cpu', '>', 90)
        self.assertEqual(cond.metric, 'cpu')

    def test_metrica_memory(self):
        cond = self._parse_condicao('memory', '<', 95)
        self.assertEqual(cond.metric, 'memory')

    def test_comparador_gt(self):
        cond = self._parse_condicao('cpu', '>', 90)
        self.assertEqual(cond.comparator, '>')

    def test_comparador_lt(self):
        cond = self._parse_condicao('memory', '<', 50)
        self.assertEqual(cond.comparator, '<')

    def test_comparador_gte(self):
        cond = self._parse_condicao('disk', '>=', 75)
        self.assertEqual(cond.comparator, '>=')

    def test_comparador_lte(self):
        cond = self._parse_condicao('cpu', '<=', 20)
        self.assertEqual(cond.comparator, '<=')

    def test_comparador_eq(self):
        cond = self._parse_condicao('memory', '==', 100)
        self.assertEqual(cond.comparator, '==')

    def test_valor_condicao(self):
        cond = self._parse_condicao('disk', '>', 85)
        self.assertEqual(cond.value, 85)


class TestParserMultiplosJobs(unittest.TestCase):
    """Testa parsing de arquivos com mais de um job declarado."""

    def test_dois_jobs(self):
        src = (
            'job backup\n  EVERY 1h\n  RUN "echo backup"\n'
            'job health_check\n  AT 08:00\n  RUN "echo health"\n'
        )
        ast = parse(src)
        self.assertEqual(len(ast.jobs), 2)
        self.assertEqual(ast.jobs[0].name, 'backup')
        self.assertEqual(ast.jobs[1].name, 'health_check')

    def test_tres_jobs_misturados(self):
        src = (
            'job a\n  EVERY 1h\n  RUN "echo a"\n'
            'job b\n  EVERY 5m\n  IF cpu > 80\n  RUN "echo b"\n'
            'job c\n  AT 23:00\n  RUN "echo c"\n'
        )
        ast = parse(src)
        self.assertEqual(len(ast.jobs), 3)

        # Job b tem condição, os outros não
        self.assertIsNone(ast.jobs[0].condition)
        self.assertIsNotNone(ast.jobs[1].condition)
        self.assertIsNone(ast.jobs[2].condition)


if __name__ == '__main__':
    unittest.main()
