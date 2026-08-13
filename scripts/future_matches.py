import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

def get_future_matches(api_key):
    
    if not api_key:
        print("Erro: Nenhuma API Key foi fornecida.")
        return None
    
    url = "https://api.football-data.org/v4/competitions/PPL/matches?status=SCHEDULED"
    
    headers = {
        "X-Auth-Token": api_key
    }
    
    print("A obter os próximos jogos da Primeira Liga através da API football-data.org.")
    
    response = requests.get(url,headers=headers)
    
    if response.status_code != 200:
        print(f"Erro ao ligar à API: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    matches = data.get("matches", [])
    
    if not matches:
        print("Não foram encontrados jogos futuros.")
        return None
    
    next_matches = matches[:9] # apenas os próximos 9 jogos
    
    # ajustar os nomes que a API retorna para os mesmos do csv
    team_names={
        "FC Famalicão": "Famalicao",
        "FC Arouca": "Arouca",
        "FC Alverca": "Alverca",
        "AVS": "AVS",
        "Moreirense FC": "Moreirense",
        "CD Nacional": "Nacional",
        "Sporting Clube de Braga": "Sp Braga",
        "Sporting Clube de Portugal": "Sp Lisbon",
        "GD Estoril Praia": "Estoril",
        "Casa Pia AC": "Casa Pia",
        "CF Estrela da Amadora": "Estrela",
        "Gil Vicente FC": "Gil Vicente",
        "Sport Lisboa e Benfica": "Benfica",
        "FC Porto": "Porto",
        "CD Santa Clara": "Santa Clara",
        "Vitória SC": "Guimaraes",
        "CD Tondela": "Tondela",
        "Rio Ave FC": "Rio Ave",
        "CS Marítimo": "Maritimo"
        #"Académico de Viseu FC": "Academico Viseu"
    }
    
    # criar lista de dicionarios com dados dos proximos jogos
    future_matches = []
    
    for match in next_matches:
        utc_date = match['utcDate'] # extrair data do formato do API
        date = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ")
        formatted_date = date.strftime("%d/%m/%Y") # formatar data para o formato do csv
        formatted_time = date.strftime("%H:%M")
        
        api_home = match['homeTeam']['name']
        api_away = match['awayTeam']['name']
        
        home_team = team_names.get(api_home, api_home) # ajustar o nome da equipa
        away_team = team_names.get(api_away, api_away)
        
        future_matches.append({
            "Div": "P1",
            "Date": formatted_date,
            "Time": formatted_time,
            "HomeTeam": home_team,
            "AwayTeam": away_team,
        })
        
        df = pd.DataFrame(future_matches)
    
    print("Próxima jornada obtida com sucesso.")
    return df
    
def main():
    api_key = os.getenv("FOOTBALL_API_KEY")
    df = get_future_matches(api_key)
    
    if df is not None:
        file_path = Path("data/raw/LigaPortugal26-27.csv")
        old_df = pd.read_csv(file_path)
        
        old_df = old_df.dropna(subset=['FTR'])
        
        new_df = pd.concat([old_df, df], ignore_index=True)
        
        new_df = new_df.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'], keep='last')
        
        new_df.to_csv(file_path, index=False)
        
        print("Próxima jornada adicionada ao dataset com sucesso.")
    
if __name__ == "__main__":
    main()
    