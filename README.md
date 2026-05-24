# Cronos — DSL para Orquestração de Tarefas Agendadas

Cronos é uma linguagem de domínio específico (DSL) interpretada para orquestração de tarefas agendadas com suporte a condições baseadas em métricas do sistema. Um programa `.cronos` é lido, analisado e executado diretamente pelo interpretador.

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

## Análise Semântica

Além da análise sintática, o parser executa cinco verificações semânticas antes de registrar os jobs. Quatro abortam a execução com erro; uma é apenas aviso.

### 1. Unicidade de identificadores de job

Dois jobs com o mesmo nome geram erro. A tabela de símbolos guarda a linha da primeira declaração e a referencia na mensagem.

```
Erro: Job 'backup' ja foi declarado na linha 1.
```

### 2. Validade do intervalo em `EVERY`

O número em `EVERY <n><unidade>` precisa ser maior que zero. `EVERY 0h` seria um loop infinito imediato.

```
Erro: Intervalo de agendamento deve ser maior que zero. Encontrado: EVERY 0h
```

### 3. Validade do horário em `AT`

O lexer aceita `[0-2][0-9]:[0-5][0-9]`, o que permite `24:30` ou `29:00`. O verificador semântico garante hora `00-23` e minuto `00-59`.

```
Erro: Horario '24:30' invalido. Horas devem estar entre 00 e 23.
```

### 4. Threshold de métricas no intervalo `[0, 100]`

Como `disk`, `cpu` e `memory` são percentuais, valores fora de `0-100` são impossíveis na prática.

```
Erro: Threshold 150 fora do intervalo valido [0, 100] para a metrica 'cpu'.
```

### 5. Comando `RUN` não vazio

`RUN ""` é sintaticamente válido mas provavelmente engano do usuário. O parser apenas avisa e segue.

```
Aviso: Job 'health_check' possui comando RUN vazio.
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

### 2. Execute direto

```bash
python main.py meus_jobs.cronos
```

O interpretador faz o parse, registra os jobs no scheduler e fica em loop executando-os conforme o agendamento. Use `Ctrl+C` pra parar.

---

## Exemplos Prontos

```bash
# Exemplo básico (do artigo)
python main.py examples/exemplo_basico.cronos

# Exemplo com todos os recursos
python main.py examples/exemplo_completo.cronos
```

---

## Arquitetura

Cronos é um interpretador direto — o parser, durante a análise sintática, acumula os jobs em uma lista (`lista_jobs`); depois `processa_jobs()` registra todos no `schedule` e `executa_loop()` mantém o processo vivo:

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
│  parser.py  │  Análise sintática (LALR(1) via PLY) +
│             │  tabela de símbolos + acumula lista_jobs +
│             │  processa_jobs() registra no scheduler +
│             │  executa_loop() roda eternamente
└─────────────┘
```

### Módulos

| Arquivo | Responsabilidade |
|---|---|
| `cronos/lexer.py` | Analisador léxico (tokenizador) usando PLY lex |
| `cronos/parser.py` | Parser LALR(1) + tabela de símbolos + interpretação (registra e executa os jobs) |
| `main.py` | CLI que lê o arquivo, dispara o parse e a execução |

---

## Testes

```bash
# Rodar todos os testes
python -m unittest discover tests/

# Rodar um módulo específico
python -m unittest tests/test_lexer.py
python -m unittest tests/test_parser.py
```

### Cobertura dos testes

| Módulo | O que é testado |
|---|---|
| `test_lexer.py` | Palavras-chave, literais (DURATION, TIME, INTEGER, STRING), comparadores, comentários |
| `test_parser.py` | `lista_jobs` populada corretamente para jobs com/sem condição, todos os comparadores e métricas, múltiplos jobs, e as 5 verificações semânticas (duplicata, intervalo, horário, threshold, RUN vazio) |

---

## Estrutura do Projeto

```
cronos/
├── main.py                    # CLI: entry point do interpretador
├── requirements.txt           # Dependências (ply, schedule, psutil)
├── cronos/
│   ├── __init__.py
│   ├── lexer.py               # Analisador léxico (PLY lex)
│   └── parser.py              # Parser (PLY yacc, LALR(1)) + interpretador
├── examples/
│   ├── exemplo_basico.cronos  # Exemplo do artigo
│   ├── exemplo_completo.cronos# Todos os recursos da linguagem
│   └── exemplo_teste.cronos   # Teste rápido com intervalo curto
└── tests/
    ├── test_lexer.py
    └── test_parser.py
```

---

## Tecnologias

| Biblioteca | Versão | Uso |
|---|---|---|
| [PLY](https://github.com/dabeaz/ply) | 3.11 | Lexer e parser (lex + yacc) |
| [schedule](https://github.com/dbader/schedule) | 1.2.2 | Agendamento dos jobs em runtime |
| [psutil](https://github.com/giampaolo/psutil) | 6.1.0 | Coleta de métricas em runtime |

---

## Autores

- **Diogo Buzatto** — RA: 111809
- **Lucas Ferreira** — RA: 111519

Engenharia de Computação — FHO – Fundação Herminio Ometto, Araras, Brasil
