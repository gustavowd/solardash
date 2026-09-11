# SolarDash

Painel web de gestão energética da **UTFPR — Campus Pato Branco**, desenvolvido em Python com Streamlit. Centraliza a visualização da geração fotovoltaica, do consumo de energia, da demanda e das séries históricas dos equipamentos monitorados no campus.

O SolarDash consulta medições já armazenadas em PostgreSQL. A aquisição das leituras dos sensores, a comunicação com os equipamentos e a alimentação do banco são realizadas fora deste repositório.

## Funcionalidades

- Consulta da geração solar e do consumo em visualizações diárias, mensais e anuais.
- Agrupamento da geração por unidade consumidora e do consumo por transformador.
- Seleção de um ou mais dispositivos para análise conjunta.
- Consulta por variável de medição e intervalo de datas nas telas de equipamentos.
- Gráficos interativos de linhas, áreas e barras, com exploração dos valores ao longo do tempo.
- Exportação dos dados apresentados em CSV, com codificação UTF-8, separador `;` e vírgula decimal.
- Navegação lateral entre sete telas, com identidade visual compartilhada e adaptação a telas menores.

## Telas e equipamentos monitorados

| Tela | O que apresenta | Filtros principais |
| --- | --- | --- |
| Visão geral · geração | Curva diária de geração dos inversores e energia gerada por dia ou mês | Unidade consumidora, inversores e período Dia/Mês/Ano |
| Consumo consolidado | Curva diária dos medidores e energia consumida por dia ou mês | Transformador, medidores e período Dia/Mês/Ano |
| Inversores | Séries históricas das variáveis disponíveis para os inversores fotovoltaicos | Dispositivos, variável e intervalo de datas |
| Medidores | Séries históricas dos medidores de energia dos blocos e instalações | Dispositivos, variável e intervalo de datas |
| Demanda | Séries históricas dos medidores gerais, destinadas à análise da demanda e de outras variáveis disponíveis | Dispositivos, variável e intervalo de datas |
| Cargas | Séries históricas dos dispositivos cadastrados como cargas | Dispositivos, variável e intervalo de datas |
| Estação solarimétrica | Séries históricas das variáveis ambientais e solarimétricas cadastradas | Estações, variável e intervalo de datas |

A geração possui agrupamentos para `UTFPR-76942716`, `Politec-73134759`, `Area Ex.-88481328` e `Total`, com seleções predefinidas de inversores Huawei, Fronius e Solis. O consumo possui agrupamentos de `TRAFO 1` a `TRAFO 4`, além da opção `Total`. A estação selecionada inicialmente é `Station_Bib`.

Esses agrupamentos e nomes são específicos da instalação do campus e estão definidos no código.

## O que é medido e como os dados são apresentados

### Geração e consumo

| Visualização | Origem e tratamento dos dados | Unidade apresentada |
| --- | --- | --- |
| Geração diária | Média por minuto da medição de ID `0`, somada entre os inversores selecionados e dividida por 1.000 | kW |
| Geração mensal | Agregados diários de `picosdiariosinversores`, com consultas complementares à medição de ID `7` para o dia atual em determinados casos; divisão por 1.000 | kWh |
| Geração anual | Soma dos agregados de `picosdiariosinversores` por mês, dividida por 1.000 | kWh |
| Consumo diário | Média por minuto da medição de ID `27`, somada entre os medidores considerados | kW, conforme o rótulo atual do gráfico |
| Consumo mensal | Agregados de `picosdiariosmedidores` por dia, com consultas complementares à medição de ID `27` em determinados casos; divisão por 1.000 | kWh |
| Consumo anual | Soma dos agregados de `picosdiariosmedidores` por mês, dividida por 1.000.000 | MWh |

**kW representa potência; kWh e MWh representam energia acumulada.** Os gráficos diários ainda usam a palavra “energia” nos rótulos em kW. As unidades de origem e a interpretação física dos IDs devem ser conferidas no catálogo do banco, especialmente o ID `27`, utilizado tanto na curva diária quanto em consultas complementares do consumo mensal. As conversões acima descrevem o comportamento implementado.

### Variáveis dos equipamentos

Os nomes das variáveis vêm de `measurement_type.measurement_name`. O repositório não contém o catálogo completo das grandezas nem suas unidades; portanto, a disponibilidade de tensão, corrente, fator de potência, irradiância, temperatura ou outras grandezas depende do cadastro e das leituras existentes no banco.

A tela de inversores lista os primeiros 21 tipos de medição, ordenados pelo identificador. As demais telas montam o seletor de variáveis a partir de leituras de um dispositivo e de um intervalo histórico fixos:

| Tela | Dispositivo de referência | Intervalo consultado para listar variáveis |
| --- | --- | --- |
| Medidores | `3` | 09/05/2024, 08:00:01–08:00:15 |
| Demanda | `34` | 12/05/2026, 16:20:01–16:20:15 |
| Cargas | `41` | 06/04/2025, 20:00:01–20:00:15 |
| Estação solarimétrica | `32` | 09/05/2024, 08:00:01–08:00:15 |

