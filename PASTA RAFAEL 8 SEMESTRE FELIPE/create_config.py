import json

def criar_configuracao():
    print("--- Criador de Configuração de Otimização ---")
    print("Vamos criar o arquivo .json que descreve o seu modelo.\n")
    
    config = {}
    
    # 1. Perguntar o nome do executável
    executavel = input("Qual o nome do arquivo executável? (ex: modelo10.exe): ")
    config['executavel'] = executavel

    # 2. Perguntar o objetivo
    while True:
        objetivo = input("Qual o objetivo da otimização? [maximizar/minimizar]: ").strip().lower()
        if objetivo in ['maximizar', 'minimizar']:
            config['objetivo'] = objetivo
            break
        print("Erro: Resposta inválida. Digite 'maximizar' ou 'minimizar'.")

    # 3. Perguntar a quantidade de parâmetros
    while True:
        try:
            num_params = int(input("Quantos parâmetros o executável tem?: "))
            if num_params > 0:
                break
            print("Erro: Digite um número positivo.")
        except ValueError:
            print("Erro: Digite um número válido.")
    
    config['parametros'] = []

    # 4. Loop para configurar cada parâmetro
    for i in range(num_params):
        print(f"\n--- Configurando Parâmetro #{i+1} de {num_params} ---")
        param = {}
        
        # Nome do Parâmetro
        param['nome'] = input(f"Nome do parâmetro #{i+1} (ex: x1, temperatura, etc.): ").strip()
        
        # Tipo do Parâmetro
        while True:
            tipo = input(f"Tipo do param '{param['nome']}' [inteiro/float/categorico]: ").strip().lower()
            if tipo in ['inteiro', 'float', 'categorico']:
                param['tipo'] = tipo
                break
            print("Erro: Tipo inválido.")
        
        # --- Detalhes para tipos numéricos ---
        if tipo == 'inteiro' or tipo == 'float':
            # Limites (Min, Max)
            while True:
                try:
                    lim_str = input(f"Limites (min, max) para '{param['nome']}' (ex: 1, 100): ")
                    lim_min_str, lim_max_str = lim_str.split(',')
                    lim_min = float(lim_min_str) if tipo == 'float' else int(lim_min_str)
                    lim_max = float(lim_max_str) if tipo == 'float' else int(lim_max_str)
                    param['limites'] = [lim_min, lim_max]
                    break
                except Exception:
                    print("Erro. Formato inválido. Use: numero,numero (ex: 1,100)")
            
            # Valor Inicial
            while True:
                try:
                    val_ini_str = input(f"Valor inicial para '{param['nome']}' (ex: 50): ")
                    val_ini = float(val_ini_str) if tipo == 'float' else int(val_ini_str)
                    if lim_min <= val_ini <= lim_max:
                        param['valor_inicial'] = val_ini
                        break
                    print(f"Erro: O valor inicial deve estar entre {lim_min} e {lim_max}.")
                except Exception:
                    print("Erro: Digite um número válido.")

            # Passo de otimização
            while True:
                try:
                    passo_str = input(f"Passo de otimização para '{param['nome']}' (ex: 5): ")
                    passo = float(passo_str) if tipo == 'float' else int(passo_str)
                    param['passo'] = passo
                    break
                except Exception:
                    print("Erro: Digite um número válido.")

        # --- Detalhes para tipo categórico ---
        elif tipo == 'categorico':
            # Limites (lista de strings)
            limites_str = input(f"Opções para '{param['nome']}' (separadas por vírgula) (ex: baixo,medio,alto): ")
            param['limites'] = [s.strip() for s in limites_str.split(',')]
            
            # Valor Inicial
            while True:
                val_ini = input(f"Valor inicial para '{param['nome']}' (uma das opções acima, ex: medio): ").strip()
                if val_ini in param['limites']:
                    param['valor_inicial'] = val_ini
                    break
                print(f"Erro: O valor deve ser exatamente uma das opções: {param['limites']}")
        
        config['parametros'].append(param)
    
    print("\n--- Configuração Concluída ---")
    
    # 5. Salvar o arquivo
    while True:
        nome_arquivo_json = input("\nDigite o nome para salvar este arquivo (ex: config_modelo10.json): ").strip()
        if not nome_arquivo_json.endswith('.json'):
            nome_arquivo_json += '.json'
        
        try:
            with open(nome_arquivo_json, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            
            print(f"\nArquivo '{nome_arquivo_json}' salvo com sucesso!")
            print("-------------------------------------------------")
            print(f"Para rodar a otimização, execute:")
            print(f"python optimize_generic.py --config {nome_arquivo_json}")
            print("-------------------------------------------------")
            break
        except Exception as e:
            print(f"Erro ao salvar o arquivo: {e}. Tente um nome de arquivo diferente.")

if __name__ == "__main__":
    criar_configuracao()