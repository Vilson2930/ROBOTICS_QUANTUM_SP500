# ROBOTICS_QUANTUM_SP500

## Sistema Quantitativo de Seleção de Empresas — Robotics & Quantum Computing

O **ROBOTICS_QUANTUM_SP500** é um sistema quantitativo desenvolvido para identificar e acompanhar empresas do **S&P 500** com exposição relevante aos temas:

- Robotics
- Quantum Computing

O sistema combina análise fundamentalista, classificação temática e, exclusivamente no segmento Robotics, análise quantitativa do momento de entrada.

O objetivo principal do robô é responder a duas perguntas diferentes:

1. **Quais são as melhores empresas dos temas Robotics e Quantum dentro do S&P 500?**
2. **Quando existe uma condição adequada para entrada ou novo aporte?**

Essas duas decisões são mantidas separadas dentro da arquitetura.


---

# 1. OBJETIVO DO ROBÔ

O objetivo do ROBOTICS_QUANTUM_SP500 é construir automaticamente uma seleção concentrada das empresas fundamentalmente mais bem classificadas nos segmentos de:

- Robotics
- Quantum Computing

dentro do universo atual do S&P 500.

O robô não procura simplesmente empresas que apresentaram valorização recente.

A seleção principal é baseada em critérios fundamentais.

No segmento Robotics existe ainda uma segunda camada independente responsável por avaliar o momento de entrada ou novo aporte.


---

# 2. UNIVERSO DE INVESTIMENTO

O universo inicial obrigatório é:

**S&P 500**

Uma empresa somente pode participar do processo de seleção se:

1. pertencer ao S&P 500;
2. estiver classificada no universo temático do projeto;
3. possuir dados suficientes para o cálculo dos fatores fundamentais exigidos.

A atualização do universo do S&P 500 ocorre antes da seleção temática.

A arquitetura é:

S&P 500

↓

Classificação temática

↓

Robotics / Quantum

↓

Análise fundamental

↓

Ranking

↓

Seleção


---

# 3. UNIVERSO TEMÁTICO

As empresas são classificadas de acordo com sua exposição aos temas:

- ROBOTICS
- QUANTUM
- BOTH

Também existe uma classificação da natureza da exposição:

- DIRECT
- STRATEGIC
- ENABLER

Uma empresa classificada como BOTH pode participar independentemente dos rankings Robotics e Quantum.

Isso significa que uma mesma empresa pode aparecer simultaneamente nas duas estratégias caso obtenha classificação fundamental suficiente.


---

# 4. ARQUITETURA GERAL

O pipeline principal do robô é:

S&P500_UNIVERSE

↓

THEMATIC_CLASSIFIER

↓

FUNDAMENTAL_DATA

↓

FUNDAMENTAL_SELECTION

↓

ROBOTICS / QUANTUM

↓

ROBOTICS → AI INFRASTRUCTURE SIGNAL ENGINE

QUANTUM → SEM TIMING TÉCNICO

↓

PORTFOLIO_ENGINE

↓

REPORT_GENERATOR

↓

EMAIL + PDF


---

# 5. ROBOTICS

## Financial Strength Top 5

O segmento ROBOTICS utiliza o fator:

**FINANCIAL STRENGTH**

O objetivo é identificar as empresas financeiramente mais fortes dentro do universo Robotics elegível.

O ranking considera três componentes fundamentais:

### 5.1 Cash / Assets

Relação entre caixa e ativos totais.

Quanto maior, melhor.

Representa a quantidade de caixa disponível em relação à estrutura de ativos da empresa.


### 5.2 Debt / Assets

Relação entre dívida e ativos totais.

Quanto menor, melhor.

Busca identificar empresas com menor comprometimento dos ativos por endividamento.


### 5.3 Debt / Equity

Relação entre dívida e patrimônio líquido.

Quanto menor, melhor.

É uma medida adicional da estrutura de capital e do nível relativo de endividamento.


---

# 6. FINANCIAL STRENGTH SCORE

Os indicadores são comparados dentro do universo elegível.

Antes da formação dos percentis, o sistema aplica tratamento de valores extremos por winsorização.

O método utiliza limites de:

**P5 — P95**

Depois disso, cada componente é convertido em uma pontuação relativa.

O Financial Strength Score é formado pela média dos componentes fundamentais válidos.

São necessários pelo menos:

**2 dos 3 componentes**

para que a empresa possua Financial Strength Score válido.

O ranking é ordenado do maior score para o menor.


---

# 7. ROBOTICS TOP 5

Após o cálculo do Financial Strength Score:

1. todas as empresas Robotics elegíveis são classificadas;
2. o ranking é ordenado pelo Financial Strength Score;
3. as cinco primeiras são selecionadas.

Portanto:

**ROBOTICS = FINANCIAL STRENGTH TOP 5**

A quantidade de empresas selecionadas permanece em cinco enquanto existirem pelo menos cinco empresas elegíveis com dados suficientes.

As empresas que ocupam essas posições podem mudar ao longo do tempo.


---

# 8. QUANDO UMA EMPRESA ROBOTICS SAI DA SELEÇÃO

Uma empresa não permanece no portfólio simplesmente porque foi selecionada anteriormente.

A cada nova execução os fundamentos são atualizados e o ranking é recalculado.

Se outra empresa obtiver Financial Strength Score superior, poderá ultrapassar uma empresa atualmente selecionada.

Quando uma empresa deixa de ocupar o Top 5 fundamental:

**ela deixa a seleção Robotics.**

O timing técnico não decide quais empresas pertencem ao Top 5.

Essa decisão pertence exclusivamente ao ranking fundamental.


---

# 9. TIMING DE ROBOTICS

Depois da seleção das cinco melhores empresas Robotics, existe uma segunda etapa:

**AI INFRASTRUCTURE SIGNAL ENGINE**

Essa camada não escolhe as empresas.

Ela recebe as empresas que já foram selecionadas pelo Financial Strength Top 5.

Sua função é responder:

**Existe condição quantitativa adequada para entrada ou novo aporte agora?**


---

# 10. AI INFRASTRUCTURE SIGNAL ENGINE

O motor de timing utilizado em Robotics preserva a arquitetura validada do AI Infrastructure Scanner.

O processo utiliza quatro grandes camadas:

1. Technical Indicators
2. Institutional Score
3. Technical Entry Score
4. Entry Timing Engine

Essas informações são posteriormente combinadas pelo:

**Signal Engine**


---

# 11. INSTITUTIONAL SCORE

O Institutional Score procura identificar características relacionadas a:

- fluxo de capital;
- força relativa;
- liquidez;
- comportamento de volume;
- liderança;
- participação institucional.

Ele não substitui a análise fundamental.

A empresa já precisa ter sido selecionada pelo ranking fundamental Robotics antes de essa camada ser utilizada.


---

# 12. TECHNICAL ENTRY SCORE

O Technical Entry Score avalia características relacionadas ao comportamento do preço e à qualidade técnica da entrada.

Entre os elementos analisados pelo motor estão:

- desconto;
- momentum;
- tendência;
- persistência da tendência;
- estrutura das médias móveis;
- distância das médias;
- distância da máxima de 52 semanas;
- volume;
- fluxo;
- liquidez;
- risco;
- penalidades técnicas.

O objetivo não é selecionar a empresa fundamentalmente.

O objetivo é avaliar a qualidade técnica do momento de entrada.


---

# 13. ENTRY TIMING ENGINE

O Entry Timing Engine é uma camada específica para determinar a qualidade do momento atual de entrada.

Entre seus resultados estão:

- Entry Timing Score
- Timing Status
- Pullback Probability
- Parabolic Risk
- Acceleration Factor
- Explosion Score
- Extension Quality
- Trend Structure
- Timing Confidence
- Timing Approved

Entre os possíveis estados estão:

- ENTRAR AGORA
- PRÉ-ENTRADA
- AGUARDAR PULLBACK
- AGUARDAR ROMPIMENTO
- MUITO ESTICADA
- ALTO RISCO
- LATERAL / OBSERVAÇÃO


---

# 14. SIGNAL ENGINE

O Signal Engine combina as informações produzidas pelas camadas anteriores.

Ele considera:

- Institutional Score
- Technical Entry Score
- Entry Timing Score
- condições de risco
- confirmações técnicas
- condições de volume
- relação risco/retorno
- vetos de timing

O resultado final determina se existe ou não aprovação para entrada.

A aprovação final é registrada por:

**signal_approved**


---

# 15. REGRA FUNDAMENTAL DE ROBOTICS

É essencial separar duas decisões.

### Empresa selecionada

Significa:

**a empresa pertence ao Financial Strength Top 5.**

### Entrada aprovada

Significa:

**além de estar no Top 5 fundamental, o Signal Engine aprovou o momento de entrada ou novo aporte.**

Portanto:

**SELEÇÃO FUNDAMENTAL ≠ MOMENTO DE ENTRADA**


---

# 16. AGUARDAR TIMING NÃO SIGNIFICA VENDER

Quando uma empresa Robotics aparece como:

**AGUARDAR TIMING**

