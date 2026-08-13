import pandas as pd
from pathlib import Path

def update_data():
    # url do csv com dados atualizados da epoca atual
    url = "https://www.football-data.co.uk/mmz4281/2627/P1.csv"
    
    # caminho para guardar csv atualizado
    file_path = Path("data/raw/LigaPortugal26-27.csv")
    
    print("Downloading ultimos jogos da epoca atual...")
    
    try:
        df = pd.read_csv(url) # le o csv para um dataframe
        df_old = pd.read_csv(file_path) # le o csv antigo para comparar
        
        # verificar se ha dados novos comparando com o csv antigo
        if df.equals(df_old):
            print("Dados ja estao atualizados.")
            return
        
        # guarda o csv atualizado
        df.to_csv(file_path, index=False)
        
        new_real_games = df['FTR'].notna().sum()
        old_real_games = df_old['FTR'].notna().sum()
        diff = new_real_games - old_real_games
        
        if diff > 0:
            print(f"Dados atualizados. Foram adicionados {diff} jogo(s).")
        else:
            print("Histórico atualizado (reset de jogos futuros), mas nenhum jogo novo adicionado.")
        
    except Exception as e:
        print(f"Erro inesperado: {e}")

if __name__ == "__main__":
    update_data()
    