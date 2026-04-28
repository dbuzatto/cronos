"""
codegen.py - Gerador de código da Cronos DSL

Percorre a AST e produz um script Python executável.
O script gerado usa 'schedule' pra controlar o agendamento
e 'psutil' pra coletar as métricas do sistema em tempo de execução.
"""

from cronos.ast_nodes import ScheduleEvery, ScheduleAt

# Mapeia as unidades de tempo da Cronos pros métodos da biblioteca schedule
_UNIT_TO_SCHEDULE = {
    's': 'seconds',
    'm': 'minutes',
    'h': 'hours',
    'd': 'days',
}

# Mapeia as métricas da Cronos pras chamadas equivalentes do psutil
_METRIC_TO_PSUTIL = {
    'disk':   'psutil.disk_usage("/").percent',
    'cpu':    'psutil.cpu_percent(interval=1)',
    'memory': 'psutil.virtual_memory().percent',
}


def generate(program) -> str:
    """Ponto de entrada do codegen — recebe a AST raiz e retorna o script Python completo."""
    lines = []

    lines += _generate_header()
    lines.append('')

    # Uma função Python por job declarado
    for job in program.jobs:
        lines += _generate_job_function(job)
        lines.append('')

    # Registra cada job no scheduler com seu intervalo/horário
    lines.append('# Registra os jobs no scheduler conforme declarado no .cronos')
    for job in program.jobs:
        lines += _generate_schedule_call(job)

    lines.append('')
    lines += _generate_main_loop()

    return '\n'.join(lines)


def _generate_header() -> list:
    """Cabeçalho do script: aviso de geração automática + imports necessários."""
    return [
        '# Código gerado automaticamente pela Cronos DSL',
        '# Não edite este arquivo — edite o .cronos original e gere novamente',
        '',
        'import subprocess',
        'import schedule',
        'import time',
        'import psutil',
    ]


def _generate_job_function(job) -> list:
    """Gera a função Python que representa a lógica de execução de um job."""
    func_name = f'job_{job.name}'
    lines = [f'def {func_name}():']

    if job.condition:
        # Com condição: mede a métrica e decide se executa
        metric_expr = _METRIC_TO_PSUTIL[job.condition.metric]
        cmp = job.condition.comparator
        val = job.condition.value

        lines.append(f'    # Coleta a métrica e verifica a condição antes de executar')
        lines.append(f'    metric_value = {metric_expr}')
        lines.append(f'    if metric_value {cmp} {val}:')
        lines.append(f'        subprocess.run({repr(job.run.command)}, shell=True)')
        lines.append(f'    # Se a condição não for satisfeita, o job é pulado silenciosamente')
    else:
        # Sem condição: executa direto
        lines.append(f'    subprocess.run({repr(job.run.command)}, shell=True)')

    return lines


def _generate_schedule_call(job) -> list:
    """Gera a chamada schedule.every(...).do(...) correspondente ao agendamento do job."""
    func_name = f'job_{job.name}'

    if isinstance(job.schedule, ScheduleEvery):
        amount = job.schedule.amount
        unit = _UNIT_TO_SCHEDULE[job.schedule.unit]
        return [f'schedule.every({amount}).{unit}.do({func_name})']

    elif isinstance(job.schedule, ScheduleAt):
        time_str = job.schedule.time
        return [f'schedule.every().day.at("{time_str}").do({func_name})']

    # Não deve chegar aqui se o parser fez seu trabalho
    return [f'# ERRO: tipo de agendamento desconhecido para {func_name}']


def _generate_main_loop() -> list:
    """Gera o loop que mantém o processo rodando e dispara os jobs no tempo certo."""
    return [
        '# Loop principal — mantém o processo vivo e executa os jobs agendados',
        'while True:',
        '    schedule.run_pending()',
        '    time.sleep(1)',
    ]