isso não significa que a empresa deixou de ser considerada boa pelo ranking fundamental.

Significa apenas que:

**o sistema não aprovou uma nova entrada ou novo aporte naquele momento.**

O Timing Engine:

- não gera sinal de venda;
- não remove empresa do Top 5;
- não altera o ranking fundamental;
- não substitui a análise fundamental.


---

# 17. QUANTUM COMPUTING

O segmento Quantum possui uma arquitetura diferente de Robotics.

A seleção utiliza:

**GROWTH TOP 2**

Não existe AI Infrastructure Timing Engine no segmento Quantum.


---

# 18. GROWTH SCORE

O Growth Score procura identificar as empresas com melhor crescimento fundamental relativo dentro do universo Quantum elegível.

São utilizados três componentes:

### 18.1 Revenue Growth

Crescimento da receita.

Quanto maior, melhor.


### 18.2 EPS Growth

Crescimento do lucro por ação diluído.

Quanto maior, melhor.


### 18.3 Operating Cash Flow Growth

Crescimento do fluxo de caixa operacional.

Quanto maior, melhor.


---

# 19. CÁLCULO DO GROWTH SCORE

Os indicadores são comparados entre as empresas elegíveis.

O processo utiliza tratamento de valores extremos e transformação em percentis.

O Growth Score é formado pela média dos componentes válidos.

A empresa precisa possuir pelo menos:

**2 dos 3 componentes**

para obter Growth Score válido.

Depois disso, as empresas são ordenadas do maior Growth Score para o menor.


---

# 20. QUANTUM TOP 2

Depois do ranking:

**as duas empresas com maior Growth Score são selecionadas.**

Portanto:

**QUANTUM = GROWTH TOP 2**

A quantidade permanece em duas empresas enquanto existirem pelo menos duas empresas elegíveis com dados suficientes.

As empresas podem mudar conforme seus fundamentos mudam.


---

# 21. QUANDO AS EMPRESAS QUANTUM MUDAM

As empresas atualmente selecionadas não possuem posição permanente.

A cada atualização dos dados fundamentais, o Growth Score é recalculado.

Se uma terceira empresa apresentar Growth Score superior à segunda colocada, ela assume a posição no Top 2.

Exemplo conceitual:

1º Empresa A — 0.87

2º Empresa B — 0.75

3º Empresa C — 0.68

Se posteriormente:

Empresa C → 0.82

o novo ranking poderá se tornar:

1º Empresa A — 0.87

2º Empresa C — 0.82

3º Empresa B — 0.75

Nesse caso, Empresa C entra no Top 2 e Empresa B deixa a seleção.


---

# 22. QUANTUM NÃO UTILIZA TIMING

Uma regra importante da arquitetura é:

**QUANTUM NÃO UTILIZA O AI INFRASTRUCTURE SIGNAL ENGINE.**

Durante os estudos de validação, o uso do timing não apresentou sustentação suficiente para justificar sua incorporação à estratégia Quantum.

Por isso, a arquitetura preservada é:

QUANTUM

↓

Growth Score

↓

Ranking

↓

Top 2

↓

Seleção Fundamental


---

# 23. SIGNIFICADO DE "ENTRADA FUNDAMENTAL"

Quando o relatório apresenta:

**ENTRADA FUNDAMENTAL**

isso significa que a empresa pertence ao:

**Growth Top 2 Quantum.**

Não significa que o sistema identificou tecnicamente o melhor preço ou o melhor momento gráfico para comprar.

Não existe essa segunda avaliação no bloco Quantum.

Uma descrição conceitualmente mais precisa é:

**SELECIONADA — TOP 2 FUNDAMENTAL**


---

# 24. DADOS FUNDAMENTAIS

Os dados fundamentais utilizados pelo sistema são obtidos a partir das informações corporativas disponibilizadas pela SEC.

O processo procura preservar a disponibilidade histórica da informação.

A data relevante para disponibilidade do dado é a data em que a informação foi registrada/publicada nos documentos corporativos utilizados pelo sistema.

O objetivo é evitar que informações ainda não disponíveis naquele momento sejam utilizadas retroativamente.


---

# 25. CRESCIMENTO POINT-IN-TIME

Para métricas de crescimento, o sistema compara a observação atual com uma observação comparável anterior.

A metodologia procura um período anterior aproximadamente equivalente a um ano.

A janela utilizada para localizar a observação comparável é:

**300 a 430 dias**

A observação mais próxima de aproximadamente 365 dias é priorizada.

O crescimento é calculado por:

Growth = Valor Atual / Valor Anterior - 1


---

