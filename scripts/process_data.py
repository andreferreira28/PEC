import pandas as pd
import numpy as np
import glob
from pathlib import Path

def calc_standings(path_raw):
    files = sorted(glob.glob(f"{path_raw}/LigaPortugal*.csv"))
    all_data = []
    
    # colunas a manter
    cols_to_keep = ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 'HTHG', 'HTAG', 'HTR', 'HY', 'AY', 'HR', 'AR']
    
    for file in files:
        df = pd.read_csv(file)
        season = Path(file).stem.replace('LigaPortugal', '') # extrai a parte do nome do ficheiro que indica a época
        
        if 'Time' in df.columns:
            cols = cols_to_keep + ['Time']
        else:
            cols = cols_to_keep
        
        df = df[cols].copy() # manter apenas as colunas relevantes e reduz a carga de memoria
        
        if season == '17-18':
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, format="%d/%m/%y") # csv com ano com 2 digitos
        else:
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, format="%d/%m/%Y") # resto das epocas com ano com 4 digitos
        
        # calcular classificaçao por ordem temporal
        if 'Time' in df.columns:
            df['Datetime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'])
            df = df.sort_values('Datetime').reset_index(drop=True)
        else:
            df = df.sort_values('Date').reset_index(drop=True) # ordena por data crescente para calcular as classificaçoes corretamente
        
        # iniciar calculo de classificaçao (reseta ao fim de cada época)
        teams = pd.concat([df['HomeTeam'], df['AwayTeam']]).unique() # obter a lista de equipas unicas
        stats = {team: {'Points': 0, 'GS': 0, 'GC': 0, 'W': 0, 'GP': 0, 'Y': 0, 'R': 0} for team in teams} # GS = goals scores, GC = goals conceded, GP = games played, Y = yellow cards, R = red cards
        
        season_matches = []
        
        # caso o csv tenha a coluna Time
        if 'Time' in df.columns:
            
            for _, row in df.iterrows():
            
            # calculo da classificaçao antes do jogo
                standings = []
                for team, s in stats.items():
                    standings.append({'Team': team, 'Points': s['Points'], 'W': s['W'], 'GD': s['GS'] - s['GC'], 'GS': s['GS'], 'GP': s['GP'], 'Y': s['Y'], 'R': s['R']})
            
                # ordenar classificaçao por Pts > DG > W > GS
                standings_df = pd.DataFrame(standings).sort_values(by=['Points', 'GD', 'W', 'GS'], ascending=False).reset_index(drop=True)
                standings_df['Rank'] = standings_df.index + 1
            
                # obter a posiçao das equipas antes do jogo
                home_rank = standings_df[standings_df['Team'] == row['HomeTeam']].iloc[0]
                away_rank = standings_df[standings_df['Team'] == row['AwayTeam']].iloc[0]
            
                # adicionar informaçao do jogo e da classificaçao ao dataframe final
                match_entry = row.to_dict()
                match_entry.update({
                    'Season': season,
                    'HomeRank': home_rank['Rank'],
                    'AwayRank': away_rank['Rank'],
                    'HomePoints': home_rank['Points'],
                    'AwayPoints': away_rank['Points'],
                    'HomeW': home_rank['W'],
                    'AwayW': away_rank['W'],
                    'HomeGD': home_rank['GD'],
                    'AwayGD': away_rank['GD'],
                    'HomeGP': home_rank['GP'],
                    'AwayGP': away_rank['GP'],
                    'Sum_HomeY': home_rank['Y'],
                    'Sum_AwayY': away_rank['Y'],
                    'Sum_HomeR': home_rank['R'],
                    'Sum_AwayR': away_rank['R']
                })
                season_matches.append(match_entry)
            
                # atualizar as estatisticas das equipas apos o jogo
                home, away = row['HomeTeam'], row['AwayTeam']
                fthg, ftag, ftr = row['FTHG'], row['FTAG'], row['FTR']
                
                # so processa se o jogo ja terminou, ou seja se tiver FTR, para evitar bug de jogos adiados
                if pd.notna(fthg) and pd.notna(ftag):
                    stats[home]['GS'] += fthg 
                    stats[home]['GC'] += ftag
                    stats[home]['GP'] += 1
                    stats[away]['GS'] += ftag 
                    stats[away]['GC'] += fthg
                    stats[away]['GP'] += 1
                    stats[home]['Y'] += pd.to_numeric(row['HY'], errors='coerce') if pd.notna(row['HY']) else 0
                    stats[away]['Y'] += pd.to_numeric(row['AY'], errors='coerce') if pd.notna(row['AY']) else 0
                    stats[home]['R'] += pd.to_numeric(row['HR'], errors='coerce') if pd.notna(row['HR']) else 0
                    stats[away]['R'] += pd.to_numeric(row['AR'], errors='coerce') if pd.notna(row['AR']) else 0
            
                    if ftr == 'H':
                        stats[home]['Points'] += 3
                        stats[home]['W'] += 1
                    elif ftr == 'A':
                        stats[away]['Points'] += 3
                        stats[away]['W'] += 1
                    else:
                        stats[home]['Points'] += 1
                        stats[away]['Points'] += 1
                
        # caso o csv nao tenha a coluna Time
        else:
            for date in sorted(df['Date'].unique()):
                daily_matches = df[df['Date'] == date]
                
                # standigs antes da data
                standings = []
                for team, s in stats.items():
                    standings.append({'Team': team, 'Points': s['Points'], 'W': s['W'], 'GD': s['GS'] - s['GC'], 'GS': s['GS'], 'GP': s['GP'], 'Y': s['Y'], 'R': s['R']})
                
                # ordenar classificaçao por Pts > DG > W > GS
                standings_df = pd.DataFrame(standings).sort_values(by=['Points', 'GD', 'W', 'GS'], ascending=False).reset_index(drop=True)
                standings_df['Rank'] = standings_df.index + 1
                
                for _, row in daily_matches.iterrows():
                    # obter a posiçao das equipas antes do jogo
                    home_rank = standings_df[standings_df['Team'] == row['HomeTeam']].iloc[0]
                    away_rank = standings_df[standings_df['Team'] == row['AwayTeam']].iloc[0]
            
                    # adicionar informaçao do jogo e da classificaçao ao dataframe final
                    match_entry = row.to_dict()
                    match_entry.update({
                        'Season': season,
                        'HomeRank': home_rank['Rank'],
                        'AwayRank': away_rank['Rank'],
                        'HomePoints': home_rank['Points'],
                        'AwayPoints': away_rank['Points'],
                        'HomeW': home_rank['W'],
                        'AwayW': away_rank['W'],
                        'HomeGD': home_rank['GD'],
                        'AwayGD': away_rank['GD'],
                        'HomeGP': home_rank['GP'],
                        'AwayGP': away_rank['GP'],
                        'Sum_HomeY': home_rank['Y'],
                        'Sum_AwayY': away_rank['Y'],
                        'Sum_HomeR': home_rank['R'],
                        'Sum_AwayR': away_rank['R']
                    })
                    season_matches.append(match_entry)
                
                # atualizar as estatisticas apos os jogos do dia
                for _,row in daily_matches.iterrows():
                    home, away = row['HomeTeam'], row['AwayTeam']
                    fthg, ftag, ftr = row['FTHG'], row['FTAG'], row['FTR']
                    
                    if pd.notna(fthg) and pd.notna(ftag):
                        stats[home]['GS'] += fthg 
                        stats[home]['GC'] += ftag
                        stats[home]['GP'] += 1
                        stats[away]['GS'] += ftag 
                        stats[away]['GC'] += fthg
                        stats[away]['GP'] += 1
                        stats[home]['Y'] += pd.to_numeric(row['HY'], errors='coerce') if pd.notna(row['HY']) else 0
                        stats[away]['Y'] += pd.to_numeric(row['AY'], errors='coerce') if pd.notna(row['AY']) else 0
                        stats[home]['R'] += pd.to_numeric(row['HR'], errors='coerce') if pd.notna(row['HR']) else 0
                        stats[away]['R'] += pd.to_numeric(row['AR'], errors='coerce') if pd.notna(row['AR']) else 0
            
                        if ftr == 'H':
                            stats[home]['Points'] += 3
                            stats[home]['W'] += 1
                        elif ftr == 'A':
                            stats[away]['Points'] += 3
                            stats[away]['W'] += 1
                        else:
                            stats[home]['Points'] += 1
                            stats[away]['Points'] += 1
        
        all_data.append(pd.DataFrame(season_matches))
    
    df_final = pd.concat(all_data, ignore_index=True)
    df_final['Stadium'], _ = pd.factorize(df_final['HomeTeam'])
    
    # ordenar pela data e hora de jogo se houver, e em caso de empate alfabeticamente pela equipa da casa
    if 'Datetime' in df_final.columns:
        df_final['Datetime'] = df_final['Datetime'].fillna(df_final['Date']) # preencher datetimes vazios com a coluna Date
        df_final = df_final.sort_values(by=['Datetime', 'HomeTeam'], ascending=False)
    else:
        df_final = df_final.sort_values(by=['Date', 'HomeTeam'], ascending=False)
    
    return df_final
    
