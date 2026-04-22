# Projeto Observatório: Análise e Predição de Salários de Desenvolvedores no Brasil
Esse repositório reúne uma série de projetos que fiz com alguns colegas do IMPATech. O projeto abrange desde a coleta dos dados até a análise final, foram utilizados conceitos aprendidos na matéria de Machine Learning e nossa intenção é explicar da forma mais clara possível cada etapa do processo.

# Sobre o Projeto
O objetivo inicial desse projeto foi investigar o cenário de remuneração de cientistas de dados no Brasil. Porém uma das etapas do projeto, usar modelos de Machine Learning para previsão de salário com base em outros preditores, foi feito com dados da profissão de desenvolvedor, por haver uma maior quantidade de dados.

O projeto se divide em três grandes etapas:

1. Coleta de Dados;
2. Análise Exploratória e Machine Learning;
3. Implementação ou Deploy (ainda em desenvolvimento...)

Por enquanto, vou falar mais sobre as duas primeiras.

![Capa](assets/capa1.png)

## 1. Coleta de Dados (Web Scraping)

Os dados foram extraídos da plataforma [Salário Transparente](https://salariotransparente.com.br/), onde profissionais compartilham anonimamente suas remunerações.

### Abordagem Técnica:

Utilizei a biblioteca `Selenium` para automação do navegador, pois permmite:
- Interações dinâmicas como inserção de texto;
- Simulação de cliques para fechar pop-ups;
- Rolagem contínua da página (Lazy loading).

Utilizei também a biblioteca `BeautifulSoup` para processar o HTML extraído de forma que as informações dos cards das vagas estivessem estruturas.

O script se encontra no arquivo `scraping.py`, porém o `scraping.ipynb` provê uma explicação mais detalhada do papel dessas bibliotecas.

Vídeo do Scraping sendo feito automaticamente com o Selenium

![scraping_gif](assets/scraping_selenium.gif)

## 2. Análise Exploratória e Machine Learning

Com a base de dados construída, o projeto explora o comportamento do mercado de tecnologia através de diferentes vertentes do aprendizado de máquina:

### Regressão:
Previsão da remuneração total mensal baseada em atributos do profissional e da vaga. Foram testados modelos lineares (Regressão Linear, Ridge, Lasso), Random Forest, Splines e GAMs, identificando as variáveis que mais impactam o salário final.

### Classificação de Senioridade:
Modelagem para prever o nível do desenvolvedor (Júnior, Pleno, Sênior) utilizando métodos como Regressão Logística, Extra Trees, Gradient Boosting e Voting Classifiers (que apresentou a melhor acurácia na generalização).

### Clusterização (K-Means & PCA):
Aprendizado não supervisionado para segmentar e agrupar vagas por similaridade técnica e financeira, revelando fronteiras e sobreposições reais no mercado de trabalho.

# Como Executar

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1Hq0vIaxXwB5if-gYuJaD3jM6NL--HrEw?usp=sharing)

# Estrutura do Repositório

- 📦 **assets/**
  Contém recursos visuais utilizados no projeto, como imagens e mídias demonstrativas (GIFs e vídeos).

- 📊 **data/**
  Armazena os dados coletados e processados, geralmente em formato `.csv`.

- 📓 **notebooks/**
  Notebooks Jupyter utilizados para exploração, testes e experimentos com os dados e modelos.

- 🧠 **src/**
  Código-fonte principal do projeto, incluindo scripts de scraping e processamento.
  
