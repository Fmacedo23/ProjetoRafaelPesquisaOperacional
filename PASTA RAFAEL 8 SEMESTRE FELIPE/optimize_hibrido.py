import subprocess
import copy
import json
import argparse
import sys
import optuna
import logging

# --- Início da Seção "Black Box" (Rodar o .exe) ---
# Esta é a nossa função "Nível 2" que entende os dois formatos de saída
# -----------------------------------------------------------------

def rodar_modelo_e_ler_saida(executavel, params_dict, lista_de_parametros):
    """
    Executa o modelo com os parâmetros dados (na ordem correta) 
    e retorna o float da saída.
    """
    
    command = [executavel]
    try:
        for param_info in lista_de_parametros:
            nome_param = param_info['nome']
            valor = params_dict[nome_param]
            command.append(str(valor))
    except KeyError as e:
        print(f"ERRO: Parâmetro '{e}' não encontrado no dicionário.")
        return None
        
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        output_completo = result.stdout.strip()
        
        # 1. Tenta o formato "Valor de saída: 123.45"
        for line in output_completo.splitlines():
            if 'Valor de saída:' in line:
                try:
                    valor_str = line.split(':')[-1].strip()
                    return float(valor_str)
                except Exception:
                    return None # Falha ao converter

        # 2. Se não achou, tenta assumir que a SAÍDA INTEIRA é o número
        try:
            valor_float = float(output_completo)
            return valor_float
        except ValueError:
            print(f"ERRO: A saída não é um número e nem o formato 'Valor de saída:'.")
            print(f"Saída: {output_completo}")
            return None

    except subprocess.CalledProcessError as e:
        # O .exe falhou (talvez por parâmetros errados)
        # Não retornamos "None" para que o Optuna saiba que foi uma falha
        print(f"Falha no .exe (parâmetros inválidos?): {e.stdout}")
        raise optuna.exceptions.TrialPruned() # Diz ao Optuna para pular esta tentativa
    except Exception as e:
        print(f"ERRO ao executar o modelo: {e}")
        return None

# --- Fim da Seção "Black Box" ---


# --- Início da Seção "Fase 1: Exploração (Optuna)" ---
# O Optuna vai chamar esta função "objective" centenas de vezes
# ---------------------------------------------------------

# Variáveis globais para compartilhar o config com o Optuna
CONFIG_GLOBAL = {}

def objective_optuna(trial):
    """
    Esta é a função que o Optuna executa em cada "Trial" (tentativa).
    """
    executavel = CONFIG_GLOBAL['executavel']
    lista_de_parametros = CONFIG_GLOBAL['parametros']
    
    params_teste = {}
    
    # 1. O Optuna "sugere" os parâmetros com base no config.json
    for param_info in lista_de_parametros:
        nome = param_info['nome']
        tipo = param_info['tipo']
        
        if tipo == 'categorico':
            limites = param_info['limites']
            params_teste[nome] = trial.suggest_categorical(nome, limites)
        
        elif tipo == 'inteiro':
            min_lim, max_lim = param_info['limites']
            # O 'passo' aqui é o passo de *sugestão* do Optuna
            passo = param_info.get('passo_sugestao', 1) 
            params_teste[nome] = trial.suggest_int(nome, min_lim, max_lim, step=passo)
            
        elif tipo == 'float':
            min_lim, max_lim = param_info['limites']
            passo = param_info.get('passo_sugestao', 0.1) 
            params_teste[nome] = trial.suggest_float(nome, min_lim, max_lim, step=passo)

    # 2. Executa o .exe com os parâmetros sugeridos
    resultado = rodar_modelo_e_ler_saida(executavel, params_teste, lista_de_parametros)
    
    if resultado is None:
        # Se falhou a leitura, diz ao Optuna para descartar (prune) esta tentativa
        raise optuna.exceptions.TrialPruned()
        
    return resultado

# --- Fim da Seção Optuna ---


# --- Início da Seção "Fase 2: Refinamento (Pattern Search)" ---
# Esta é a lógica do nosso script 'optimize_generic.py' antigo,
# agora transformada em uma função.
# --------------------------------------------------------------

