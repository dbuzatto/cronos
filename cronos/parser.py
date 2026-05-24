import sys
import time
import subprocess

import ply.yacc as yacc
import schedule
import psutil

from cronos.lexer import tokens  # noqa: F401

# Tabela de símbolos
tabela_simbolos = {}

# Lista de jobs acumulados durante o parse
lista_jobs = []


def insere_simbolo(nome, linha):
    global tabela_simbolos
    if nome in tabela_simbolos:
        linha_anterior = tabela_simbolos[nome]
        print(f"Erro: Job '{nome}' ja foi declarado na linha {linha_anterior}.")
        sys.exit(1)
    tabela_simbolos[nome] = linha


def valida_intervalo(amount, unit):
    if amount <= 0:
        print(f"Erro: Intervalo de agendamento deve ser maior que zero. Encontrado: EVERY {amount}{unit}")
        sys.exit(1)


def valida_horario(time_str):
    hora, minuto = time_str.split(':')
    if int(hora) > 23:
        print(f"Erro: Horario '{time_str}' invalido. Horas devem estar entre 00 e 23.")
        sys.exit(1)
    if int(minuto) > 59:
        print(f"Erro: Horario '{time_str}' invalido. Minutos devem estar entre 00 e 59.")
        sys.exit(1)


def valida_threshold(metrica, valor):
    if valor < 0 or valor > 100:
        print(f"Erro: Threshold {valor} fora do intervalo valido [0, 100] para a metrica '{metrica}'.")
        sys.exit(1)


UNIDADES = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days'}


def le_metrica(metrica):
    if metrica == 'disk':
        return psutil.disk_usage("/").percent
    if metrica == 'cpu':
        return psutil.cpu_percent(interval=1)
    if metrica == 'memory':
        return psutil.virtual_memory().percent


def compara(atual, op, valor):
    if op == '>':  return atual > valor
    if op == '<':  return atual < valor
    if op == '>=': return atual >= valor
    if op == '<=': return atual <= valor
    if op == '==': return atual == valor


def monta_funcao_job(comando, condicao):
    def executar():
        if condicao is not None:
            metrica, op, valor = condicao
            if not compara(le_metrica(metrica), op, valor):
                return
        subprocess.run(comando, shell=True)
    return executar


def processa_jobs():
    global lista_jobs
    for job in lista_jobs:
        func = monta_funcao_job(job['comando'], job['condicao'])
        agenda = job['agenda']
        if agenda[0] == 'every':
            _, amount, unit = agenda
            getattr(schedule.every(amount), UNIDADES[unit]).do(func)
        else:
            schedule.every().day.at(agenda[1]).do(func)


def executa_loop():
    while True:
        schedule.run_pending()
        time.sleep(1)


# <program> ::= <job_decl>+
def p_program(p):
    '''program : job_list'''
    pass

def p_job_list_multiple(p):
    '''job_list : job_list job_decl'''
    pass

def p_job_list_single(p):
    '''job_list : job_decl'''
    pass

# <job_decl> ::= JOB IDENTIFIER <schedule_clause> [<condition_clause>] <run_clause>
def p_job_decl_with_condition(p):
    '''job_decl : JOB IDENTIFIER schedule_clause condition_clause run_clause'''
    insere_simbolo(p[2], p.lineno(2))
    if p[5] == "":
        print(f"Aviso: Job '{p[2]}' possui comando RUN vazio.")
    lista_jobs.append({'nome': p[2], 'agenda': p[3], 'condicao': p[4], 'comando': p[5]})

def p_job_decl_without_condition(p):
    '''job_decl : JOB IDENTIFIER schedule_clause run_clause'''
    insere_simbolo(p[2], p.lineno(2))
    if p[4] == "":
        print(f"Aviso: Job '{p[2]}' possui comando RUN vazio.")
    lista_jobs.append({'nome': p[2], 'agenda': p[3], 'condicao': None, 'comando': p[4]})

# <schedule_clause> ::= EVERY DURATION | AT TIME
def p_schedule_every(p):
    '''schedule_clause : EVERY DURATION'''
    amount, unit = p[2]
    valida_intervalo(amount, unit)
    p[0] = ('every', amount, unit)

def p_schedule_at(p):
    '''schedule_clause : AT TIME'''
    valida_horario(p[2])
    p[0] = ('at', p[2])

# <condition_clause> ::= IF <metric> <comparator> INTEGER
def p_condition(p):
    '''condition_clause : IF metric comparator INTEGER'''
    valida_threshold(p[2], p[4])
    p[0] = (p[2], p[3], p[4])

# <metric> ::= disk | cpu | memory
def p_metric(p):
    '''metric : DISK
              | CPU
              | MEMORY'''
    p[0] = p[1].lower()

# <comparator> ::= > | < | >= | <= | ==
def p_comparator(p):
    '''comparator : GTE
                  | LTE
                  | EQ
                  | GT
                  | LT'''
    p[0] = p[1]

# <run_clause> ::= RUN STRING
def p_run_clause(p):
    '''run_clause : RUN STRING'''
    p[0] = p[2]


def p_error(p):
    if p:
        print(f"Erro de sintaxe na linha {p.lineno}, lexema '{p.value}' - tipo {p.type}")
    else:
        print("Fim de arquivo precoce")


def build_parser():
    tabela_simbolos.clear()
    lista_jobs.clear()
    return yacc.yacc(write_tables=False)