Essas referências servem para descobrir as variáveis; as séries exibidas usam os dispositivos e as datas escolhidos pelo usuário. Na tela de demanda, valores da variável de ID `3` maiores ou iguais a `1` são limitados a `1` antes da exibição e exportação.

## Tecnologias

| Tecnologia | Uso |
| --- | --- |
| Python | Consultas, processamento e aplicação |
| Streamlit | Interface web, navegação, filtros e downloads |
| pandas | Organização, combinação e exportação das séries |
| Plotly Express | Gráficos interativos |
| SQLAlchemy e psycopg2 | Conexão com PostgreSQL |
| CSS | Personalização visual compartilhada |

A interface utiliza azul profundo, destaques em laranja e gráficos em cartões, com inspiração visual na proposta da SolarView PRO. A implementação atual utiliza o seletor nativo do Streamlit e não depende de `extra-streamlit-components`.

## Instalação e execução

### 1. Preparar o ambiente

É necessário Python com suporte à sintaxe `match` (3.10 ou superior), uma versão do Streamlit com `st.segmented_control` e acesso ao PostgreSQL da instalação. O ambiente utilizado nesta revisão possui Python 3.12 e Streamlit 1.63.0.

Na raiz do projeto, em Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install streamlit==1.63.0 pandas plotly sqlalchemy psycopg2-binary
```

### 2. Configurar a conexão

Crie `.streamlit/secrets.toml` com os dados de acesso ao banco:

```toml
[connections.my_database]
type = "sql"
dialect = "postgresql"
driver = "psycopg2"
host = "HOST_DO_BANCO"
port = 5432
database = "NOME_DO_BANCO"
username = "USUARIO"
password = "SENHA"
```

A aplicação usa `st.connection("my_database")`. O arquivo de credenciais está incluído no `.gitignore` e não deve ser versionado.

### 3. Iniciar o painel

Execute a partir da raiz do repositório:

```bash
streamlit run Totalizadores.py
```

Abra o endereço informado no terminal, normalmente `http://localhost:8501`. Use o menu lateral para acessar as demais telas; `Totalizadores.py` é o ponto de entrada da aplicação.

## Banco de dados esperado

O banco precisa estar criado e populado. Este repositório não fornece scripts de criação, migrações, dados de exemplo ou o processamento que produz os agregados diários.

| Tabela ou relação | Campos referenciados / finalidade |
| --- | --- |
| `devices` | `device_id`, `device_name`, `device_type`: cadastro dos equipamentos |
| `measurement_type` | `measurement_type_id`, `measurement_name`: catálogo de variáveis |
| `measurements` | `device_id`, `measurement_type_id`, `measurement_time`, `measurement_value`: leituras históricas |
| `time` | Dimensão temporal usada em junções para obter `day` |
| `picosdiariosinversores` | `device_id`, `year`, `month`, `day`, `pico`: agregados diários da geração |
| `picosdiariosmedidores` | `device_id`, `year`, `month`, `day`, `pico`: agregados diários do consumo |

Os tipos de equipamento usados em `devices.device_type` são:

| ID | Categoria |
| --- | --- |
| `1` | Inversores |
| `2` | Medidores |
| `3` | Medidores gerais / demanda |
| `4` | Estações solarimétricas |
| `5` | Cargas |

Essa relação documenta os campos acessados pela aplicação, não um esquema completo. As consultas usam recursos do PostgreSQL e junções `NATURAL JOIN`; o esquema existente precisa ser compatível com essas consultas.

## Como usar

1. Abra **Visão geral · geração** ou **Consumo consolidado** para consultar os totais agrupados.
2. Escolha **Dia**, **Mês** ou **Ano**. A visão diária usa a data atual do servidor; as demais permitem selecionar mês/ano ou ano.
3. Selecione a unidade consumidora ou o transformador e revise os dispositivos envolvidos. A opção `Total` do consumo possui consultas próprias de consolidação.
4. Para investigar um equipamento, abra sua categoria no menu, selecione os dispositivos, a variável e as duas datas do intervalo.
5. Explore o gráfico e utilize **Download de dados em CSV** para exportar a série processada.

## Estrutura do projeto

```text
solardash/
├── Totalizadores.py                  # Tela inicial e totalização da geração
├── ui.py                             # Navegação, cabeçalhos e estilo dos gráficos
├── assets/
│   └── theme.css                     # Estilos compartilhados e responsividade
├── pages/
│   ├── Cargas.py
│   ├── Estação Solarimétrica.py
│   ├── Inversores.py
│   ├── Medidores.py
│   ├── Medidores Gerais (Demanda).py
│   └── Totalizadores dos medidores.py
├── .streamlit/
│   ├── config.toml                   # Tema e configuração da navegação
│   └── secrets.toml                  # Credenciais locais, não versionadas
└── README.md
```

