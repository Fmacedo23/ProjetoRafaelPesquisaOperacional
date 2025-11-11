import subprocess
import copy

# -----------------------------------------------------------------
# 1. OBJETIVO DA OTIMIZAÇÃO: "minimizar" ou "maximizar" o valor?
#    (Mude aqui conforme sua necessidade)
OBJETIVO = 'maximizar' 

# -----------------------------------------------------------------
# 2. CONFIGURAÇÕES INICIAIS
#    Este é o "chute" inicial que o otimizador vai usar.
# -----------------------------------------------------------------
# Ponto de partida
params_iniciais = {
    'x1': 'medio',
    'x2': 50,
    'x3': 50,
    'x4': 50,
    'x5': 50,
    'x6': 50,
    'x7': 50,
    'x8': 50,
    'x9': 50,
    'x10': 50,
}

# Parâmetros para os inteiros
# O 'passo' (step) que o algoritmo vai usar para testar
STEP_SIZE_INTEIROS = 5 # Vai testar (valor_atual + 5) e (valor_atual - 5)

# Limites dos parâmetros (baseado na mensagem de 'Uso:')
LIMITES = {
    'x1': ['baixo', 'medio', 'médio', 'alto'],
    'x2': (1, 100),
    'x3': (1, 100),
    'x4': (0, 100),
    'x5': (0, 100),
    'x6': (0, 100),
    'x7': (0, 100),
    'x8': (0, 100),
    'x9': (0, 100),
    'x10': (0, 100),
}

# -----------------------------------------------------------------
# 3. FUNÇÃO "BLACK BOX" (Nosso modelo10.exe)
#    Esta função executa o .exe e PARSEIA (lê) o resultado
# -----------------------------------------------------------------
def rodar_modelo_e_ler_saida(params):
    """Executa o modelo10.exe com os parâmetros dados e retorna o float da saída."""
    
    command = [
        'modelo10.exe',
        params['x1'],
        str(params['x2']),
        str(params['x3']),
        str(params['x4']),
        str(params['x5']),
        str(params['x6']),
        str(params['x7']),
        str(params['x8']),
        str(params['x9']),
        str(params['x10']),
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        # Parseia a saída "Valor de saída: 65.43"
        for line in result.stdout.splitlines():
            if 'Valor de saída:' in line:
                valor_str = line.split(':')[-1].strip()
                return float(valor_str)
        
        # Se não achou "Valor de saída:", é um erro
        print(f"ERRO: Não achei 'Valor de saída:' no output do modelo.")
        print(f"Saída: {result.stdout}")
        return None

    except Exception as e:
        print(f"ERRO ao executar o modelo10.exe: {e}")
        return None

# -----------------------------------------------------------------
# 4. O ALGORITMO DE PATTERN SEARCH (Busca por Coordenadas)
# -----------------------------------------------------------------
def otimizar():
    print(f"--- Iniciando Otimização (Pattern Search) ---")
    print(f"Objetivo: {OBJETIVO} o 'Valor de saída'")
    
    # Começa com os parâmetros iniciais
    melhores_params = copy.deepcopy(params_iniciais)
    melhor_resultado = rodar_modelo_e_ler_saida(melhores_params)
    
    if melhor_resultado is None:
        print("Falha ao rodar o modelo com parâmetros iniciais. Abortando.")
        return

    print(f"Resultado Inicial: {melhor_resultado} com params: {melhores_params['x1']}, {melhores_params['x2']}...")

    # Loop principal de otimização
    # Vai continuar rodando enquanto encontrar alguma melhoria
    iteracao = 0
    while True:
        iteracao += 1
        print(f"\n--- Iteração {iteracao} ---")
        houve_melhoria = False
        
        # 'params_iteracao' começa como os melhores params da rodada anterior
        params_iteracao = copy.deepcopy(melhores_params)

        # 1. Otimiza o parâmetro Categórico (x1)
        for valor_x1 in LIMITES['x1']:
            if valor_x1 == params_iteracao['x1']: # Já testamos esse
                continue
            
            params_teste = copy.deepcopy(params_iteracao)
            params_teste['x1'] = valor_x1
            
            resultado_teste = rodar_modelo_e_ler_saida(params_teste)
            
            if (OBJETIVO == 'maximizar' and resultado_teste > melhor_resultado) or \
               (OBJETIVO == 'minimizar' and resultado_teste < melhor_resultado):
                
                print(f"  Melhoria! x1: {params_teste['x1']} -> Resultado: {resultado_teste}")
                melhor_resultado = resultado_teste
                melhores_params = copy.deepcopy(params_teste)
                houve_melhoria = True
        
        # 2. Otimiza os parâmetros Inteiros (x2 a x10)
        for key in [f'x{i}' for i in range(2, 11)]: # 'x2' até 'x10'
            params_iteracao = copy.deepcopy(melhores_params) # Pega os params mais atuais
            
            # Testa o "passo" para CIMA e para BAIXO
            for direcao in [STEP_SIZE_INTEIROS, -STEP_SIZE_INTEIROS]:
                valor_atual = params_iteracao[key]
                valor_teste = valor_atual + direcao
                
                # Garante que o valor está dentro dos limites
                min_lim, max_lim = LIMITES[key]
                valor_teste = max(min_lim, min(valor_teste, max_lim))
                
                if valor_teste == valor_atual: # Se o passo não mudou (ex: já estava no limite)
                    continue

                params_teste = copy.deepcopy(params_iteracao)
                params_teste[key] = valor_teste
                
                resultado_teste = rodar_modelo_e_ler_saida(params_teste)
                
                if (OBJETIVO == 'maximizar' and resultado_teste > melhor_resultado) or \
                   (OBJETIVO == 'minimizar' and resultado_teste < melhor_resultado):
                    
                    print(f"  Melhoria! {key}: {valor_teste} -> Resultado: {resultado_teste}")
                    melhor_resultado = resultado_teste
                    melhores_params = copy.deepcopy(params_teste)
                    houve_melhoria = True

        # 3. Critério de Parada
        if not houve_melhoria:
            print("\nNenhuma melhoria encontrada nesta iteração. Otimização concluída.")
            break
            
    # Fim do loop
    print("\n--- OTIMIZAÇÃO FINALIZADA ---")
    print(f"Melhor resultado ({OBJETIVO}izado): {melhor_resultado}")
    print("Encontrado com os seguintes parâmetros:")
    print(melhores_params)

# -----------------------------------------------------------------
# 5. PONTO DE ENTRADA
# -----------------------------------------------------------------
if __name__ == "__main__":
    otimizar()