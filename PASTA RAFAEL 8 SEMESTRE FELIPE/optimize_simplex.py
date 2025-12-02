import subprocess
import json
import argparse
import sys
import time
import logging
from datetime import datetime
import numpy as np
from scipy.optimize import minimize

# ==============================================================================
# 1. FUNÇÃO BLACK BOX (Executa o .exe)
# ==============================================================================
def rodar_modelo_e_ler_saida(executavel, params_dict, lista_de_parametros):
    command = [executavel]
    try:
        for param_info in lista_de_parametros:
            nome_param = param_info['nome']
            valor = params_dict[nome_param]
            command.append(str(valor))
    except KeyError: return None
        
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        output_completo = result.stdout.strip()
        for line in output_completo.splitlines():
            if 'Valor de saída:' in line:
                try: return float(line.split(':')[-1].strip())
                except: pass
        return float(output_completo)
    except Exception: return None

# ==============================================================================
# 2. TRADUTOR (SCIPY <-> JSON)
# O Simplex só entende vetor de números. Precisamos converter tudo.
# ==============================================================================
def params_to_vector(params_dict, config_params):
    """Converte o dicionário legível para um vetor numérico [1.0, 2.5, 0.0]"""
    vector = []
    for p in config_params:
        val = params_dict[p['nome']]
        if p['tipo'] == 'categorico':
            # Converte texto para o índice (ex: 'medio' -> 1.0)
            try: vector.append(float(p['limites'].index(val)))
            except: vector.append(0.0)
        else:
            vector.append(float(val))
    return np.array(vector)

def vector_to_params(vector, config_params):
    """Converte o vetor numérico de volta para o dicionário do .exe"""
    params_dict = {}
    for i, p in enumerate(config_params):
        val_num = vector[i]
        
        if p['tipo'] == 'categorico':
            # Arredonda e pega o texto correspondente
            idx = int(round(val_num))
            idx = max(0, min(idx, len(p['limites']) - 1)) # Garante limites
            params_dict[p['nome']] = p['limites'][idx]
            
        elif p['tipo'] == 'inteiro':
            # Arredonda e aplica limites
            mini, maxi = p['limites']
            val_int = int(round(val_num))
            params_dict[p['nome']] = max(mini, min(val_int, maxi))
            
        elif p['tipo'] == 'float':
            mini, maxi = p['limites']
            params_dict[p['nome']] = max(mini, min(val_num, maxi))
            
    return params_dict

# ==============================================================================
# 3. ALGORITMO SIMPLEX (NELDER-MEAD)
# ==============================================================================
CONFIG_GLOBAL = {}
OBJETIVO_GLOBAL = 'maximizar'
MELHOR_RESULTADO_CACHE = -float('inf')

def funcao_objetivo_scipy(vector):
    """Esta é a função que o SciPy vai tentar MINIMIZAR"""
    global MELHOR_RESULTADO_CACHE
    
    # 1. Traduz vetor para parametros
    params = vector_to_params(vector, CONFIG_GLOBAL['parametros'])
    
    # 2. Roda o modelo
    resultado = rodar_modelo_e_ler_saida(CONFIG_GLOBAL['executavel'], params, CONFIG_GLOBAL['parametros'])
    
    # Se der erro no .exe, retornamos um valor "ruim" (infinito)
    if resultado is None:
        return float('inf') if OBJETIVO_GLOBAL == 'maximizar' else float('inf')

    # Atualiza cache para mostrar na tela
    if OBJETIVO_GLOBAL == 'maximizar':
        if resultado > MELHOR_RESULTADO_CACHE:
            MELHOR_RESULTADO_CACHE = resultado
            print(f"  [Simplex] Novo Recorde: {resultado:.4f}")
        return -resultado # SciPy só minimiza, então invertemos o sinal para maximizar
    else:
        if resultado < MELHOR_RESULTADO_CACHE or MELHOR_RESULTADO_CACHE == -float('inf'):
            MELHOR_RESULTADO_CACHE = resultado
            print(f"  [Simplex] Novo Recorde: {resultado:.4f}")
        return resultado