## Particularidades e limites atuais

- A disponibilidade e a atualização dos resultados dependem da coleta externa e dos agregados existentes no banco. Não há rotina de atualização periódica automática da interface implementada no projeto.
- Os seletores de ano dos totalizadores cobrem 2024–2030 e precisam ser revistos para uso fora desse intervalo.
- A visão diária de geração consulta de 05:00:01 a 19:59:59. A tela de inversores usa esses horários como limites inicial e final do intervalo selecionado. As outras categorias consultam de 00:00:01 a 23:59:59.
- As telas individuais subtraem três horas dos horários retornados. Os totalizadores não aplicam o mesmo ajuste no DataFrame; o fuso do banco e o do servidor devem ser considerados ao comparar telas.
- Nomes de equipamentos predefinidos e leituras históricas de referência precisam existir no banco. Sua ausência pode impedir a seleção ou provocar erros; o tratamento de bases vazias ainda não é uniforme.
- O CSV contém os dados após os tratamentos da tela, incluindo agregações, conversões e ajustes de horário, quando aplicáveis.
- O escopo atual é consulta, visualização e exportação CSV. Não há cadastro de equipamentos pela interface, controle remoto, alarmes automáticos, relatórios PDF ou cálculo financeiro implementados.

## Visão geral — Monitorar

A sidebar mantém as páginas individuais e pode ser recolhida ou reaberta pelo controle no canto superior esquerdo. A visão geral usa um cabeçalho compacto, com as abas Monitorar e Analisar. Analisar apresenta as variáveis individuais por equipamento na própria visão geral. As páginas anteriores continuam acessíveis na sidebar.

Em Monitorar, selecione uma data inicial e final (iguais para um único dia). À direita, ative Geração (inversores), Consumo (medidores) e Consumo geral (medidor geral do campus). Os seletores de equipamentos preservam os grupos por unidade consumidora e transformador. As séries podem aparecer simultaneamente e ser exportadas em CSV.

- Um dia: curvas de potência em kW, com médias por minuto somadas entre equipamentos.
- Vários dias: barras de energia em kWh, agrupáveis por dia, mês ou ano. Geração e consumo usam os agregados anteriores, complementando o dia atual com o máximo registrado quando ainda não existe agregado para aquele equipamento, sem duplicá-lo.
- Consumo geral: configure a variável e a unidade no seletor. Para vários dias, escolha um contador acumulado de energia; o cálculo usa a última menos a primeira leitura diária, não cobrindo os intervalos antes/depois dessas leituras. Reinícios do contador e dias com menos de duas leituras ficam sem valor.

Na visão geral, a potência de inversores (variável 0) e medidores (variável 27) é dividida por 1.000 para apresentar ambas em kW, considerando as leituras de origem em W. A unidade da variável 27 deve ser confirmada na instalação. O complemento diário mantém a convenção anterior (7/1000 e 27/1000). Os horários são os retornados pelo banco e os limites abrangem o dia inteiro. As consultas usam cache de 60 segundos e não há atualização automática. Dados ausentes não são preenchidos com zero.

Validação local: `python -m unittest discover -s tests -v`. Os testes de interface usam dados simulados; não validam a disponibilidade nem as unidades do banco real.

Gráficos e CSV usam a mesma conversão. Não há multiplicador adicional na série Consumo; os agregados de energia permanecem divididos por 1.000 e apresentados em kWh.


### Analisar — variáveis por equipamento

Selecione um ou mais equipamentos e parâmetros (potência, tensão, corrente e outras variáveis cadastradas), usando o mesmo seletor de período com atalhos. O seletor carrega todos os parâmetros diretamente do cadastro, sem percorrer o histórico de medições. Parâmetros sem leituras na seleção apresentam uma mensagem de ausência de dados. Cada combinação equipamento/parâmetro tem sua própria série de linhas, inclusive para vários dias; não há soma entre equipamentos nem conversão dos valores de origem.

Parâmetros diferentes aparecem em painéis com escalas verticais independentes. A lateral mostra máximo, mínimo, média, variação, desvio padrão populacional e mediana da série escolhida, calculados sobre as leituras disponíveis. O CSV preserva as leituras retornadas, inclusive registros no mesmo horário, com identificadores e nomes dos equipamentos e parâmetros. A unidade não é inferida pelo nome: os valores seguem o cadastro do banco.

Os filtros de Analisar são enviados juntos pelo botão **Aplicar seleção**. Marcar equipamentos ou variáveis não dispara novas consultas; o gráfico e o CSV mantêm a última seleção aplicada. Em Monitorar, cada seletor de equipamentos também possui **Aplicar seleção**, inclusive após escolher um grupo de unidade consumidora ou transformador. O período continua com sua confirmação própria.
