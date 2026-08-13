import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder

# funçao para garantir que a soma das probabilidades seja 100%
def normalize_probabilities(prob_home, prob_draw, prob_away):
    h = round(prob_home * 100, 1)
    d = round(prob_draw * 100, 1)
    a = round(prob_away * 100, 1)
    
    sum = round(h + d + a, 1)
    diff = round(100 - sum, 1)
    
    if diff != 0.0:
        if h >= d and h >= a:
            h = round(h + diff, 1)
        elif d >= h and d >= a:
            d = round(d + diff, 1)
        else:
            a = round(a + diff, 1)
    
    return h, d, a

# carregar e preparar dados
def load_and_prep_data(file_path):
    print('Carregando e preparando os dados...')
    df = pd.read_csv(file_path)
    df = df.sort_values(by=['Date', 'Time', 'HomeTeam'], ascending=[True, True, True]).reset_index(drop=True)
    
    # features
    features = [
        'HomeRank', 'AwayRank', 'HomePoints', 'AwayPoints',
        'HomeW', 'AwayW', 'HomeGD', 'AwayGD', 'HomeGP', 'AwayGP',
        'Sum_HomeY', 'Sum_AwayY', 'Sum_HomeR', 'Sum_AwayR',
        'Stadium', 'Home_L5_GS', 'Home_L5_GC', 'Home_L5_Form_Pts',
        'Away_L5_GS', 'Away_L5_GC', 'Away_L5_Form_Pts',
        'Rank_Diff', 'Form_Diff', 'GD_Diff', 'HomePPG', 'AwayPPG',
        'PPG_Diff', 'HomeGDpg', 'AwayGDpg', 'GDpg_Diff', 'WeatherSeason',
        'Home_LastRank', 'Away_LastRank', 'LastRank_Diff'
    ]
    
    # features para remover apos ablation study
    features_to_remove = [
        'WeatherSeason',
        'Sum_AwayR', 'Sum_HomeR',
        'AwayPoints', 'HomePoints',
        'AwayW', 'HomeW'
    ]
    
    features_reduced = [f for f in features if f not in features_to_remove]
    
    # separar os jogos que ja aconteceram dos futuros
    df_played = df[df['FTR'].notna()].copy()
    df_future = df[df['FTR'].isna()].copy()
    
    # transformar FTR em numerico
    le = LabelEncoder()
    df_played['FTR_num'] = le.fit_transform(df_played['FTR'])
    
    return df_played, df_future, features_reduced, le, features

# treino do modelo
def train_model(df_played, features_reduced, le):
    print('Treinando o modelo pré jogo...')
    
    X_train = df_played[features_reduced]
    y_train = df_played['FTR_num']
    
    # hiperparametros obtidos pelo Optuna
    model = xgb.XGBClassifier(
        learning_rate=0.15126766673915848, 
        max_depth=6, 
        n_estimators=422, 
        subsample=0.9371543391575077, 
        colsample_bytree=0.9206831318413401, 
        min_child_weight=6, 
        gamma=3.3894775369915258, 
        reg_lambda=0.01156311748437383, 
        reg_alpha=0.2752277707681487,
        objective="multi:softprob",
        num_class=3,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    model.save_model('pregame_model.json') # para power bi
    
    return model

# modelo 2 classes
def train_model_binary(df_played, features):
    
    df_binary = df_played[df_played['FTR'] != 'D'].copy()
    
    le_bin = LabelEncoder()
    df_binary['FTR_num_bin'] = le_bin.fit_transform(df_binary['FTR'])
    
    X_train = df_binary[features]
    y_train = df_binary['FTR_num_bin']
    
    model = xgb.XGBClassifier(
        random_state=42, 
        objective="binary:logistic",
        learning_rate=0.04635632211048546, 
        max_depth=3, n_estimators=678, 
        subsample=0.4995243416931511, 
        colsample_bytree=0.5426490676090604, 
        min_child_weight=6, 
        gamma=5.2047737369795435, 
        reg_lambda=0.3751488469606916, 
        reg_alpha=0.18389140874211948
    )
    
    model.fit(X_train, y_train)
    model.save_model('pregame_model_bin.json') # para power bi
    
    return model, le_bin
'''
# gerar dataset ao intervalo com as probabilidades
def generate_halftime_dataset(model, df_played, features, le):
    print('A criar dataset com as probabilidades para o modelo ao intervalo...')
    
    # obter probabilidades para todos os jogos antigos
    X_all = df_played[features]
    probs = model.predict_proba(X_all)
    
    # index de H, D, A
    idx_H = list(le.classes_).index('H')
    idx_D = list(le.classes_).index('D')
    idx_A = list(le.classes_).index('A')
    
    # criar dataset
    cols_to_keep = ['Date', 'Time', 'Season', 'HomeTeam', 'AwayTeam', 'HTHG', 'HTAG', 'FTR']
    df_ht = df_played[cols_to_keep].copy()
    
    # inserir as probs em formato 0-1
    df_ht['Pregame_Prob_H'] = probs[:, idx_H]
    df_ht['Pregame_Prob_D'] = probs[:, idx_D]
    df_ht['Pregame_Prob_A'] = probs[:, idx_A]
    
    # guardar csv
    df_ht.to_csv("data/processed/HalftimeDataset.csv", index=False)
    print(f'Dataset criado com sucesso.')
'''

# prever jogos futuros
def predict_future_matches(model, model_binary, df_future, features_reduced, le, le_bin, features):
    print('Previsão próximos 9 jogos...')
    
    if len(df_future) == 0:
        print('Não há jogos futuros no dataset.')
        return
    
    X_future = df_future[features_reduced]
    probs = model.predict_proba(X_future)
    probs_binary = model_binary.predict_proba(df_future[features])
    
    # index de H, D, A
    idx_H = list(le.classes_).index('H')
    idx_D = list(le.classes_).index('D')
    idx_A = list(le.classes_).index('A')
    
    idx_H_bin = list(le_bin.classes_).index('H')
    idx_A_bin = list(le_bin.classes_).index('A')
    
    for i in range(len(df_future)):
        equipa_casa = df_future.iloc[i]['HomeTeam']
        equipa_fora = df_future.iloc[i]['AwayTeam']
        
        p_home = probs[i][idx_H]
        p_draw = probs[i][idx_D]
        p_away = probs[i][idx_A]
        
        p_home_b = probs_binary[i][idx_H_bin] * 100
        p_away_b = probs_binary[i][idx_A_bin] * 100
        
        h_final, d_final, a_final = normalize_probabilities(p_home, p_draw, p_away)
        
        print(f"{equipa_casa}: {h_final:.1f}% - Empate: {d_final:.1f}% - {equipa_fora}: {a_final:.1f}%")
        print(f"{equipa_casa}: {p_home_b:>4.1f}% - {equipa_fora}: {p_away_b:>4.1f}%")
        print("-" * 50)
        
        
def main():
    file_path = "data/processed/LigaPortugal.csv"
        
    df_played, df_future, features_reduced, le, features = load_and_prep_data(file_path)
        
    final_model = train_model(df_played, features_reduced, le)
    final_model_binary, le_bin = train_model_binary(df_played, features)
    
    #generate_halftime_dataset(final_model, df_played, features_reduced, le)
        
    predict_future_matches(final_model, final_model_binary, df_future, features_reduced, le, le_bin, features)
    
if __name__ == "__main__":
    main()