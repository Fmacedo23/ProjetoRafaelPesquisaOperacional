# 🚀 Otimizador Híbrido de Modelos "Black-Box"

Este projeto é uma ferramenta avançada de otimização automática projetada para encontrar os melhores parâmetros de programas executáveis (`.exe`) externos. 

Ele utiliza uma abordagem **Híbrida (Global + Local)** para garantir que você encontre o melhor resultado possível (Máximo ou Mínimo) sem precisar alterar o código do seu software original.

---

## 🧠 Como Funciona (A Lógica Híbrida)

O sistema combina dois algoritmos poderosos em sequência:

1.  **Fase 1: Exploração Global (Optuna/TPE)**
    * Usa o algoritmo *Tree-structured Parzen Estimator*.
    * "Sobrevoa" todo o espaço de possibilidades para identificar as regiões mais promissoras.
    * Lida nativamente com números inteiros, decimais e categorias de texto.

2.  **Fase 2: Refinamento Local (Pattern Search)**
    * Pega o melhor resultado encontrado na Fase 1.
    * Realiza uma busca determinística (passo a passo) para "escalar a montanha" até o pico exato.
    * Garante precisão decimal no resultado final.

> **Bônus:** O repositório também inclui um otimizador baseado no método **Simplex (Nelder-Mead)** como alternativa geométrica.

---

## 📂 Estrutura do Projeto

* `main.py`: **O Script Principal.** Contém o motor híbrido, a proteção contra falhas e o gerador de relatórios.
* `optimize_simplex.py`: Uma implementação alternativa usando o algoritmo Simplex (SciPy).
* `config_*.json`: Arquivos de configuração (o "mapa" que ensina o Python a ler o seu .exe).
* `requirements.txt`: Lista de bibliotecas necessárias.

---

## 🛠️ Instalação

### 1. Pré-requisitos
Certifique-se de ter o **Python 3.8+** instalado no seu computador.

### 2. Instalar Dependências
Abra o terminal na pasta do projeto e execute:

```bash
pip install -r requirements.txt
