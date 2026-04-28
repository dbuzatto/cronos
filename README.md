# Cronos — DSL para Orquestração de Tarefas Agendadas

Cronos é uma linguagem de domínio específico (DSL) interpretada para orquestração de tarefas agendadas com suporte a condições baseadas em métricas do sistema. Um programa `.cronos` é compilado para um script Python executável.

> Trabalho acadêmico — Engenharia de Computação, FHO – Fundação Herminio Ometto  
> Diogo Buzatto (RA: 111809) · Lucas Ferreira (RA: 111519)

---

## Por que Cronos?

Ferramentas como `cron` e `systemd timers` não permitem condicionar a execução de tarefas ao estado atual do sistema (uso de disco, CPU, memória) sem scripts auxiliares externos. Cronos resolve isso com uma sintaxe declarativa simples:

```cronos
job backup
  EVERY 1h
  IF disk > 80
  RUN "tar -czf /tmp/backup.tar.gz /data"
```

Em vez de:

```bash
# crontab + script auxiliar
0 * * * * /bin/bash -c 'if [ $(df / | tail -1 | awk "{print \$5}" | tr -d "%") -gt 80 ]; then tar -czf /tmp/backup.tar.gz /data; fi'
```

---

## Sintaxe da Linguagem

### Estrutura de um job

```
job <nome>
  <agendamento>
  [condição]
  <comando>
```

- **`<nome>`** — identificador único do job (`backup`, `health_check`, `limpar_logs`, etc.)
- **`<agendamento>`** — quando executar (obrigatório)
- **`[condição]`** — métrica do sistema que precisa ser satisfeita (opcional)
- **`<comando>`** — comando shell entre aspas (obrigatório)

---

### Agendamento

| Sintaxe | Descrição |
|---|---|
| `EVERY <n>s` | A cada N segundos |
| `EVERY <n>m` | A cada N minutos |
| `EVERY <n>h` | A cada N horas |
| `EVERY <n>d` | A cada N dias |
| `AT HH:MM` | Todo dia no horário especificado |

```cronos
job ping
  EVERY 30s
  RUN "curl http://localhost/health"

job relatorio
  AT 23:00
  RUN "python3 gerar_relatorio.py"
```

---

### Condição (opcional)

```
IF <métrica> <comparador> <valor>
```

| Métrica | O que mede |
|---|---|
| `disk` | Uso do disco raiz (%) |
| `cpu` | Uso de CPU (%) |
| `memory` | Uso de memória RAM (%) |

| Comparador | Significado |
|---|---|
| `>` | maior que |
| `<` | menor que |
| `>=` | maior ou igual |
| `<=` | menor ou igual |
| `==` | igual a |

```cronos
job backup
  EVERY 1h
  IF disk > 80
  RUN "rsync -av /dados /backup"
```

Se a condição não for satisfeita, o job é **pulado silenciosamente** naquele ciclo.

---

### Comentários

Comentários começam com `#` e vão até o fim da linha:

```cronos
# Isso é um comentário
job health_check
  AT 08:00
  # Verifica se o serviço está respondendo
  RUN "curl -f http://localhost/health"
```

---

### Exemplo completo

```cronos
# Backup condicional — só se disco estiver acima de 70%
job backup_incremental
  EVERY 6h
  IF disk > 70
  RUN "rsync -av /dados /backup"

# Health check diário sem condição
job health_check
  AT 08:00
  RUN "curl -f http://localhost/health"

# Limpeza noturna de temporários
job limpeza
  AT 03:00
  RUN "find /tmp -mtime +7 -delete"
```

---

## Gramática Formal (EBNF)

```ebnf
program         ::= job_decl+
job_decl        ::= JOB IDENTIFIER schedule_clause condition_clause? run_clause
schedule_clause ::= EVERY DURATION | AT TIME
DURATION        ::= INTEGER ( s | m | h | d )
TIME            ::= [0-2][0-9]:[0-5][0-9]
condition_clause::= IF metric comparator INTEGER
metric          ::= disk | cpu | memory
comparator      ::= ">" | "<" | ">=" | "<=" | "=="
run_clause      ::= RUN STRING
IDENTIFIER      ::= [a-zA-Z_][a-zA-Z0-9_]*
INTEGER         ::= [0-9]+
STRING          ::= '"' .* '"'
```

