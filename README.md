# 🚀 Otimizador de Modelos "Black-Box" (Sistema Híbrido)

Este projeto contém uma suíte completa de ferramentas de otimização para encontrar os melhores parâmetros de executáveis (`.exe`) externos.

O sistema inclui três estratégias diferentes para garantir que você encontre o resultado máximo (ou mínimo) possível:

1.  **Híbrido (`main.py`):** A melhor opção. Usa Inteligência Artificial (Optuna) para achar a região certa e depois Refinamento Local (Pattern Search) para achar o topo exato.
2.  **Swarm Infinito (`optimize_swarm_infinito.py`):** Exploração Global pura. Testa milhares de possibilidades aleatórias inteligentes sem parar.
3.  **Pattern Search Infinito (`optimize_pattern_infinito.py`):** Busca Local pura. Refina passo-a-passo a partir de um ponto inicial.

---

## 🛠️ 1. Instalação (Faça isso primeiro)

Antes de rodar qualquer coisa, você precisa instalar as bibliotecas necessárias.

1.  Abra o terminal na pasta do projeto.
2.  Execute o comando:

```bash
pip install -r requirements.txt