def add_last_season_rank(df):
    # calcular pontos obtidos por jogo
    home_pts = np.where(df['FTR'] == 'H', 3, np.where(df['FTR'] == 'D', 1, 0))
    away_pts = np.where(df['FTR'] == 'A', 3, np.where(df['FTR'] == 'D', 1, 0))
    
    home_df = pd.DataFrame({'Season': df['Season'], 'Team': df['HomeTeam'], 'Pts': home_pts, 'GS': df['FTHG'], 'GC': df['FTAG']})
    away_df = pd.DataFrame({'Season': df['Season'], 'Team': df['AwayTeam'], 'Pts': away_pts, 'GS': df['FTAG'], 'GC': df['FTHG']})
    
    all_matches = pd.concat([home_df, away_df], ignore_index=True).dropna(subset=['Pts'])
    
    # somar totais da epoca
    season_totals = all_matches.groupby(['Season', 'Team']).agg(Points=('Pts', 'sum'), GS=('GS', 'sum'), GC=('GC', 'sum')).reset_index()
    season_totals['GD'] = season_totals['GS'] - season_totals['GC']
    
    # ordenar e atribuir rank final
    season_totals = season_totals.sort_values(by=['Season', 'Points', 'GD', 'GS'], ascending=[True,False,False,False]).reset_index(drop=True)
    
    season_totals['FinalRank'] = season_totals.groupby('Season').cumcount() + 1
    
    final_ranks = season_totals[['Season', 'Team', 'FinalRank']].copy()
    
    # dicionario com ranks da epoca 16-17 para preencher primeiros jogos da epoca 17-18
    rank_16_17 = [
        {'Season': '16-17', 'Team': 'Benfica', 'FinalRank': 1},
        {'Season': '16-17', 'Team': 'Porto', 'FinalRank': 2},
        {'Season': '16-17', 'Team': 'Sp Lisbon', 'FinalRank': 3}, 
        {'Season': '16-17', 'Team': 'Guimaraes', 'FinalRank': 4},
        {'Season': '16-17', 'Team': 'Braga', 'FinalRank': 5},
        {'Season': '16-17', 'Team': 'Maritimo', 'FinalRank': 6},
        {'Season': '16-17', 'Team': 'Rio Ave', 'FinalRank': 7},
        {'Season': '16-17', 'Team': 'Feirense', 'FinalRank': 8},
        {'Season': '16-17', 'Team': 'Boavista', 'FinalRank': 9},
        {'Season': '16-17', 'Team': 'Estoril', 'FinalRank': 10},
        {'Season': '16-17', 'Team': 'Chaves', 'FinalRank': 11},
        {'Season': '16-17', 'Team': 'Setubal', 'FinalRank': 12},
        {'Season': '16-17', 'Team': 'Pacos Ferreira', 'FinalRank': 13},
        {'Season': '16-17', 'Team': 'Belenenses', 'FinalRank': 14},
        {'Season': '16-17', 'Team': 'Moreirense', 'FinalRank': 15},
        {'Season': '16-17', 'Team': 'Tondela', 'FinalRank': 16},
        {'Season': '16-17', 'Team': 'Arouca', 'FinalRank': 17},
        {'Season': '16-17', 'Team': 'Nacional', 'FinalRank': 18}
    ]
    
    df_16_17 = pd.DataFrame(rank_16_17)
    final_ranks = pd.concat([df_16_17,final_ranks], ignore_index=True)
    
    # mapeara a epoca anterior
    def get_prev_season(s):
        try:
            parts = s.split('-')
            return f"{int(parts[0])-1:02d}-{int(parts[1])-1:02d}"
        except:
            return None
        
    df['PrevSeason'] = df['Season'].apply(get_prev_season)
    
    # preparar a tabela de merge para evitar conflitos de colunas
    ranks_to_merge = final_ranks.rename(columns={'Season': 'PrevSeason', 'Team': 'MergeTeam', 'FinalRank': 'RankVal'})
    
    df = df.merge(
        ranks_to_merge, 
        left_on=['PrevSeason', 'HomeTeam'], 
        right_on=['PrevSeason', 'MergeTeam'], 
        how='left'
    ).rename(columns={'RankVal': 'Home_LastRank'}).drop(columns=['MergeTeam'])
    
    df = df.merge(
        ranks_to_merge, 
        left_on=['PrevSeason', 'AwayTeam'], 
        right_on=['PrevSeason', 'MergeTeam'], 
        how='left'
    ).rename(columns={'RankVal': 'Away_LastRank'}).drop(columns=['MergeTeam', 'PrevSeason'])
    
    # preencher recem promovidos com 19
    df['Home_LastRank'] = df['Home_LastRank'].fillna(19)
    df['Away_LastRank'] = df['Away_LastRank'].fillna(19)
    
    return df