def refinar_com_pattern_search(config, params_iniciais):
    """
    Executa o Pattern Search (busca local) começando de um ponto inicial.
    """
    
    executavel = config['executavel']
    objetivo = config['objetivo']
    lista_de_parametros = config['parametros']

    print(f"\n--- Iniciando FASE 2: Refinamento (Pattern Search) ---")
    
    melhores_params = copy.deepcopy(params_iniciais)
    melhor_resultado = rodar_modelo_e_ler_saida(executavel, melhores_params, lista_de_parametros)
    
    if melhor_resultado is None:
        print("Falha ao rodar o modelo com parâmetros iniciais do refinamento.")
        return params_iniciais, -float('inf') if objetivo == 'maximizar' else float('inf')

    print(f"Ponto de partida do refinamento: {melhor_resultado}")

    iteracao = 0
    while True:
        iteracao += 1
        print(f"  Refinamento (Iteração {iteracao})...")
        houve_melhoria = False
        
        for param_info in lista_de_parametros:
            nome_param = param_info['nome']
            tipo_param = param_info['tipo']
            
            params_base_iteracao = copy.deepcopy(melhores_params)

            if tipo_param == 'categorico':
                # O Pattern Search não pode "adivinhar" categorias
                # Ele só testa as que estão no config.json
                limites = param_info['limites']
                for valor_teste in limites:
                    if valor_teste == params_base_iteracao[nome_param]: continue
                    
                    params_teste = copy.deepcopy(params_base_iteracao)
                    params_teste[nome_param] = valor_teste
                    
                    resultado_teste = rodar_modelo_e_ler_saida(executavel, params_teste, lista_de_parametros)
                    if resultado_teste is None: continue

                    if (objetivo == 'maximizar' and resultado_teste > melhor_resultado) or \
                       (objetivo == 'minimizar' and resultado_teste < melhor_resultado):
                        
                        melhor_resultado = resultado_teste
                        melhores_params = copy.deepcopy(params_teste)
                        houve_melhoria = True

            elif tipo_param == 'inteiro' or tipo_param == 'float':
                # No refinamento, usamos um passo *menor*
                passo = param_info['passo'] 
                min_lim, max_lim = param_info['limites']
                
                for direcao in [passo, -passo]:
                    params_base_direcao = copy.deepcopy(melhores_params) 
                    valor_atual = params_base_direcao[nome_param]
                    valor_teste = valor_atual + direcao
                    
                    if tipo_param == 'inteiro': valor_teste = int(round(valor_teste))
                    
                    valor_teste = max(min_lim, min(valor_teste, max_lim)) 
                    
                    if valor_teste == valor_atual: continue

                    params_teste = copy.deepcopy(params_base_direcao)
                    params_teste[nome_param] = valor_teste
                    
                    resultado_teste = rodar_modelo_e_ler_saida(executavel, params_teste, lista_de_parametros)
                    if resultado_teste is None: continue

                    if (objetivo == 'maximizar' and resultado_teste > melhor_resultado) or \
                       (objetivo == 'minimizar' and resultado_teste < melhor_resultado):
                        
                        print(f"    Melhoria no Refinamento! {nome_param}: {valor_teste} -> Resultado: {resultado_teste}")
                        melhor_resultado = resultado_teste
                        melhores_params = copy.deepcopy(params_teste)
                        houve_melhoria = True
            
        if not houve_melhoria:
            print(f"  Refinamento concluído.")
            break
            
    return melhores_params, melhor_resultado

# --- Fim da Seção Pattern Search ---


# --- Ponto de Entrada Principal ---
# Aqui é onde o script decide o que fazer
# -----------------------------------

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Otimizador Híbrido (Optuna + Pattern Search)")
    parser.add_argument('-c', '--config', 
                        type=str, 
                        required=True, 
                        help="Caminho para o arquivo .json de configuração do modelo.")
    parser.add_argument('-t', '--trials',
                        type=int,
                        default=100,
                        help="Número de 'trials' (tentativas) para a Fase 1 (Optuna).")
    parser.add_argument('--norefine',
                        action='store_true',
                        help="Desativa a Fase 2 (Refinamento com Pattern Search).")
    
    args = parser.parse_args()
    
    # 1. Carrega o arquivo de configuração
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            CONFIG_GLOBAL = json.load(f) # Salva na variável global
    except FileNotFoundError:
        print(f"ERRO: Arquivo de configuração não encontrado: {args.config}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"ERRO: O arquivo de configuração '{args.config}' não é um JSON válido.")
        sys.exit(1)

    # Define a direção da otimização
    direcao = CONFIG_GLOBAL.get('objetivo', 'maximizar')
    
    print(f"--- Iniciando OTIMIZAÇÃO HÍBRIDA ---")
    print(f"Arquivo de Configuração: {args.config}")
    print(f"Objetivo: {direcao}")
    
    # --- FASE 1: EXPLORAÇÃO (OPTUNA) ---
    print(f"\n--- Iniciando FASE 1: Exploração (Optuna) com {args.trials} tentativas ---")
    
    # Esconde o log do Optuna para não poluir o terminal
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    
    study = optuna.create_study(direction='maximize' if direcao == 'maximizar' else 'minimize')
    study.optimize(objective_optuna, n_trials=args.trials, show_progress_bar=True)
    
    print("... Exploração concluída.")
    
    # Pega o melhor resultado do Optuna
    melhor_trial_optuna = study.best_trial
    resultado_optuna = melhor_trial_optuna.value
    params_optuna = melhor_trial_optuna.params
    
    print(f"\n--- Resultado da FASE 1 (Optuna) ---")
    print(f"Melhor Valor: {resultado_optuna}")
    print(f"Melhores Parâmetros:\n{json.dumps(params_optuna, indent=4)}")

    # --- FASE 2: REFINAMENTO (PATTERN SEARCH) ---
    
    if args.norefine:
        print("\n--- OTIMIZAÇÃO FINALIZADA (sem refinamento) ---")
        print(f"Resultado Final: {resultado_optuna}")
        print(f"Parâmetros Finais:\n{json.dumps(params_optuna, indent=4)}")
    else:
        # Usa os parâmetros do Optuna como ponto de partida para o Pattern Search
        params_finais, resultado_final = refinar_com_pattern_search(CONFIG_GLOBAL, params_optuna)
        
        print("\n--- OTIMIZAÇÃO FINALIZADA (com refinamento) ---")
        print(f"Resultado Pós-Refinamento: {resultado_final}")
        print(f"Parâmetros Finais:\n{json.dumps(params_finais, indent=4)}")