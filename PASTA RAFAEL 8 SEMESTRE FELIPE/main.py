import subprocess
import copy
import json
import argparse
import sys
import optuna
import logging
import time
import os
from datetime import datetime

# ==============================================================================
# 1. FUNÇÃO BLACK BOX (Executa o .exe e lê o resultado)
# ==============================================================================
def rodar_modelo_e_ler_saida(executavel, params_dict, lista_de_parametros):
    command = [executavel]
    try:
        for param_info in lista_de_parametros:
            nome_param = param_info['nome']
            valor = params_dict[nome_param]
            command.append(str(valor))
    except KeyError:
        return None
        
    try:
        if not os.path.exists(executavel): return None
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        output_completo = result.stdout.strip()
        
        # Tenta achar "Valor de saída:"
        for line in output_completo.splitlines():
            if 'Valor de saída:' in line:
                try:
                    return float(line.split(':')[-1].strip())
                except: pass

        # Tenta ler apenas o número
        return float(output_completo)

    except Exception:
        return None

# ==============================================================================
# 2. FASE 1: EXPLORAÇÃO GLOBAL (Optuna)
# ==============================================================================
CONFIG_GLOBAL = {}

def objective_optuna(trial):
    executavel = CONFIG_GLOBAL['executavel']
    lista_de_parametros = CONFIG_GLOBAL['parametros']
    params_teste = {}
    
    for param_info in lista_de_parametros:
        nome = param_info['nome']
        tipo = param_info['tipo']
        
        if tipo == 'categorico':
            params_teste[nome] = trial.suggest_categorical(nome, param_info['limites'])
        elif tipo == 'inteiro':
            mini, maxi = param_info['limites']
            passo = param_info.get('passo_sugestao', 1)
            params_teste[nome] = trial.suggest_int(nome, mini, maxi, step=passo)
        elif tipo == 'float':
            mini, maxi = param_info['limites']
            passo = param_info.get('passo_sugestao', 0.1)
            params_teste[nome] = trial.suggest_float(nome, mini, maxi, step=passo)

    resultado = rodar_modelo_e_ler_saida(executavel, params_teste, lista_de_parametros)
    
    if resultado is None:
        raise optuna.exceptions.TrialPruned()
        
    return resultado

# ==============================================================================
# 3. FASE 2: REFINAMENTO LOCAL (Pattern Search) - MODO INFINITO
# ==============================================================================
def refinar_com_pattern_search(config, params_iniciais, objetivo_escolhido):
    executavel = config['executavel']
    lista_de_parametros = config['parametros']
    
    print(f"\n>>> Iniciando FASE 2: Refinamento Contínuo (Pattern Search) <<<")
    print("(O programa ficará rodando para sempre. Pressione Ctrl+C para parar e salvar)")
    
    melhores_params = copy.deepcopy(params_iniciais)
    melhor_resultado = rodar_modelo_e_ler_saida(executavel, melhores_params, lista_de_parametros)
    
    if melhor_resultado is None: return params_iniciais, 0

    print(f"Ponto de partida (vindo do Optuna): {melhor_resultado}")
    
    iteracao = 0
    
    # --- BLINDAGEM: TRY/EXCEPT DENTRO DO LOOP ---
    try:
        while True: # LOOP INFINITO
            iteracao += 1
            houve_melhoria = False
            
            for param_info in lista_de_parametros:
                nome = param_info['nome']
                tipo = param_info['tipo']
                params_base = copy.deepcopy(melhores_params)

                candidatos = []
                if tipo == 'categorico':
                    candidatos = [v for v in param_info['limites'] if v != params_base[nome]]
                else:
                    passo = param_info.get('passo', 1) # Usa passo do JSON ou 1
                    val = params_base[nome]
                    mini, maxi = param_info['limites']
                    vizinhos = [val + passo, val - passo]
                    if tipo == 'inteiro': vizinhos = [int(round(c)) for c in vizinhos]
                    candidatos = [c for c in vizinhos if mini <= c <= maxi and c != val]

                for val_teste in candidatos:
                    params_teste = copy.deepcopy(params_base)
                    params_teste[nome] = val_teste
                    
                    res = rodar_modelo_e_ler_saida(executavel, params_teste, lista_de_parametros)
                    if res is None: continue

                    melhorou = False
                    if objetivo_escolhido == 'maximizar' and res > melhor_resultado: melhorou = True
                    if objetivo_escolhido == 'minimizar' and res < melhor_resultado: melhorou = True
                    
                    if melhorou:
                        print(f"  [Iteração {iteracao}] ✨ MELHORIA! {nome}: {val_teste} -> {res}")
                        melhor_resultado = res
                        melhores_params = copy.deepcopy(params_teste)
                        houve_melhoria = True
                        params_base = copy.deepcopy(melhores_params)

            if not houve_melhoria:
                # Em vez de parar, avisa e espera um pouco
                sys.stdout.write(f"\r  [Iteração {iteracao}] Estável em {melhor_resultado}. Monitorando...")
                sys.stdout.flush()
                time.sleep(0.5) # Pausa para não sobrecarregar CPU
                
    except KeyboardInterrupt:
        print("\n\n⚠️  INTERRUPÇÃO DETECTADA NA FASE 2!")
        print("Salvando o melhor resultado encontrado até agora...")
        # A exceção é tratada aqui para retornar os dados limpos
        return melhores_params, melhor_resultado
            
    return melhores_params, melhor_resultado