# 26. PREVENÇÃO DE LOOKAHEAD

A arquitetura foi construída para impedir que informações futuras sejam utilizadas na geração dos sinais.

Os dados fundamentais precisam estar disponíveis na data considerada.

Da mesma forma:

**retornos futuros não participam da geração dos sinais.**

Retornos posteriores podem ser utilizados em estudos históricos de validação, mas não para produzir uma decisão operacional atual.


---

# 27. PORTFÓLIO FINAL

A arquitetura produz duas seleções independentes:

### ROBOTICS

Financial Strength Top 5

+

AI Infrastructure Signal Engine para entrada/aporte


### QUANTUM

Growth Top 2

+

Sem timing técnico


Portanto, o portfólio possui:

- 5 teses Robotics
- 2 teses Quantum

Total:

**7 teses**

Como uma empresa pode participar simultaneamente dos dois temas, o número de empresas únicas pode ser inferior a sete.


---

# 28. EMPRESAS BOTH

Empresas classificadas como:

**BOTH**

participam independentemente dos rankings Robotics e Quantum.

Isso significa que uma empresa pode:

- estar no Top 5 Robotics;
- estar no Top 2 Quantum;
- aparecer simultaneamente nas duas seleções.

Isso não representa duplicação acidental.

São duas teses temáticas diferentes avaliadas por metodologias fundamentais diferentes.


---

# 29. RELATÓRIO EXECUTIVO

Após a execução dos motores, o sistema gera um relatório executivo.

O relatório apresenta:

### Robotics

- posição fundamental;
- ticker;
- Financial Strength Score;
- Institutional Score;
- Technical Entry Score;
- Entry Timing Score;
- Final Score;
- Timing Status;
- decisão operacional.

### Quantum

- posição;
- ticker;
- empresa;
- Growth Score;
- situação fundamental.


---

# 30. RELATÓRIO POR E-MAIL

O robô possui uma camada independente de relatório por e-mail.

Ela:

1. recebe o portfólio final;
2. gera resumo executivo HTML;
3. gera relatório PDF;
4. anexa o PDF;
5. envia o relatório por Gmail.

As credenciais são fornecidas por GitHub Secrets:

- EMAIL_USER
- EMAIL_PASSWORD
- EMAIL_TO

A camada de relatório não possui autoridade para modificar decisões de investimento.


---

# 31. PDF

O PDF contém:

- resumo executivo;
- quantidade de empresas selecionadas;
- quantidade de Robotics com entrada aprovada;
- ranking Robotics;
- scores do Signal Engine;
- ranking Quantum;
- Growth Score;
- regras principais da arquitetura;
- interpretação operacional.

O PDF é apenas uma camada de apresentação.

Nenhuma decisão é recalculada durante sua geração.


---

# 32. GITHUB ACTIONS

O sistema é executado automaticamente por GitHub Actions.

O workflow também pode ser executado manualmente através de:

**workflow_dispatch**

A execução programada ocorre:

**segunda a sexta-feira**

Cron:

0 11 * * 1-5

correspondendo aproximadamente a:

**08:00 no horário de Brasília**

dependendo das regras de horário aplicáveis.


---

# 33. PIPELINE DE PRODUÇÃO

A execução segue a seguinte sequência lógica:

1. Atualização do S&P 500
2. Classificação temática
3. Coleta dos fundamentos
4. Seleção fundamental Robotics
5. Seleção fundamental Quantum
6. Download de dados de mercado para Robotics
7. Cálculo dos indicadores técnicos
8. Institutional Score
9. Technical Entry Score
10. Entry Timing Engine
11. Signal Engine
12. Portfolio Engine
13. Geração dos relatórios
14. Auditoria das invariantes
15. Geração do PDF e envio por e-mail


---

# 34. ESTRUTURA PRINCIPAL DO REPOSITÓRIO

```text
ROBOTICS_QUANTUM_SP500/
│
├── main.py
├── requirements.txt
├── README.md
│
├── config/
│   ├── settings.py
│   ├── thematic_universe.py
│   └── fundamental_policy.py
│
├── data/
│   ├── sp500_universe.py
│   ├── fundamental_data.py
│   └── market_data.py
│
├── engine/
│   ├── thematic_classifier.py
│   ├── fundamental_selection.py
│   ├── technical_indicators.py
│   ├── institutional_score.py
│   ├── technical_score.py
│   ├── entry_timing_engine.py
│   ├── signal_engine.py
│   └── portfolio_engine.py
│
├── reports/
│   ├── report_generator.py
│   └── email_report.py
│
└── .github/
    └── workflows/
        └── run_robot.yml
