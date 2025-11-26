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

⚙️ 2. Configuração (O Mapa do Tesouro)

{
    "executavel": "simulado.exe",
    "parametros": [
        {
            "nome": "x1",
            "tipo": "inteiro",
            "limites": [1, 100],
            "valor_inicial": 50,
            "passo": 5
        },
        {
            "nome": "x2",
            "tipo": "inteiro",
            "limites": [1, 100],
            "valor_inicial": 50,
            "passo": 5
        },
        {
            "nome": "x3",
            "tipo": "inteiro",
            "limites": [1, 100],
            "valor_inicial": 50,
            "passo": 5
        },
        {
            "nome": "x4",
            "tipo": "inteiro",
            "limites": [1, 100],
            "valor_inicial": 50,
            "passo": 5
        },
        {
            "nome": "x5",
            "tipo": "inteiro",
            "limites": [1, 100],
            "valor_inicial": 50,
            "passo": 5
        }
    ]
}


🚀 3. Como Rodar (Escolha sua Estratégia)
python main.py --config config_simulado.json
python main.py --config config_simulado.json --max
python optimize_swarm_infinito.py --config config_simulado.json --max
python optimize_pattern_infinito.py --config config_simulado.json --max
