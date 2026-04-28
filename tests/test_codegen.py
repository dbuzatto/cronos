"""
test_codegen.py - Testes unitários do gerador de código

Verifica se o codegen produz o script Python correto pra cada tipo de job.
Roda com: python -m unittest tests/test_codegen.py
"""

import unittest
from cronos.ast_nodes import (
    Program, JobDecl,
    ScheduleEvery, ScheduleAt,
    Condition, RunClause,
)
from cronos.codegen import generate


def make_job(name, schedule, condition=None, command='echo ok'):
    """Helper: cria um JobDecl com os parâmetros dados."""
    return JobDecl(name=name, schedule=schedule, condition=condition, run=RunClause(command))


class TestCodegenImportsEstrutura(unittest.TestCase):
    """Testa se o script gerado tem a estrutura básica esperada."""

    def setUp(self):
        prog = Program(jobs=[make_job('teste', ScheduleEvery(1, 'h'))])
        self.code = generate(prog)

    def test_import_schedule(self):
        self.assertIn('import schedule', self.code)

    def test_import_psutil(self):
        self.assertIn('import psutil', self.code)

    def test_import_subprocess(self):
        self.assertIn('import subprocess', self.code)

    def test_import_time(self):
        self.assertIn('import time', self.code)

    def test_loop_principal(self):
        self.assertIn('while True:', self.code)
        self.assertIn('schedule.run_pending()', self.code)
        self.assertIn('time.sleep(1)', self.code)

    def test_aviso_nao_editar(self):
        # O script gerado deve avisar que não deve ser editado manualmente
        self.assertIn('gerado automaticamente', self.code)


class TestCodegenAgendamento(unittest.TestCase):
    """Testa geração das chamadas de agendamento."""

    def test_every_horas(self):
        prog = Program(jobs=[make_job('backup', ScheduleEvery(1, 'h'))])
        code = generate(prog)
        self.assertIn('schedule.every(1).hours.do(job_backup)', code)

    def test_every_minutos(self):
        prog = Program(jobs=[make_job('check', ScheduleEvery(30, 'm'))])
        code = generate(prog)
        self.assertIn('schedule.every(30).minutes.do(job_check)', code)

    def test_every_segundos(self):
        prog = Program(jobs=[make_job('ping', ScheduleEvery(10, 's'))])
        code = generate(prog)
        self.assertIn('schedule.every(10).seconds.do(job_ping)', code)

    def test_every_dias(self):
        prog = Program(jobs=[make_job('limpeza', ScheduleEvery(7, 'd'))])
        code = generate(prog)
        self.assertIn('schedule.every(7).days.do(job_limpeza)', code)

    def test_at_horario(self):
        prog = Program(jobs=[make_job('morning', ScheduleAt('08:00'))])
        code = generate(prog)
        self.assertIn('schedule.every().day.at("08:00").do(job_morning)', code)

    def test_at_horario_noturno(self):
        prog = Program(jobs=[make_job('noturno', ScheduleAt('23:00'))])
        code = generate(prog)
        self.assertIn('schedule.every().day.at("23:00").do(job_noturno)', code)


class TestCodegenFuncaoJob(unittest.TestCase):
    """Testa geração das funções dos jobs."""

    def test_nome_funcao_gerada(self):
        prog = Program(jobs=[make_job('meu_job', ScheduleEvery(1, 'h'))])
        code = generate(prog)
        self.assertIn('def job_meu_job():', code)

    def test_comando_no_corpo(self):
        prog = Program(jobs=[make_job('x', ScheduleEvery(1, 'h'), command='ls -la')])
        code = generate(prog)
        self.assertIn("subprocess.run('ls -la', shell=True)", code)

    def test_sem_condicao_sem_metrica(self):
        # Job sem IF não deve verificar nenhuma métrica
        prog = Program(jobs=[make_job('simples', ScheduleEvery(1, 'h'))])
        code = generate(prog)
        self.assertNotIn('metric_value', code)


class TestCodegenCondicao(unittest.TestCase):
    """Testa geração de código quando há cláusula IF."""

    def test_condicao_disk(self):
        prog = Program(jobs=[
            make_job('backup', ScheduleEvery(1, 'h'),
                     condition=Condition('disk', '>', 80))
        ])
        code = generate(prog)
        self.assertIn('psutil.disk_usage("/").percent', code)
        self.assertIn('> 80', code)

    def test_condicao_cpu(self):
        prog = Program(jobs=[
            make_job('alerta', ScheduleEvery(5, 'm'),
                     condition=Condition('cpu', '>=', 90))
        ])
        code = generate(prog)
        self.assertIn('psutil.cpu_percent(interval=1)', code)
        self.assertIn('>= 90', code)

    def test_condicao_memory(self):
        prog = Program(jobs=[
            make_job('gc', ScheduleEvery(10, 'm'),
                     condition=Condition('memory', '<', 95))
        ])
        code = generate(prog)
        self.assertIn('psutil.virtual_memory().percent', code)
        self.assertIn('< 95', code)

    def test_metrica_atribuida_a_variavel(self):
        # A metrica deve ser atribuída a metric_value antes do if
        prog = Program(jobs=[
            make_job('x', ScheduleEvery(1, 'm'),
                     condition=Condition('cpu', '>', 50))
        ])
        code = generate(prog)
        self.assertIn('metric_value =', code)
        self.assertIn('if metric_value', code)


class TestCodegenMultiplosJobs(unittest.TestCase):
    """Testa geração com múltiplos jobs no mesmo arquivo."""

    def test_dois_jobs_geram_duas_funcoes(self):
        prog = Program(jobs=[
            make_job('job_a', ScheduleEvery(1, 'h')),
            make_job('job_b', ScheduleAt('08:00')),
        ])
        code = generate(prog)
        self.assertIn('def job_job_a():', code)
        self.assertIn('def job_job_b():', code)

    def test_dois_jobs_geram_dois_schedules(self):
        prog = Program(jobs=[
            make_job('a', ScheduleEvery(1, 'h')),
            make_job('b', ScheduleEvery(30, 'm')),
        ])
        code = generate(prog)
        self.assertIn('schedule.every(1).hours.do(job_a)', code)
        self.assertIn('schedule.every(30).minutes.do(job_b)', code)


if __name__ == '__main__':
    unittest.main()
