# Otimizador Híbrido (Black-Box Optimization) 🚀

Este projeto implementa um sistema robusto de otimização para modelos "caixa-preta" (arquivos executáveis `.exe`).

O sistema utiliza uma **Estratégia Híbrida** combinando algoritmos estocásticos para exploração global e algoritmos determinísticos para refinamento local.

## 🧠 Estratégia de Otimização

O otimizador funciona em duas fases sequenciais para garantir o melhor resultado possível:

1.  **Fase 1 (Exploração Global):** Utiliza **TPE (Tree-structured Parzen Estimator)** via biblioteca *Optuna*. Esta fase "sobrevoa" o espaço de busca para encontrar as regiões mais promissoras, lidando bem com variáveis categóricas e inteiras.
2.  **Fase 2 (Refinamento Local):** Utiliza **Pattern Search (Busca por Coordenadas)**. Pega o melhor resultado da Fase 1 e realiza um ajuste fino ("polimento") para encontrar o ótimo local exato.

> **Nota:** Também está incluída uma implementação do método **Simplex (Nelder-Mead)** como alternativa geométrica.

## 🛠️ Funcionalidades

* **Configuração via JSON:** Não é necessário alterar o código. Cada modelo (`.exe`) possui seu próprio "mapa" em arquivo `.json`.
* **Objetivos Flexíveis:** O usuário pode escolher **Maximizar** (ex: lucro) ou **Minimizar** (ex: erro) via linha de comando ou menu interativo.
* **Sistema "Blindado":** Possui proteção contra interrupções (`Ctrl+C`). Se o usuário parar a execução, o programa salva o melhor resultado encontrado até aquele momento e gera o relatório.
* **Relatórios Automáticos:** Ao final, gera um arquivo `.txt` com estatísticas de tempo, evolução da otimização e os parâmetros ideais.
* **Suporte a Tipos Mistos:** Otimiza parâmetros inteiros, flutuantes (floats) e categóricos (texto) simultaneamente.

## 📂 Estrutura de Arquivos

* `main.py`: **O Otimizador Principal.** Contém a lógica híbrida (Optuna + Pattern Search) e o gerador de relatórios.
* `optimize_simplex.py`: Uma implementação alternativa usando o algoritmo Nelder-Mead (SciPy).
* `config_*.json`: Arquivos de configuração que descrevem os parâmetros e limites de cada executável.
* `requirements.txt`: Lista de dependências Python.

## 🚀 Como Usar

### 1. Instalação
Certifique-se de ter o Python instalado e instale as dependências:

```bash
pip install -r requirements.txt