---

## Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip

### Passos

```bash
# Clone o repositório
git clone <url-do-repo>
cd cronos

# Crie um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Instale as dependências
pip install -r requirements.txt
```

---

## Como Usar

### 1. Escreva um arquivo `.cronos`

```cronos
# meus_jobs.cronos
job backup
  EVERY 1h
  IF disk > 80
  RUN "tar -czf /tmp/backup.tar.gz /data"
```

### 2. Compile para Python

```bash
python main.py meus_jobs.cronos
# Saída: meus_jobs.py
```

Ou especifique o arquivo de saída:

```bash
python main.py meus_jobs.cronos agendador.py
```

### 3. Execute o script gerado

```bash
python meus_jobs.py
```

O processo fica rodando em loop, verificando e executando os jobs conforme o agendamento.

---

## Exemplos Prontos

```bash
# Exemplo básico (do artigo)
python main.py examples/exemplo_basico.cronos
python examples/exemplo_basico.py

# Exemplo com todos os recursos
python main.py examples/exemplo_completo.cronos
python examples/exemplo_completo.py
```

---

## Arquitetura

Cronos segue a arquitetura clássica de compiladores em três fases:

```
arquivo.cronos
      │
      ▼
┌─────────────┐
│   lexer.py  │  Análise léxica: texto → tokens
└──────┬──────┘
       │ tokens
       ▼
┌─────────────┐
│  parser.py  │  Análise sintática: tokens → AST (LALR(1) via PLY)
└──────┬──────┘
       │ AST
       ▼
┌─────────────┐
│  codegen.py │  Geração de código: AST → script Python
└──────┬──────┘
       │
       ▼
   arquivo.py   ← script executável com schedule + psutil
```

### Módulos

| Arquivo | Responsabilidade |
|---|---|
| `cronos/ast_nodes.py` | Dataclasses que representam os nós da AST |
| `cronos/lexer.py` | Analisador léxico (tokenizador) usando PLY lex |
| `cronos/parser.py` | Analisador sintático LALR(1) usando PLY yacc |
| `cronos/codegen.py` | Gerador de código Python a partir da AST |
| `main.py` | CLI que orquestra o pipeline completo |

---

## Testes

```bash
# Rodar todos os testes
python -m unittest discover tests/

# Rodar um módulo específico
python -m unittest tests/test_lexer.py
python -m unittest tests/test_parser.py
python -m unittest tests/test_codegen.py
```

### Cobertura dos testes

| Módulo | O que é testado |
|---|---|
| `test_lexer.py` | Palavras-chave, literais (DURATION, TIME, INTEGER, STRING), comparadores, comentários |
| `test_parser.py` | AST gerada para jobs com/sem condição, todos os comparadores e métricas, múltiplos jobs |
| `test_codegen.py` | Imports, loop principal, chamadas de schedule, funções geradas, condições com psutil |

---

## Estrutura do Projeto

```
cronos/
├── main.py                    # CLI: entry point do compilador
├── requirements.txt           # Dependências (ply, schedule, psutil)
├── cronos/
│   ├── __init__.py
│   ├── ast_nodes.py           # Nós da árvore sintática abstrata
│   ├── lexer.py               # Analisador léxico (PLY lex)
│   ├── parser.py              # Analisador sintático (PLY yacc, LALR(1))
│   └── codegen.py             # Gerador de código Python
├── examples/
│   ├── exemplo_basico.cronos  # Exemplo do artigo
│   └── exemplo_completo.cronos# Todos os recursos da linguagem
└── tests/
    ├── test_lexer.py
    ├── test_parser.py
    └── test_codegen.py
```

---

## Tecnologias

| Biblioteca | Versão | Uso |
|---|---|---|
| [PLY](https://github.com/dabeaz/ply) | 3.11 | Lexer e parser (lex + yacc) |
| [schedule](https://github.com/dbader/schedule) | 1.2.2 | Agendamento no script gerado |
| [psutil](https://github.com/giampaolo/psutil) | 6.1.0 | Coleta de métricas no script gerado |

---

## Autores

- **Diogo Buzatto** — RA: 111809
- **Lucas Ferreira** — RA: 111519

Engenharia de Computação — FHO – Fundação Herminio Ometto, Araras, Brasil
