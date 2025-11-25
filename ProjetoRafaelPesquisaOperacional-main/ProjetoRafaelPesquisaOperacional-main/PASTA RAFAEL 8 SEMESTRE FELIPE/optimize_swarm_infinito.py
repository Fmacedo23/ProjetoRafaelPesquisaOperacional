import subprocess
import json
import argparse
import sys
import time
import os
from datetime import datetime
import optuna

# --- FUNÇÃO BLACK BOX ---
def rodar_modelo_e_ler_saida(executavel, params_dict, lista_de_parametros):
    command = [executavel]
    try:
        for param_info in lista_de_parametros:
            valor = params_dict[param_info['nome']]
            command.append(str(valor))
    except KeyError: return None
        
    try:
        if not os.path.exists(executavel): return None
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        for line in output.splitlines():
            if 'Valor de saída:' in line:
                return float(line.split(':')[-1].strip())
        if output: return float(output)
        return None
    except: return None

# --- MENU INTELIGENTE ---
def menu_inteligente(config_nome):
    print("\n" + "="*60)
    print("           SWARM / OPTUNA (MODO INFINITO)")
    print("="*60)
    print(f"Modelo: {config_nome}")
    print("-" * 60)
    while True:
        try:
            print("\nObjetivo?")
            print("  [1] MAXIMIZAR")
            print("  [2] MINIMIZAR")
            entrada = input(">> Digite 1 ou 2: ").strip()
            if entrada == '1': return 'maximizar'
            elif entrada == '2': return 'minimizar'
        except KeyboardInterrupt: sys.exit(0)
        except EOFError: sys.exit(1)

# --- LÓGICA SWARM ---
CONFIG_GLOBAL = {}

def objective(trial):
    config = CONFIG_GLOBAL
    params = {}
    for p in config['parametros']:
        if p['tipo'] == 'categorico':
            params[p['nome']] = trial.suggest_categorical(p['nome'], p['limites'])
        elif p['tipo'] == 'inteiro':
            params[p['nome']] = trial.suggest_int(p['nome'], p['limites'][0], p['limites'][1], step=p.get('passo_sugestao', 1))
        elif p['tipo'] == 'float':
            params[p['nome']] = trial.suggest_float(p['nome'], p['limites'][0], p['limites'][1], step=p.get('passo_sugestao', 0.1))
            
    res = rodar_modelo_e_ler_saida(config['executavel'], params, config['parametros'])
    if res is None: raise optuna.exceptions.TrialPruned()
    return res

# --- GERADOR RELATÓRIO ---
def gerar_relatorio_arquivo(dados):
    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = f"relatorio_SWARM_{dados['modelo'].replace('.exe', '')}_{data_hora}.txt"
    
    conteudo = f"""
================================================================================
                  RELATÓRIO: SWARM INFINITO (OPTUNA)
================================================================================
Data           : {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
Modelo         : {dados['modelo']}
Objetivo       : {dados['objetivo'].upper()}
Status         : {dados['status']}
Tentativas     : {dados['trials']}
--------------------------------------------------------------------------------
MELHOR RESULTADO: {dados['resultado']}
Tempo Total     : {dados['tempo']:.2f}s
--------------------------------------------------------------------------------
PARÂMETROS IDEAIS:
{json.dumps(dados['params'], indent=4)}
================================================================================
"""
    try: 
        with open(nome_arquivo, 'w', encoding='utf-8') as f: f.write(conteudo)
        print(f"\n📄 Relatório salvo: {nome_arquivo}")
    except: pass

# --- EXECUÇÃO ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', required=True)
    parser.add_argument('--max', action='store_true')
    parser.add_argument('--min', action='store_true')
    args = parser.parse_args()

    try:
        with open(args.config, 'r', encoding='utf-8') as f: CONFIG_GLOBAL = json.load(f)
    except: sys.exit(1)
    
    obj = None
    if args.max: obj = 'maximizar'
    elif args.min: obj = 'minimizar'
    else: obj = menu_inteligente(CONFIG_GLOBAL['executavel'])

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    direction = 'maximize' if obj == 'maximizar' else 'minimize'
    
    print(f"\n>>> INICIANDO SWARM INFINITO <<<")
    print(f"Objetivo: {obj.upper()}")
    print("(Pressione Ctrl+C para parar e gerar relatório)")
    
    inicio = time.time()
    study = optuna.create_study(direction=direction)
    status = "CONCLUÍDO"
    
    try:
        # n_trials=None significa INFINITO
        study.optimize(objective, n_trials=None, show_progress_bar=False) 
    except KeyboardInterrupt:
        print("\n\n🛑 PARADA MANUAL DETECTADA.")
        status = "INTERROMPIDO PELO USUÁRIO"

    tempo = time.time() - inicio
    
    best_val = 0
    best_params = {}
    
    if len(study.trials) > 0:
        try:
            best_val = study.best_value
            best_params = study.best_params
        except: pass
    
    print("\n" + "="*50)
    print(f"RESULTADO FINAL ({obj.upper()})")
    print(f"Valor: {best_val}")
    print(f"Tempo: {tempo:.2f}s")
    print(json.dumps(best_params, indent=4))
    print("="*50)
    
    gerar_relatorio_arquivo({
        'modelo': CONFIG_GLOBAL['executavel'],
        'objetivo': obj,
        'resultado': best_val,
        'params': best_params,
        'tempo': tempo,
        'status': status,
        'trials': len(study.trials)
    })