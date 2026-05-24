import unittest
from cronos.lexer import build_lexer
from cronos.parser import build_parser, lista_jobs


def parse(text):
    lexer = build_lexer()
    parser = build_parser()
    parser.parse(text, lexer=lexer)
    return list(lista_jobs)


class TestParserJobSimples(unittest.TestCase):
    def test_job_every_sem_condicao(self):
        src = 'job backup\n  EVERY 1h\n  RUN "tar -czf /tmp/bkp.tar.gz /data"'
        jobs = parse(src)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['nome'], 'backup')
        self.assertIsNone(jobs[0]['condicao'])

    def test_agendamento_every_horas(self):
        job = parse('job x\n  EVERY 1h\n  RUN "echo ok"')[0]
        self.assertEqual(job['agenda'], ('every', 1, 'h'))

    def test_agendamento_every_minutos(self):
        job = parse('job x\n  EVERY 30m\n  RUN "echo ok"')[0]
        self.assertEqual(job['agenda'], ('every', 30, 'm'))

    def test_agendamento_at(self):
        job = parse('job health_check\n  AT 08:00\n  RUN "curl -f http://localhost/health"')[0]
        self.assertEqual(job['agenda'], ('at', '08:00'))

    def test_run_command(self):
        job = parse('job x\n  EVERY 5m\n  RUN "ls -la"')[0]
        self.assertEqual(job['comando'], 'ls -la')


class TestParserCondicao(unittest.TestCase):
    def _parse_condicao(self, metrica, op, val):
        src = f'job teste\n  EVERY 1m\n  IF {metrica} {op} {val}\n  RUN "echo ok"'
        return parse(src)[0]['condicao']

    def test_condicao_presente(self):
        job = parse('job limpar\n  EVERY 30m\n  IF disk > 80\n  RUN "rm -rf /tmp/old"')[0]
        self.assertIsNotNone(job['condicao'])

    def test_metrica_disk(self):
        self.assertEqual(self._parse_condicao('disk', '>', 80)[0], 'disk')

    def test_metrica_cpu(self):
        self.assertEqual(self._parse_condicao('cpu', '>', 90)[0], 'cpu')

    def test_metrica_memory(self):
        self.assertEqual(self._parse_condicao('memory', '<', 95)[0], 'memory')

    def test_comparador_gt(self):
        self.assertEqual(self._parse_condicao('cpu', '>', 90)[1], '>')

    def test_comparador_lt(self):
        self.assertEqual(self._parse_condicao('memory', '<', 50)[1], '<')

    def test_comparador_gte(self):
        self.assertEqual(self._parse_condicao('disk', '>=', 75)[1], '>=')

    def test_comparador_lte(self):
        self.assertEqual(self._parse_condicao('cpu', '<=', 20)[1], '<=')

    def test_comparador_eq(self):
        self.assertEqual(self._parse_condicao('memory', '==', 100)[1], '==')

    def test_valor_condicao(self):
        self.assertEqual(self._parse_condicao('disk', '>', 85)[2], 85)


class TestParserMultiplosJobs(unittest.TestCase):
    def test_dois_jobs(self):
        src = ('job backup\n  EVERY 1h\n  RUN "echo backup"\n'
               'job health_check\n  AT 08:00\n  RUN "echo health"\n')
        jobs = parse(src)
        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0]['nome'], 'backup')
        self.assertEqual(jobs[1]['nome'], 'health_check')

    def test_tres_jobs_misturados(self):
        src = ('job a\n  EVERY 1h\n  RUN "echo a"\n'
               'job b\n  EVERY 5m\n  IF cpu > 80\n  RUN "echo b"\n'
               'job c\n  AT 23:00\n  RUN "echo c"\n')
        jobs = parse(src)
        self.assertEqual(len(jobs), 3)
        self.assertIsNone(jobs[0]['condicao'])
        self.assertIsNotNone(jobs[1]['condicao'])
        self.assertIsNone(jobs[2]['condicao'])


class TestSemantica(unittest.TestCase):
    def test_job_duplicado_aborta(self):
        src = 'job backup\n  EVERY 1h\n  RUN "x"\njob backup\n  AT 08:00\n  RUN "y"'
        with self.assertRaises(SystemExit):
            parse(src)

    def test_intervalo_zero_aborta(self):
        with self.assertRaises(SystemExit):
            parse('job x\n  EVERY 0h\n  RUN "echo"')

    def test_horario_hora_invalida_aborta(self):
        with self.assertRaises(SystemExit):
            parse('job x\n  AT 24:30\n  RUN "echo"')

    def test_threshold_acima_de_100_aborta(self):
        with self.assertRaises(SystemExit):
            parse('job x\n  EVERY 1m\n  IF cpu > 150\n  RUN "echo"')

    def test_threshold_no_limite_passa(self):
        jobs = parse('job x\n  EVERY 1m\n  IF cpu > 100\n  RUN "echo"')
        self.assertEqual(len(jobs), 1)

    def test_run_vazio_emite_aviso(self):
        # Aviso não aborta — job é registrado normalmente
        jobs = parse('job health_check\n  EVERY 1m\n  RUN ""')
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['comando'], '')


if __name__ == '__main__':
    unittest.main()