def add_rolling_features(df):
    # criar colunas para jogos em casa e fora
    home = df[['Date', 'HomeTeam', 'FTHG', 'FTAG', 'FTR', 'Season']].copy() # manter colunas relevantes para rolling
    home.columns = ['Date', 'Team', 'GS', 'GC', 'Result', 'Season'] # renomear para facilitar
    home['Pts'] = home['Result'].map({'H': 3, 'D': 1, 'A': 0}) # pontos ganhos em casa
    
    away = df[['Date', 'AwayTeam', 'FTAG', 'FTHG', 'FTR', 'Season']].copy()
    away.columns = ['Date', 'Team', 'GS', 'GC', 'Result', 'Season']
    away['Pts'] = away['Result'].map({'A': 3, 'D': 1, 'H': 0}) # pontos ganho fora
    
    # juntar tudo e ordenar por epoca, equipa e data
    team_stats = pd.concat([home, away], ignore_index=True).sort_values(['Season', 'Team', 'Date'])
    
    # definir peso dos jogos mais recentes
    weights = np.array([1, 2, 3, 4, 5])
    
    def weighted_form(x):
        w = weights[-len(x):] # usar para jogos disponiveis e nao so quando ha 5 jogos
        return (x * w).sum()
    
    # calcular rolling averages para os ultimos 5 jogos disputados
    played_stats = team_stats.dropna(subset=['Result']).copy()
    grouped = team_stats.groupby(['Season', 'Team']) # calcular tudo separadamente para cada epoca e equipa
    
    played_stats['L5_GS'] = grouped['GS'].transform(lambda x: x.rolling(5, min_periods=1).mean().shift(1)) # media de golos marcados nos ultimos 5 jogos, sem contar o jogo atual
    played_stats['L5_GC'] = grouped['GC'].transform(lambda x: x.rolling(5, min_periods=1).mean().shift(1))
    
    # calcular forma ponderada
    played_stats['L5_Form'] = grouped['Pts'].transform(lambda x: x.rolling(5, min_periods=1).apply(weighted_form, raw=True).shift(1))
    
    team_stats = team_stats.merge(played_stats[['Date', 'Team', 'L5_GS', 'L5_GC', 'L5_Form']], on=['Date', 'Team'], how='left')
    
    # arrastar a forma do jogo anterior para jogos adiados
    team_stats[['L5_GS', 'L5_GC', 'L5_Form']] = team_stats.groupby(['Season', 'Team'])[['L5_GS', 'L5_GC', 'L5_Form']].ffill()
    
    # preencher com 0 para os primeiros jogos
    team_stats[['L5_GS', 'L5_GC', 'L5_Form']] = team_stats[['L5_GS', 'L5_GC', 'L5_Form']].fillna(0)
    
    # juntar as features de volta ao dataframe original
    df = df.merge(team_stats[['Date', 'Team', 'L5_GS', 'L5_GC', 'L5_Form']], left_on=['Date', 'HomeTeam'], right_on=['Date', 'Team'], how='left')
    df = df.rename(columns={'L5_GS': 'Home_L5_GS', 'L5_GC': 'Home_L5_GC', 'L5_Form': 'Home_L5_Form_Pts'})
    df = df.drop(columns=['Team'])
    
    df = df.merge(team_stats[['Date', 'Team', 'L5_GS', 'L5_GC', 'L5_Form']], left_on=['Date', 'AwayTeam'], right_on=['Date', 'Team'], how='left')
    df = df.rename(columns={'L5_GS': 'Away_L5_GS', 'L5_GC': 'Away_L5_GC', 'L5_Form': 'Away_L5_Form_Pts'})
    df = df.drop(columns=['Team'])
    
    # ordenar pela data e hora de jogo se houver, e em caso de empate alfabeticamente pela equipa da casa
    if 'Datetime' in df.columns:
        df = df.sort_values(by=['Datetime', 'HomeTeam'], ascending=False).reset_index(drop=True)
    else:
        df = df.sort_values(by=['Date', 'HomeTeam'], ascending=False).reset_index(drop=True)
    
    return df