# ==============================================================================
# 4. GERADOR DE RELATÓRIO AUTOMÁTICO
# ==============================================================================
def gerar_relatorio_arquivo(dados):
    """Gera um arquivo .txt com a análise completa"""
    
    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_modelo = dados['modelo'].replace('.exe', '')
    nome_arquivo = f"relatorio_HIBRIDO_{nome_modelo}_{data_hora}.txt"
    
    val_inicial = dados['resultado_fase1']
    val_final = dados['resultado_final']
    
    if val_inicial is None: val_inicial = 0
    if val_final is None: val_final = 0
    
    diff = val_final - val_inicial
    
    texto_impacto = ""
    if dados['status'] == 'INTERROMPIDO':
        texto_impacto = "⚠️ A EXECUÇÃO FOI INTERROMPIDA PELO USUÁRIO.\nOs dados abaixo representam o melhor estado encontrado antes da parada."
    else:
        if dados['objetivo'] == 'maximizar':
            if diff > 0: texto_impacto = f"SUCESSO: A Fase 2 aumentou o valor em +{diff:.4f} unidades."
            else: texto_impacto = "NEUTRO: A Fase 1 já havia encontrado o máximo local."
        else: # minimizar
            if diff < 0: texto_impacto = f"SUCESSO: A Fase 2 reduziu o valor em {diff:.4f} unidades."
            else: texto_impacto = "NEUTRO: A Fase 1 já havia encontrado o mínimo local."

    conteudo = f"""
================================================================================
                        RELATÓRIO DE OTIMIZAÇÃO HÍBRIDA
================================================================================
STATUS DA EXECUÇÃO    : {dados['status']}
Data e Hora           : {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}
Modelo Otimizado      : {dados['modelo']}
Arquivo Configuração  : {dados['config_file']}
Objetivo da Otimização: {dados['objetivo'].upper()}

--------------------------------------------------------------------------------
                            ESTATÍSTICAS DE TEMPO
--------------------------------------------------------------------------------
Tempo Total de Execução : {dados['tempo_total']:.2f} segundos
Tentativas Exploratórias: {dados['trials']} (Optuna)

--------------------------------------------------------------------------------
                            EVOLUÇÃO DOS RESULTADOS
--------------------------------------------------------------------------------
1. FIM DA FASE 1 (Exploração Global) : {val_inicial}
2. FIM DA FASE 2 (Refinamento Local) : {val_final}

>>> ANÁLISE DE IMPACTO:
{texto_impacto}

--------------------------------------------------------------------------------
                       MELHOR COMBINAÇÃO DE PARÂMETROS
--------------------------------------------------------------------------------
{json.dumps(dados['params_finais'], indent=4)}

================================================================================
"""
    try:
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f"\n[RELATÓRIO] Arquivo salvo com sucesso: {nome_arquivo}")
    except Exception as e:
        print(f"\n[RELATÓRIO] Erro ao salvar arquivo: {e}")

