import subprocess
import copy
import json
import argparse
import sys

def rodar_modelo_e_ler_saida(executavel, params_dict, lista_de_parametros):
    """
    Executa o modelo com os parâmetros dados (na ordem correta) 
    e retorna o float da saída.
    
    *** AGORA COM LÓGICA DE PARSING MELHORADA ***
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
        # 1. Executa o comando
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        output_completo = result.stdout.strip()
        
        # --- INÍCIO DA NOVA LÓGICA DE PARSING ---
        
        # 2. Tenta o formato "Valor de saída: 123.45" (para modelo10.exe)
        for line in output_completo.splitlines():
            if 'Valor de saída:' in line:
                try:
                    valor_str = line.split(':')[-1].strip()
                    return float(valor_str)
                except Exception:
                    print(f"ERRO: Achou 'Valor de saída:' mas falhou ao converter o valor em '{line}'")
                    return None

        # 3. Se não achou, tenta assumir que a SAÍDA INTEIRA é o número (para modelo2.exe)
        try:
            valor_float = float(output_completo)
            return valor_float
        except ValueError:
            # Se não for um número E não for o formato "Valor de saída:"...
            print(f"ERRO: A saída não é um número e nem o formato 'Valor de saída:'.")
            print(f"Comando: {' '.join(command)}")
            print(f"Saída: {output_completo}")
            return None
        # --- FIM DA NOVA LÓGICA DE PARSING ---

    except subprocess.CalledProcessError as e:
        # Isso acontece se o .exe falhar (retornar código != 0)
        print(f"ERRO: O executável '{executavel}' falhou (retornou código de erro).")
        print(f"Comando: {' '.join(command)}")
        print(f"Saída (stderr - erros): {e.stderr}")
        print(f"Saída (stdout - talvez a msg de 'Uso:'): {e.stdout}")
        return None
    except Exception as e:
        print(f"ERRO ao executar o modelo: {e}")
        return None

#
# O RESTO DO SCRIPT (OTIMIZAR) É EXATAMENTE O MESMO
#

def otimizar(config):
    """
    Executa o Pattern Search genérico baseado no arquivo de configuração.
    """
    
    executavel = config['executavel']
    objetivo = config['objetivo']
    lista_de_parametros = config['parametros'] # Esta lista define a ORDEM

    print(f"--- Iniciando Otimização (Pattern Search Genérico) ---")
    print(f"Executável: {executavel}")
    print(f"Objetivo: {objetivo} o 'Valor de saída'")
    
    params_iniciais = {}
    for param in lista_de_parametros:
        params_iniciais[param['nome']] = param['valor_inicial']
        
    melhores_params = copy.deepcopy(params_iniciais)
    melhor_resultado = rodar_modelo_e_ler_saida(executavel, melhores_params, lista_de_parametros)
    
    if melhor_resultado is None:
        print("Falha ao rodar o modelo com parâmetros iniciais. Abortando.")
        return

    print(f"Resultado Inicial: {melhor_resultado} (com {len(lista_de_parametros)} params)")

    iteracao = 0
    while True:
        iteracao += 1
        print(f"\n--- Iteração {iteracao} ---")
        houve_melhoria = False
        
        for param_info in lista_de_parametros:
            
            nome_param = param_info['nome']
            tipo_param = param_info['tipo']
            
            params_base_iteracao = copy.deepcopy(melhores_params)

            if tipo_param == 'categorico':
                limites = param_info['limites']
                for valor_teste in limites:
                    if valor_teste == params_base_iteracao[nome_param]:
                        continue
                    
                    params_teste = copy.deepcopy(params_base_iteracao)
                    params_teste[nome_param] = valor_teste
                    
                    resultado_teste = rodar_modelo_e_ler_saida(executavel, params_teste, lista_de_parametros)
                    if resultado_teste is None: continue

                    if (objetivo == 'maximizar' and resultado_teste > melhor_resultado) or \
                       (objetivo == 'minimizar' and resultado_teste < melhor_resultado):
                        
                        print(f"  Melhoria! {nome_param}: {valor_teste} -> Resultado: {resultado_teste}")
                        melhor_resultado = resultado_teste
                        melhores_params = copy.deepcopy(params_teste)
                        houve_melhoria = True

            elif tipo_param == 'inteiro' or tipo_param == 'float':
                passo = param_info['passo']
                min_lim, max_lim = param_info['limites']
                
                for direcao in [passo, -passo]:
                    params_base_direcao = copy.deepcopy(melhores_params) 
                    valor_atual = params_base_direcao[nome_param]
                    valor_teste = valor_atual + direcao
                    
                    if tipo_param == 'inteiro':
                        valor_teste = int(round(valor_teste))
                    
                    valor_teste = max(min_lim, min(valor_teste, max_lim)) 
                    
                    if valor_teste == valor_atual:
                        continue

                    params_teste = copy.deepcopy(params_base_direcao)
                    params_teste[nome_param] = valor_teste
                    
                    resultado_teste = rodar_modelo_e_ler_saida(executavel, params_teste, lista_de_parametros)
                    if resultado_teste is None: continue

                    if (objetivo == 'maximizar' and resultado_teste > melhor_resultado) or \
                       (objetivo == 'minimizar' and resultado_teste < melhor_resultado):
                        
                        print(f"  Melhoria! {nome_param}: {valor_teste} -> Resultado: {resultado_teste}")
                        melhor_resultado = resultado_teste
                        melhores_params = copy.deepcopy(params_teste)
                        houve_melhoria = True
            
        if not houve_melhoria:
            print("\nNenhuma melhoria encontrada nesta iteração. Otimização concluída.")
            break
            
    print("\n--- OTIMIZAÇÃO FINALIZADA ---")
    print(f"Melhor resultado ({objetivo}izado): {melhor_resultado}")
    print("Encontrado com os seguintes parâmetros:")
    print(json.dumps(melhores_params, indent=4))

# --- Ponto de Entrada do Script ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Otimizador Genérico (Pattern Search)")
    parser.add_argument('-c', '--config', 
                        type=str, 
                        required=True, 
                        help="Caminho para o arquivo .json de configuração do modelo.")
    
    args = parser.parse_args()
    
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        print(f"ERRO: Arquivo de configuração não encontrado: {args.config}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"ERRO: O arquivo de configuração '{args.config}' não é um JSON válido.")
        sys.exit(1)
    
    otimizar(config_data)