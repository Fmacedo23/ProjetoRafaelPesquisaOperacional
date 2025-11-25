import subprocess
import copy
import json
import argparse
import sys
import time
import os
from datetime import datetime

# ==============================================================================
# 1. FUNÇÃO BLACK BOX (Executa o .exe)
# ==============================================================================
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
        
        # Tenta ler formato "Valor de saída:"
        for line in output.splitlines():
            if 'Valor de saída:' in line:
                return float(line.split(':')[-1].strip())
        
        # Tenta ler número puro
        if output: return float(output)
        return None
    except: return None

# ==============================================================================
# 2. GERADOR DE RELATÓRIO
# ==============================================================================
def gerar_relatorio_arquivo(dados):
    """Gera um arquivo .txt com os dados da otimização"""
    data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_modelo = dados['modelo'].replace('.exe', '')
    nome_arquivo = f"relatorio_PATTERN_{nome_modelo}_{data_hora}.txt"
    
    conteudo = f"""
================================================================================
               RELATÓRIO: PATTERN SEARCH INTELIGENTE (INFINITO)
================================================================================
Data           : {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
Modelo         : {dados['modelo']}
Objetivo       : {dados['objetivo'].upper()}
Status         : {dados['status']}
Iterações      : {dados['iteracoes']}
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

# ==============================================================================
# 3. LÓGICA PATTERN SEARCH (ADAPTATIVA + INFINITA)
# ==============================================================================
def pattern_search_infinito(config, objetivo_escolhido):
    executavel = config['executavel']
    params_lista = config['parametros']
    
    # Inicializa passos (smart step)
    passos_atuais = {}
    for p in params_lista:
        passos_atuais[p['nome']] = p.get('passo', 1) if p['tipo'] != 'categorico' else None

    # Ponto de partida
    params_iniciais = {p['nome']: p['valor_inicial'] for p in params_lista}
    
    print(f"\n>>> INICIANDO PATTERN SEARCH (SMART & INFINITO) <<<")
    print(f"Objetivo: {objetivo_escolhido.upper()}")
    print("(Pressione Ctrl+C a qualquer momento para PARAR e GERAR O RELATÓRIO)")
    
    valor_inicial = rodar_modelo_e_ler_saida(executavel, params_iniciais, params_lista)
    
    if valor_inicial is None:
        print("ERRO: Falha ao rodar o modelo inicial.")
        return params_iniciais, 0, 0, "ERRO"

    print(f"-> Valor Inicial: {valor_inicial}")

    melhores_params = copy.deepcopy(params_iniciais)
    melhor_resultado = valor_inicial
    
    iteracao = 0
    status = "CONCLUÍDO"

    try:
        while True: # Loop Infinito
            iteracao += 1
            houve_melhoria = False
            
            for p in params_lista:
                nome = p['nome']
                tipo = p['tipo']
                base = copy.deepcopy(melhores_params)
                
                candidatos = []
                if tipo == 'categorico':
                    candidatos = [v for v in p['limites'] if v != base[nome]]
                else:
                    passo = passos_atuais[nome]
                    # Proteção passo mínimo
                    if tipo == 'inteiro' and passo < 1: passo = 1
                    if tipo == 'float' and passo < 0.001: passo = 0.001

                    vals = [base[nome] + passo, base[nome] - passo]
                    if tipo == 'inteiro': vals = [int(round(v)) for v in vals]
                    mini, maxi = p['limites']
                    candidatos = [v for v in vals if mini <= v <= maxi]

                for val_teste in candidatos:
                    teste = copy.deepcopy(base)
                    teste[nome] = val_teste
                    res = rodar_modelo_e_ler_saida(executavel, teste, params_lista)
                    if res is None: continue

                    melhorou = False
                    if objetivo_escolhido == 'maximizar' and res > melhor_resultado: melhorou = True
                    if objetivo_escolhido == 'minimizar' and res < melhor_resultado: melhorou = True
                    
                    if melhorou:
                        print(f"  [Iteração {iteracao}] ✨ MELHORIA! {nome}: {val_teste} (Passo {passos_atuais.get(nome)}) -> {res}")
                        melhor_resultado = res
                        melhores_params = copy.deepcopy(teste)
                        houve_melhoria = True
                        base = copy.deepcopy(melhores_params) 

            if not houve_melhoria:
                # Tenta refinar o passo antes de desistir
                reduziu_algum = False
                for p in params_lista:
                    nome = p['nome']
                    if p['tipo'] == 'inteiro' and passos_atuais[nome] > 1:
                        passos_atuais[nome] = max(1, int(passos_atuais[nome] / 2))
                        reduziu_algum = True
                    elif p['tipo'] == 'float' and passos_atuais[nome] > 0.001:
                        passos_atuais[nome] = passos_atuais[nome] / 2.0
                        reduziu_algum = True
                
                if reduziu_algum:
                    print(f"  [Iteração {iteracao}] Refinando passos para maior precisão...")
                else:
                    # Se já refinou tudo, fica monitorando
                    sys.stdout.write(f"\r  [Iteração {iteracao}] Topo alcançado ({melhor_resultado}). Monitorando...")
                    sys.stdout.flush()
                    time.sleep(0.5) 
                
    except KeyboardInterrupt:
        print("\n\n🛑 PARADA MANUAL (Ctrl+C) DETECTADA!")
        status = "INTERROMPIDO PELO USUÁRIO"
    
    return melhores_params, melhor_resultado, status, iteracao

# ==============================================================================
# 4. EXECUÇÃO PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', required=True, help="Arquivo JSON")
    parser.add_argument('--max', action='store_true', help="Maximizar")
    parser.add_argument('--min', action='store_true', help="Minimizar")
    args = parser.parse_args()

    try:
        with open(args.config, 'r', encoding='utf-8') as f: CONFIG = json.load(f)
    except: 
        print("Erro ao abrir arquivo de configuração."); sys.exit(1)
    
    # Lógica de Escolha
    obj = None
    if args.max: obj = 'maximizar'
    elif args.min: obj = 'minimizar'
    else:
        print("\n" + "="*50)
        print(f"MODELO: {CONFIG['executavel']}")
        print("="*50)
        while True:
            try:
                print("Qual o seu objetivo?")
                print(" [1] MAXIMIZAR (Maior Valor)")
                print(" [2] MINIMIZAR (Menor Valor)")
                escolha = input(">> Digite 1 ou 2: ").strip()
                if escolha == '1': obj = 'maximizar'; break
                elif escolha == '2': obj = 'minimizar'; break
                else: print("Opção inválida.\n")
            except KeyboardInterrupt: sys.exit(0)

    # Inicia Cronômetro
    inicio = time.time()
    
    # Roda o motor
    params, res, status, iters = pattern_search_infinito(CONFIG, obj)
    
    tempo = time.time() - inicio

    # Prepara dados para o relatório
    dados_relatorio = {
        'modelo': CONFIG['executavel'],
        'config_file': args.config,
        'objetivo': obj,
        'status': status,
        'tempo_total': tempo,
        'iteracoes': iters,
        'resultado': res,
        'params': params
    }

    # Exibe na Tela
    print("\n" + "="*50)
    print(f"RESULTADO FINAL ({obj.upper()})")
    print(f"Valor: {res}")
    print(f"Tempo: {tempo:.2f}s")
    print(json.dumps(params, indent=4))
    print("="*50)

    # Gera o arquivo
    gerar_relatorio_arquivo(dados_relatorio)