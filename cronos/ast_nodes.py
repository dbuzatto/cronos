"""
ast_nodes.py - Nós da Árvore Sintática Abstrata (AST) da Cronos DSL

Cada classe representa uma construção da linguagem.
Usamos dataclasses porque evita escrever __init__ na mão pra cada nó.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Program:
    """Raiz da AST — contém todos os jobs declarados no arquivo."""
    jobs: list  # lista de JobDecl


@dataclass
class JobDecl:
    """Declaração completa de um job: nome + agendamento + condição opcional + comando."""
    name: str
    schedule: object            # ScheduleEvery ou ScheduleAt
    condition: Optional[object] # Condition ou None (cláusula IF é opcional)
    run: object                 # RunClause


@dataclass
class ScheduleEvery:
    """Agendamento por intervalo de tempo: EVERY 5m, EVERY 1h, etc."""
    amount: int
    unit: str  # 's' = segundos, 'm' = minutos, 'h' = horas, 'd' = dias


@dataclass
class ScheduleAt:
    """Agendamento por horário fixo diário: AT 08:00."""
    time: str  # formato HH:MM


@dataclass
class Condition:
    """Condição de execução baseada em métrica do sistema: IF disk > 80."""
    metric: str      # 'disk', 'cpu' ou 'memory'
    comparator: str  # '>', '<', '>=', '<=' ou '=='
    value: int       # limite numérico (percentual 0-100)


@dataclass
class RunClause:
    """Comando shell a ser executado quando o job disparar: RUN "comando"."""
    command: str
