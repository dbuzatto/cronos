"""
parser.py - Analisador sintático da Cronos DSL

Usa PLY com parser LALR(1) pra verificar a gramática e construir a AST.
Cada função p_* define uma produção — p[0] é o lado esquerdo, p[1..n] o direito.

Gramática resumida (EBNF):
  program        ::= job_decl+
  job_decl       ::= JOB IDENTIFIER schedule_clause condition_clause? run_clause
  schedule_clause::= EVERY DURATION | AT TIME
  condition_clause::= IF metric comparator INTEGER
  metric         ::= disk | cpu | memory
  comparator     ::= '>' | '<' | '>=' | '<=' | '=='
  run_clause     ::= RUN STRING
"""

import os
import logging

import ply.yacc as yacc

# O PLY exige que 'tokens' esteja no namespace do módulo onde yacc.yacc() é chamado
from cronos.lexer import tokens  # noqa: F401
from cronos.ast_nodes import (
    Program, JobDecl,
    ScheduleEvery, ScheduleAt,
    Condition, RunClause,
)

# Logger silencioso pra evitar spam do PLY no terminal durante os testes
_quiet_log = logging.getLogger('cronos.parser')
_quiet_log.addHandler(logging.NullHandler())


# --- Regras da gramática ---

def p_program(p):
    '''program : job_list'''
    p[0] = Program(jobs=p[1])


def p_job_list_multiple(p):
    '''job_list : job_list job_decl'''
    # Left-recursive: vai acumulando jobs na lista conforme o parser avança
    p[0] = p[1] + [p[2]]


def p_job_list_single(p):
    '''job_list : job_decl'''
    p[0] = [p[1]]


def p_job_decl_with_condition(p):
    '''job_decl : JOB IDENTIFIER schedule_clause condition_clause run_clause'''
    p[0] = JobDecl(name=p[2], schedule=p[3], condition=p[4], run=p[5])


def p_job_decl_without_condition(p):
    '''job_decl : JOB IDENTIFIER schedule_clause run_clause'''
    # Cláusula IF é opcional — sem ela, condition fica None
    p[0] = JobDecl(name=p[2], schedule=p[3], condition=None, run=p[4])


def p_schedule_every(p):
    '''schedule_clause : EVERY DURATION'''
    amount, unit = p[2]
    p[0] = ScheduleEvery(amount=amount, unit=unit)


def p_schedule_at(p):
    '''schedule_clause : AT TIME'''
    p[0] = ScheduleAt(time=p[2])


def p_condition(p):
    '''condition_clause : IF metric comparator INTEGER'''
    p[0] = Condition(metric=p[2], comparator=p[3], value=p[4])


def p_metric(p):
    '''metric : DISK
              | CPU
              | MEMORY'''
    # Normaliza pra lowercase — o codegen espera 'disk', 'cpu', 'memory'
    p[0] = p[1].lower()


def p_comparator(p):
    '''comparator : GTE
                  | LTE
                  | EQ
                  | GT
                  | LT'''
    p[0] = p[1]


def p_run_clause(p):
    '''run_clause : RUN STRING'''
    p[0] = RunClause(command=p[2])


def p_error(p):
    if p:
        print(f"[Parser] Erro de sintaxe: token inesperado '{p.value}' "
              f"(tipo: {p.type}) na linha {p.lineno}")
    else:
        print("[Parser] Erro de sintaxe: fim de arquivo inesperado")


def build_parser(**kwargs):
    """Constrói e retorna o parser LALR(1) do PLY.

    O parsetab.py (tabela cacheada do parser) é salvo no diretório do pacote
    e está no .gitignore — é gerado automaticamente na primeira execução.
    """
    defaults = {
        'outputdir': os.path.dirname(os.path.abspath(__file__)),
        'debug': False,
        'errorlog': _quiet_log,
    }
    defaults.update(kwargs)
    return yacc.yacc(**defaults)