# ==============================================================================
# 5. EXECUÇÃO PRINCIPAL BLINDADA
# ==============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=str, required=True, help="Arquivo JSON")
    parser.add_argument('-t', '--trials', type=int, default=50, help="Tentativas Optuna")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--max', action='store_true', help="Forçar Maximizar")
    group.add_argument('--min', action='store_true', help="Forçar Minimizar")
    
    args = parser.parse_args()
    status_execucao = "CONCLUÍDO"
    
    melhor_fase1 = None
    params_fase1 = {}
    resultado_final = None
    params_finais = {}
    inicio_total = time.time()
    objetivo_cliente = "DESCONHECIDO"

    try:
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                CONFIG_GLOBAL = json.load(f)
        except:
            print("Erro ao abrir config JSON."); sys.exit(1)

        # --- LÓGICA DE ESCOLHA ---
        objetivo_cliente = None
        if args.max: objetivo_cliente = 'maximizar'
        elif args.min: objetivo_cliente = 'minimizar'

        if objetivo_cliente is None:
            print("\n" + "="*60)
            print("              CONFIGURADOR DE OTIMIZAÇÃO HÍBRIDA")
            print("="*60)
            print(f"Modelo Carregado: {CONFIG_GLOBAL['executavel']}")
            print("-" * 60)
            
            while True:
                try:
                    print("O que você deseja fazer?")
                    print(" [1] MAXIMIZAR (Buscar o MAIOR valor/lucro)")
                    print(" [2] MINIMIZAR (Buscar o MENOR valor/custo)")
                    escolha = input(">> Digite sua escolha (1 ou 2): ").strip()
                    if escolha == '1': objetivo_cliente = 'maximizar'; break
                    elif escolha == '2': objetivo_cliente = 'minimizar'; break
                    else: print("   [!] Opção inválida. Tente novamente.\n")
                except EOFError:
                    print("\nErro de entrada. Use flags."); sys.exit(1)

        print(f"\n--- INICIANDO OTIMIZAÇÃO: {objetivo_cliente.upper()} ---")
        print("(Você pode parar a qualquer momento com Ctrl+C que o relatório será gerado)")

        # FASE 1: OPTUNA
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        direcao = 'maximize' if objetivo_cliente == 'maximizar' else 'minimize'
        study = optuna.create_study(direction=direcao)
        
        print(f"Rodando Fase 1 (Exploração Global - {args.trials} tentativas)...")
        
        try:
            study.optimize(objective_optuna, n_trials=args.trials, show_progress_bar=True)
        except KeyboardInterrupt:
            print("\n⚠️ Interrupção na Fase 1! Usando o melhor resultado parcial...")
            status_execucao = "INTERROMPIDO"

        if len(study.trials) > 0:
            try:
                melhor_fase1 = study.best_trial.value
                params_fase1 = study.best_trial.params
                print(f"-> Melhor resultado da Fase 1: {melhor_fase1}")
            except ValueError:
                print("-> Nenhum trial válido completado na Fase 1.")
                params_fase1 = {p['nome']: p['valor_inicial'] for p in CONFIG_GLOBAL['parametros']}
                melhor_fase1 = 0
        else:
            params_fase1 = {p['nome']: p['valor_inicial'] for p in CONFIG_GLOBAL['parametros']}
            melhor_fase1 = 0

        # FASE 2: PATTERN SEARCH (Só se não parou na Fase 1)
        if status_execucao != "INTERROMPIDO":
            print(f"Rodando Fase 2 (Refinamento Local)...")
            params_finais, resultado_final = refinar_com_pattern_search(CONFIG_GLOBAL, params_fase1, objetivo_cliente)
        else:
            params_finais = params_fase1
            resultado_final = melhor_fase1

    except KeyboardInterrupt:
        print("\n\n⚠️  PARADA TOTAL SOLICITADA PELO USUÁRIO.")
        status_execucao = "INTERROMPIDO"
        if not params_finais: # Se parou antes de terminar fase 2
            params_finais = params_fase1
            resultado_final = melhor_fase1

    except Exception as e:
        print(f"\n❌ Erro Crítico: {e}")
        status_execucao = f"ERRO: {str(e)}"

    finally:
        tempo_gasto = time.time() - inicio_total

        if resultado_final is None:
            resultado_final = melhor_fase1
            params_finais = params_fase1

        dados = {
            'status': status_execucao,
            'modelo': CONFIG_GLOBAL.get('executavel', 'Desconhecido'),
            'objetivo': objetivo_cliente if objetivo_cliente else "Indefinido",
            'config_file': args.config,
            'tempo_total': tempo_gasto,
            'trials': args.trials,
            'resultado_fase1': melhor_fase1,
            'resultado_final': resultado_final,
            'params_finais': params_finais
        }

        print("\n" + "="*60)
        print(f"                 RESULTADO FINAL ({status_execucao})")
        print("="*60)
        if resultado_final is not None:
            print(f" OBJETIVO       : {str(objetivo_cliente).upper()}")
            print(f" VALOR FINAL    : {resultado_final}")
            print(f" TEMPO TOTAL    : {tempo_gasto:.2f}s")
            print("-" * 60)
            print(" PARÂMETROS IDEAIS:")
            print(json.dumps(params_finais, indent=4))
        else:
            print("Nenhum resultado foi gerado a tempo.")
        print("="*60)

        if resultado_final is not None:
            gerar_relatorio_arquivo(dados)