def add_difference_features(df):
    df['Rank_Diff'] = df['HomeRank'] - df['AwayRank']
    df['LastRank_Diff'] = df['Home_LastRank'] - df['Away_LastRank']
    df['Form_Diff'] = df['Home_L5_Form_Pts'] - df['Away_L5_Form_Pts']
    df['GD_Diff'] = df['HomeGD'] - df['AwayGD']
    
    df['HomePPG'] = df['HomePoints'] / df['HomeGP'].replace(0, np.nan)
    df['AwayPPG'] = df['AwayPoints'] / df['AwayGP'].replace(0, np.nan)
    df['HomePPG'] = df['HomePPG'].fillna(0)
    df['AwayPPG'] = df['AwayPPG'].fillna(0)
    df['PPG_Diff'] = df['HomePPG'] - df['AwayPPG']
    
    df['HomeGDpg'] = df['HomeGD'] / df['HomeGP'].replace(0, np.nan)
    df['AwayGDpg'] = df['AwayGD'] / df['AwayGP'].replace(0, np.nan)
    df['HomeGDpg'] = df['HomeGDpg'].fillna(0)
    df['AwayGDpg'] = df['AwayGDpg'].fillna(0)
    df['GDpg_Diff'] = df['HomeGDpg'] - df['AwayGDpg']
    return df
    
