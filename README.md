# Projeto Olist Pipeline

Pipeline de dados do e-commerce brasileiro da Olist, desenvolvido com Python,
DuckDB, Pandas, SQL e Streamlit.

O projeto transforma os arquivos brutos da Olist em tabelas confiáveis,
indicadores analíticos e um dashboard local.

## Visão geral

```text
raw/*.csv.gz
    ↓ pipeline.ingestao
olist.duckdb · raw.*
    ↓ pipeline.transformacao
olist.duckdb · refined.*
    ↓ pipeline.marts
olist.duckdb · marts.*
    ↓ app.py
Dashboard Streamlit
```

### Camadas

- **raw**: cópia fiel dos arquivos de origem. Os dados entram como texto,
  sem conversão ou limpeza.
- **refined**: dados tipados, com datas, valores e identificadores tratados.
- **marts**: tabelas agregadas para responder perguntas de negócio.
- **dashboard**: visualização dos indicadores com Streamlit.

## Requisitos

- Python 3.13
- Poetry
- Git

O projeto usa o Poetry para criar o ambiente virtual e controlar as
dependências.

## Instalação

```powershell
git clone https://github.com/AlexPreite/projeto-olist-pipeline.git
cd projeto-olist-pipeline
poetry install
```

Confirme o ambiente:

```powershell
poetry run python --version
poetry run python -c "import duckdb, pandas, streamlit"
```

## Dados da Olist

Os arquivos de dados não são versionados no GitHub porque ocupam espaço e são
gerados fora do código. A pasta `raw/` deve conter estes nove arquivos:

- `olist_orders_dataset.csv.gz`
- `olist_order_items_dataset.csv.gz`
- `olist_order_payments_dataset.csv.gz`
- `olist_order_reviews_dataset.csv.gz`
- `olist_customers_dataset.csv.gz`
- `olist_sellers_dataset.csv.gz`
- `olist_products_dataset.csv.gz`
- `product_category_name_translation.csv.gz`
- `olist_geolocation_dataset.csv.gz`

Os dados podem ser obtidos no repositório do curso:

```powershell
git clone --depth 1 https://github.com/ckoliveiraa/pipeline-olist.git dados-curso
Move-Item .\dados-curso\raw .\raw
Remove-Item .\dados-curso -Recurse -Force
```

Não descompacte os arquivos `.csv.gz` e não edite o conteúdo da pasta `raw/`.

## Executar o pipeline

Execute os comandos na ordem:

### 1. Ingestão

```powershell
poetry run python -m pipeline.ingestao
```

Lê os nove arquivos e cria o schema `raw` no arquivo `olist.duckdb`.
A execução esperada totaliza **1.550.922 registros**.

### 2. Transformação

```powershell
poetry run python -m pipeline.transformacao
```

Converte os dados de `raw` em oito tabelas no schema `refined`.
Datas, valores monetários e contagens recebem tipos apropriados.

### 3. Marts

```powershell
poetry run python -m pipeline.marts
```

Executa os dez arquivos SQL em [sql/marts](sql/marts) e recria as tabelas
analíticas no schema `marts`.

## Dashboard

Depois de executar o pipeline:

```powershell
poetry run streamlit run app.py
```

Abra [http://localhost:8501](http://localhost:8501).

O dashboard apresenta:

- receita e pedidos;
- percentual de entregas no prazo;
- nota média;
- tempo médio de entrega;
- recompra;
- receita mensal;
- receita por categoria;
- ticket médio por estado;
- mix de pagamentos;
- concentração de receita por vendedor.

## Explorar o banco com SQL

O projeto inclui uma interface web do DuckDB:

```powershell
poetry run python ui.py
```

Abra [http://localhost:4213](http://localhost:4213).

Exemplos de consultas:

```sql
SELECT * FROM raw.pedidos LIMIT 5;

DESCRIBE refined.pedidos;

SELECT * FROM marts.vendas_mensais ORDER BY mes;
```

### Importante: DuckDB não é SQLite

O arquivo `olist.duckdb` usa o formato DuckDB. As extensões SQLite do VS Code
não são o visualizador adequado para esse arquivo. Use `ui.py`, o terminal
DuckDB ou outra ferramenta com suporte explícito a DuckDB.

Não deixe o `ui.py` e o dashboard abertos ao mesmo tempo, pois ambos mantêm
conexões com o banco.

## Testes e qualidade

Executar os testes:

```powershell
poetry run pytest
```

Executar o lint:

```powershell
poetry run ruff check pipeline ui.py app.py tests
```

Validar a sintaxe:

```powershell
poetry run python -m compileall pipeline ui.py app.py tests
```

Os testes verificam a existência das camadas, a preservação das contagens,
os tipos da camada `raw` e a presença de dados nos marts.

O GitHub Actions executa automaticamente, em cada push e pull request:

1. instalação das dependências;
2. obtenção dos dados de teste;
3. ingestão, transformação e marts;
4. Ruff;
5. suíte completa de testes de qualidade.

## Estrutura do projeto

```text
.
├── pipeline/
│   ├── db.py
│   ├── ingestao.py
│   ├── transformacao.py
│   └── marts.py
├── sql/
│   └── marts/
├── tests/
│   └── test_pipeline.py
├── app.py
├── ui.py
├── indicadores.md
├── MANUAL.md
├── pyproject.toml
├── poetry.lock
└── .gitignore
```

## Documentação completa

Consulte o [MANUAL.md](MANUAL.md) para explicações detalhadas sobre:

- arquitetura do pipeline;
- ferramentas utilizadas;
- decisões de modelagem;
- funcionamento de cada camada;
- comandos completos;
- problemas comuns;
- processo de desenvolvimento.

## Fonte dos dados

Brazilian E-Commerce Public Dataset by Olist:

<https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce>

O material do curso está disponível em:

<https://ckoliveiraa.github.io/pipeline-olist/>

## Licença dos dados

Os dados originais da Olist são distribuídos sob a licença indicada na fonte
original. Consulte os termos do dataset antes de redistribuí-los.
