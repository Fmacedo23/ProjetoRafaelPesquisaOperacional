import argparse
import subprocess
import sys

def run_modelo(args):
    """
    Função que constrói e executa o comando para o modelo10.exe
    usando TODOS os argumentos recebidos.
    """
    
    executable = 'modelo10.exe' 
    
    # 1. Constrói a lista de comandos a partir dos 'args'
    #    Converte todos os argumentos para string, na ordem correta.
    command = [
        executable,
        args.x1,
        str(args.x2),
        str(args.x3),
        str(args.x4),
        str(args.x5),
        str(args.x6),
        str(args.x7),
        str(args.x8),
        str(args.x9),
        str(args.x10)
    ]
    
    print(f"--- Iniciando Autotune ---")
    print(f"Executando comando: {' '.join(command)}")
    print("--- Saída do modelo10.exe ---")
    
    try:
        # 2. Executa o processo
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        # 3. Imprime a saída padrão (stdout) do seu .exe
        #    É AQUI QUE O RESULTADO DO SEU MODELO VAI APARECER
        print(result.stdout)
        
        # Imprime se houver alguma saída de erro (stderr)
        if result.stderr:
            print("--- Erros do modelo10.exe (stderr) ---")
            print(result.stderr)

    except FileNotFoundError:
        print(f"ERRO: Não foi possível encontrar o arquivo '{executable}'.")
    except subprocess.CalledProcessError as e:
        # Se o .exe falhar, ele vai imprimir a mensagem de "Uso:" aqui
        print(f"ERRO: O 'modelo10.exe' falhou (retornou código de erro).")
        print("Saída do Erro (stderr):")
        print(e.stderr)
        print("Saída Padrão (stdout - pode conter a mensagem de 'Uso:'):")
        print(e.stdout)
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

# -----------------------------------------------------------------
# O "AUTOTUNE" (Leitor de Parâmetros) - VERSÃO CORRETA
# -----------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lançador (Autotune) para o modelo10.exe")

    # 1. Agora definimos os 10 argumentos que o .exe realmente quer
    
    # x1: texto em {baixo, medio, médio, alto}
    parser.add_argument('--x1', 
                        type=str, 
                        required=True, 
                        choices=['baixo', 'medio', 'médio', 'alto'],
                        help="x1: texto em {baixo, medio, médio, alto}")
    
    # x2, x3: inteiros de 1 a 100
    parser.add_argument('--x2', type=int, required=True, help="x2: inteiro de 1 a 100")
    parser.add_argument('--x3', type=int, required=True, help="x3: inteiro de 1 a 100")
    
    # x4..x10: inteiros de 0 a 100
    parser.add_argument('--x4', type=int, required=True, help="x4: inteiro de 0 a 100")
    parser.add_argument('--x5', type=int, required=True, help="x5: inteiro de 0 a 100")
    parser.add_argument('--x6', type=int, required=True, help="x6: inteiro de 0 a 100")
    parser.add_argument('--x7', type=int, required=True, help="x7: inteiro de 0 a 100")
    parser.add_argument('--x8', type=int, required=True, help="x8: inteiro de 0 a 100")
    parser.add_argument('--x9', type=int, required=True, help="x9: inteiro de 0 a 100")
    parser.add_argument('--x10', type=int, required=True, help="x10: inteiro de 0 a 100")

    # 2. Leia os argumentos
    args = parser.parse_args()

    # 3. Chame a função que executa o .exe
    run_modelo(args)