# ==============================================================================
# 4. GERADOR DE RELATÓRIO
# ==============================================================================
def gerar_relatorio(dados):
    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_arquivo = f"relatorio_simplex_{dados['modelo'].replace('.exe','')}_{data_hora}.txt"
    
    conteudo = f"""
================================================================================
                        RELATÓRIO DE OTIMIZAÇÃO (SIMPLEX NELDER-MEAD)
================================================================================
Data e Hora           : {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}
Modelo Otimizado      : {dados['modelo']}
Objetivo              : {dados['objetivo'].upper()}
Status                : {dados['status']}

--------------------------------------------------------------------------------
                            ESTATÍSTICAS
--------------------------------------------------------------------------------
Tempo Total           : {dados['tempo']:.2f} segundos
Número de Iterações   : {dados['iteracoes']}
VALOR FINAL ALCANÇADO : {dados['resultado_final']}

--------------------------------------------------------------------------------
                       MELHOR COMBINAÇÃO DE PARÂMETROS
--------------------------------------------------------------------------------
{json.dumps(dados['params_finais'], indent=4)}
================================================================================
"""
    with open(nome_arquivo, 'w', encoding='utf-8') as f: f.write(conteudo)
    print(f"\n✅ Relatório salvo: {nome_arquivo}")

# ==============================================================================
# 5. EXECUÇÃO PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=str, required=True)
    # Simplex não tem "trials" fixos, ele roda até convergir, mas podemos por limite
    parser.add_argument('--maxiter', type=int, default=100, help="Máximo de iterações do Simplex")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--max', action='store_true')
    group.add_argument('--min', action='store_true')
    args = parser.parse_args()

    try:
        with open(args.config, 'r', encoding='utf-8') as f: CONFIG_GLOBAL = json.load(f)
    except: sys.exit("Erro no config json")

    # Definição do Objetivo
    if args.max: OBJETIVO_GLOBAL = 'maximizar'
    elif args.min: OBJETIVO_GLOBAL = 'minimizar'
    else:
        while True:
            print("\n[SIMPLEX] Escolha o objetivo:")
            print(" 1. MAXIMIZAR")
            print(" 2. MINIMIZAR")
            try:
                if input(">> ").strip() == '1': OBJETIVO_GLOBAL='maximizar'; break
                if input(">> ").strip() == '2': OBJETIVO_GLOBAL='minimizar'; break
            except: sys.exit(0)
            
    # Configura valor inicial cache (para printar corretamente)
    if OBJETIVO_GLOBAL == 'minimizar': MELHOR_RESULTADO_CACHE = float('inf')
    else: MELHOR_RESULTADO_CACHE = -float('inf')

    print(f"\n--- INICIANDO SIMPLEX (NELDER-MEAD) ---")
    print(f"Alvo: {CONFIG_GLOBAL['executavel']} | Modo: {OBJETIVO_GLOBAL.upper()}")
    
    # Ponto Inicial (x0) - Pega do JSON
    params_iniciais_dict = {p['nome']: p['valor_inicial'] for p in CONFIG_GLOBAL['parametros']}
    x0 = params_to_vector(params_iniciais_dict, CONFIG_GLOBAL['parametros'])
    
    inicio = time.time()
    status_msg = "SUCESSO"
    
    try:
        # CHAMA O SCIPY MINIMIZE (COM MÉTODO NELDER-MEAD)
        res = minimize(
            funcao_objetivo_scipy, 
            x0, 
            method='Nelder-Mead',
            options={'maxiter': args.maxiter, 'disp': True} # disp=True mostra log do scipy
        )
        
        # Recupera resultados
        vetor_final = res.x
        params_finais = vector_to_params(vetor_final, CONFIG_GLOBAL['parametros'])
        
        # Recalcula valor final exato
        resultado_final = rodar_modelo_e_ler_saida(CONFIG_GLOBAL['executavel'], params_finais, CONFIG_GLOBAL['parametros'])

    except KeyboardInterrupt:
        print("\n⚠️ Interrompido pelo usuário! Salvando melhor estado...")
        status_msg = "INTERROMPIDO"
        resultado_final = MELHOR_RESULTADO_CACHE
        # Como não temos o vetor exato do crash, usamos o x0 ou o último printado visualmente
        # (Limitação do scipy: ele não devolve o x corrente no crash facilmente)
        params_finais = "Verificar último log de recorde" 

    tempo_gasto = time.time() - inicio

    print("\n" + "="*60)
    print(f" RESULTADO SIMPLEX ({status_msg})")
    print(f" VALOR FINAL: {resultado_final}")
    print(f" TEMPO: {tempo_gasto:.2f}s")
    if status_msg != "INTERROMPIDO":
        print(json.dumps(params_finais, indent=4))
    print("="*60)

    if status_msg != "INTERROMPIDO":
        gerar_relatorio({
            'modelo': CONFIG_GLOBAL['executavel'],
            'objetivo': OBJETIVO_GLOBAL,
            'status': status_msg,
            'tempo': tempo_gasto,
            'iteracoes': res.nit if 'nit' in res else args.maxiter,
            'resultado_final': resultado_final,
            'params_finais': params_finais
        })