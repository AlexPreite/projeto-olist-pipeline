# Projeto Olist: pipeline de dados completo

Este manual explica o projeto do início ao fim: o objetivo, a arquitetura, as
ferramentas, o que foi construído, como executar cada etapa e como conferir se
os resultados estão corretos. O projeto acompanha o curso
[pipeline-olist](https://ckoliveiraa.github.io/pipeline-olist/), mas usa **Poetry**
no lugar de `uv`, porque o projeto original já estava configurado dessa forma.

## 1. Objetivo

Transformar os nove arquivos públicos do e-commerce brasileiro da Olist em:

1. dados brutos preservados;
2. tabelas tipadas e confiáveis;
3. indicadores SQL prontos para consumo;
4. um dashboard local em Streamlit.

O pipeline é local. Não há servidor, nuvem ou banco para instalar: o banco
DuckDB é o arquivo `olist.duckdb`.

## 2. Arquitetura

```text
raw/*.csv.gz
    |
    | pipeline.ingestao
    v
olist.duckdb
    raw.*              cópia fiel: texto, nulos e colunas originais
    |
    | pipeline.transformacao
    v
    refined.*          tipos confiáveis: datas, números e nomes em português
    |
    | pipeline.marts + sql/marts/*.sql
    v
    marts.*             uma tabela por pergunta de negócio
    |
    | app.py
    v
dashboard Streamlit
```

O arquivo `ui.py` é uma ferramenta auxiliar para explorar o banco no navegador.
Ele não faz parte da sequência de transformação.

### Grão das principais tabelas

- `refined.pedidos`: uma linha por pedido.
- `refined.itens_pedido`: uma linha por item de pedido.
- `refined.pagamentos`: uma linha por parcela ou pagamento.
- `refined.avaliacoes`: uma linha por avaliação do pedido.
- `refined.clientes`: um cliente Olist por pedido; a pessoa real é
  `cliente_unico_id`.
- `refined.produtos`: uma linha por produto.

Esse grão precisa ser conhecido antes de qualquer `JOIN`. Por exemplo, juntar
pedido com item repete o pedido uma vez por item; para contar pedidos nesse
resultado, use `count(DISTINCT pedido_id)`.

## 3. Ferramentas utilizadas

### Python 3.13

É a linguagem do pipeline. A versão do projeto está registrada em
`.python-version`.

```powershell
poetry run python --version
```

### Poetry

O Poetry cria o ambiente virtual local em `.venv`, registra as dependências no
`pyproject.toml` e fixa versões no `poetry.lock`.

```powershell
poetry install
poetry env info
poetry add nome-da-biblioteca
poetry remove nome-da-biblioteca
```

Nunca instale as dependências do projeto globalmente. Use sempre `poetry run`.

### DuckDB

Banco analítico que funciona em um único arquivo. É usado para armazenar as
camadas `raw`, `refined` e `marts`, executar SQL e servir a interface web.

O DuckDB **não é SQLite**. Portanto, as extensões SQLite do VS Code instaladas
anteriormente não abrem o arquivo `olist.duckdb` como se ele fosse `.sqlite`.
Para este projeto, use `ui.py` ou o comando Python abaixo:

```powershell
poetry run python -c "import duckdb; print(duckdb.connect('olist.duckdb', read_only=True).sql('SHOW TABLES'))"
```

### Pandas

Lê os arquivos `.csv.gz` na ingestão. As colunas são carregadas como texto para
não perder zeros à esquerda de CEPs nem alterar valores antes da transformação.

### Streamlit

Transforma `app.py` em uma aplicação web local:

```powershell
poetry run streamlit run app.py
```

O navegador abrirá normalmente em `http://localhost:8501`.

### Ruff

Verificador rápido de estilo e erros comuns:

```powershell
poetry run ruff check pipeline ui.py app.py tests
```

### Pytest

Executa os testes automatizados:

```powershell
poetry run pytest
```

### Extensões do VS Code

As extensões instaladas para apoio ao desenvolvimento foram:

- `alexcvzz.vscode-sqlite`: exploração de arquivos SQLite;
- `qwtel.sqlite-viewer`: visualização de SQLite;
- `mtxr.sqltools`: consultas SQL;
- `mtxr.sqltools-driver-sqlite`: driver SQLite do SQLTools;
- Python, Pylance e Jupyter.

Elas são úteis para bancos SQLite, mas o banco deste curso é DuckDB. Para
DuckDB, o `ui.py` é a opção correta.

## 4. Instalação do projeto

Abra o PowerShell na pasta:

```powershell
cd "C:\Users\alexp\OneDrive\Documentos\Projeto_Python"
```

Instale as dependências:

```powershell
poetry install
```

Confirme o ambiente:

```powershell
poetry run python --version
poetry run python -c "import duckdb, pandas, streamlit"
```

## 5. Dados de origem

A pasta `raw/` contém os nove arquivos comprimidos:

- `olist_orders_dataset.csv.gz`
- `olist_order_items_dataset.csv.gz`
- `olist_order_payments_dataset.csv.gz`
- `olist_order_reviews_dataset.csv.gz`
- `olist_customers_dataset.csv.gz`
- `olist_sellers_dataset.csv.gz`
- `olist_products_dataset.csv.gz`
- `product_category_name_translation.csv.gz`
- `olist_geolocation_dataset.csv.gz`

Não edite esses arquivos. Eles são a fonte original e devem continuar
reprodutíveis. O pipeline lê gzip diretamente; não é necessário descompactar.

## 6. Execução completa

Execute os comandos na ordem abaixo. Não deixe `ui.py` ou outra conexão de
escrita aberta enquanto o pipeline estiver rodando.

### 6.1 Ingestão

```powershell
poetry run python -m pipeline.ingestao
```

Resultado esperado:

```text
raw.pedidos                 99.441
raw.itens_pedido           112.650
raw.pagamentos             103.886
raw.avaliacoes              99.224
raw.clientes                99.441
raw.vendedores               3.095
raw.produtos                32.951
raw.traducao_categorias         71
raw.geolocalizacao        1.000.163
TOTAL                    1.550.922
```

O script valida os nove arquivos antes de abrir o banco. Se um arquivo faltar,
ele para sem fazer ingestão parcial.

### 6.2 Transformação

```powershell
poetry run python -m pipeline.transformacao
```

O resultado esperado é `550.759` linhas no total das oito tabelas `refined`.
A geolocalização permanece em `raw` para o desafio de modelagem do curso.

Aqui acontece a mudança de tipo:

- datas: `TIMESTAMP`;
- preços, fretes e valores: `DECIMAL`;
- contagens: `INTEGER`;
- CEPs e identificadores: `VARCHAR`.

### 6.3 Marts

```powershell
poetry run python -m pipeline.marts
```

Os dez arquivos em `sql/marts/` são executados em ordem. Cada SQL recria sua
tabela, por isso executar novamente não duplica dados.

| Mart | Pergunta |
| --- | --- |
| `vendas_mensais` | Como receita e pedidos evoluem por mês? |
| `top_categorias` | Quais categorias geram mais receita? |
| `entrega_no_prazo` | Qual percentual foi entregue no prazo? |
| `nota_por_categoria` | Como a satisfação varia por categoria? |
| `recompra` | Quantos pedidos cada pessoa fez? |
| `ticket_medio_por_estado` | Qual o ticket médio por UF? |
| `mix_pagamento` | Como os pagamentos se distribuem? |
| `nota_por_prazo` | Atraso está associado a notas menores? |
| `vendedores_pareto` | Quanto da receita está concentrado nos vendedores? |
| `tempo_entrega_por_estado` | Quanto tempo cada estado espera? |

### 6.4 Dashboard

```powershell
poetry run streamlit run app.py
```

O dashboard lê o banco em modo somente leitura e apresenta cartões, série
mensal, categorias, estados, formas de pagamento e Pareto de vendedores.

### 6.5 Interface SQL do DuckDB

```powershell
poetry run python ui.py
```

Abra `http://localhost:4213`. Exemplos de consultas:

```sql
SELECT * FROM raw.pedidos LIMIT 5;
DESCRIBE refined.pedidos;
SELECT * FROM marts.vendas_mensais ORDER BY mes;
```

Encerre com `Ctrl+C` antes de executar qualquer etapa que escreva no banco.

## 7. Testes e conferências

Execute:

```powershell
poetry run pytest
```

Os testes confirmam que:

- as camadas existem;
- as contagens de `raw` e `refined` estão preservadas;
- todas as colunas de `raw` são `VARCHAR`;
- o mart principal não está vazio.

Verificações manuais úteis:

```powershell
poetry run ruff check pipeline ui.py app.py tests
poetry run python -m compileall pipeline ui.py app.py tests
```

Uma ingestão repetida deve produzir a mesma saída. Essa propriedade é chamada
de idempotência e permite recuperar o projeto sem medo depois de um erro.

## 8. Arquivos do projeto

```text
Projeto_Python/
├── raw/                         fonte original, não editar
├── pipeline/
│   ├── db.py                    conexão e gravação DuckDB
│   ├── ingestao.py              CSV → raw
│   ├── transformacao.py         raw → refined
│   └── marts.py                 executor dos SQLs
├── sql/marts/                   dez consultas analíticas
├── tests/test_pipeline.py       testes de contrato
├── app.py                       dashboard Streamlit
├── ui.py                        DuckDB UI
├── indicadores.md               perguntas de negócio e fontes
├── olist.duckdb                 banco local gerado
├── pyproject.toml               dependências e configuração
├── poetry.lock                  versões fixadas
└── MANUAL.md                   este manual
```

## 9. Como o projeto foi desenvolvido

1. Foi conferida a estrutura inicial e preservado o Poetry já existente.
2. Foram instalados DuckDB, Pandas, Streamlit, Pytest e Ruff pelo Poetry.
3. Os dados oficiais do repositório do curso foram colocados em `raw/`.
4. A ingestão foi criada com caminhos absolutos baseados no arquivo Python,
   leitura UTF-8, gzip direto, tipos texto e recriação das tabelas.
5. A transformação foi criada com SQL explícito, sem inferência silenciosa de
   tipos e com oito tabelas confiáveis.
6. Os indicadores foram registrados em `indicadores.md` antes dos marts.
7. Cada mart foi escrito em um arquivo SQL separado e executado pelo Python.
8. O dashboard foi criado somente depois que os marts estavam disponíveis.
9. O lint, a compilação, a execução real e a reexecução foram conferidos.

## 10. Problemas comuns

### `Could not set lock on file`

O `ui.py`, o dashboard ou outro processo ainda está usando o banco. Feche-o
com `Ctrl+C` e rode o pipeline novamente.

O dashboard e o `ui.py` não devem ficar abertos ao mesmo tempo: o `ui.py`
mantém uma conexão viva para servir o navegador e pode impedir a conexão do
dashboard. Depois de encerrar o `ui.py`, atualize a página do Streamlit.

### Banco não encontrado no dashboard

Execute, nesta ordem:

```powershell
poetry run python -m pipeline.ingestao
poetry run python -m pipeline.transformacao
poetry run python -m pipeline.marts
```

### O SQLite Viewer não abre `olist.duckdb`

Isso é esperado: SQLite e DuckDB são formatos diferentes. Use `ui.py`,
DuckDB pelo terminal ou um cliente que tenha suporte explícito a DuckDB.

### O terminal mostra acentos estranhos

Os scripts reconfiguram a saída para UTF-8. Se o problema for do terminal,
execute o PowerShell em uma sessão nova e confira a fonte/encoding do console.

## 11. Próximas evoluções

- criar testes de qualidade para chaves primárias e estrangeiras;
- decidir uma modelagem para `raw.geolocalizacao`;
- adicionar filtros de período ao dashboard;
- incluir os indicadores 08 e 10 em uma segunda página;
- publicar o repositório somente depois de remover arquivos locais gerados,
  conforme a política de versionamento escolhida.