def add_season_of_the_year(df):
    # criar Mes * 100 + dia para simplificar os calculos das estaçoes,
    # ou seja 15 de março fica (mes 3, dia 15) 315
    mmdd = df['Date'].dt.month * 100 + df['Date'].dt.day
    
    # data das estaçoes aproximadamente
    # primavera: 21 março (321) a  20 de junho (620)
    # verao: 21 de junho (621) a 22 de setembro (922)
    # outono: 23 de setembro (923) a 20 de dezembro (1220)
    # inverno: 21 de dezembro (1221) a 20 de março (320)
    
    conditions = [
        (mmdd >= 321) & (mmdd <= 620), # primavera
        (mmdd >= 621) & (mmdd <= 922), # verao
        (mmdd >= 923) & (mmdd <= 1220), # outono
        (mmdd >= 1221) | (mmdd <= 320) # inverno
    ]
    
    # inverno = 0, primavera = 1, verao = 2, outono = 3
    ws_number = [1, 2, 3, 0]
    df['WeatherSeason'] = np.select(conditions, ws_number)
    
    return df

def main():
    df = calc_standings("data/raw")
    df = add_last_season_rank(df)
    df = add_rolling_features(df)
    df = add_difference_features(df)
    df = add_season_of_the_year(df)
    
    df = df.drop(columns=['Datetime'])
    
    # meter a coluna time a seguir ao Date
    if 'Time' in df.columns:
        cols = df.columns.tolist()
        cols.remove('Time')
        
        idx = cols.index('HomeTeam')
        
        cols.insert(idx, 'Time')
        
        df = df[cols]
    
    df.to_csv("data/processed/LigaPortugal.csv", index=False)
    print('Dados processados e guardados com sucesso.')
    
if __name__ == "__main__":
    main()
    