import os
import numpy as np
import pandas as pd
import seaborn as sns
from utils_analysis import adjust_hero_name, replace_error_date, convert_bp_str_to_list
from datetime import datetime
from tqdm import tqdm
import sys

# define filtering rules
# None for no filtration
tournament_codes = None # list to include only stated values
tournament_tiers = ['S', 'A'] # list to include only stated values
tournament_stages =  None # b for bracket only
tournament_start_date = 20230101 # minimum starting date (inclusive), yyyymmdd
tournament_end_date = 20231231 # max end date (inclusive), yyyymmdd
pick_rate_threshold = 0.05 # minimum pick rate for a hero to be included in the final matrix


# dataset names
tournament_data_name = "tournament_data.csv"
game_data_name = "consolidated_game_data_20240505.csv"
hero_info_name = "hero_info.csv"




# get dircetory path
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, "data")
result_dir = os.path.join(script_dir, "results")
if not os.path.exists(result_dir):
    os.mkdir(result_dir)

# read datasets
# read hero info
hero_info_path = os.path.join(data_dir, hero_info_name)
hero_info_df = pd.read_csv(hero_info_path, usecols=['Name', 'Hero Code'])
hero_info_df['Name'] = hero_info_df['Name'].apply(adjust_hero_name)

# read tournament data
tournament_data_path = os.path.join(data_dir, tournament_data_name)
tournament_data_df = pd.read_csv(tournament_data_path, dtype=str)
# replace errornous date
tournament_data_df['start_date'] = tournament_data_df['start_date'].apply(replace_error_date)
tournament_data_df['start_date'] = pd.to_datetime(tournament_data_df['start_date'], format='%Y%m%d')
tournament_data_df['end_date'] = tournament_data_df['end_date'].apply(replace_error_date)
tournament_data_df['end_date'] = pd.to_datetime(tournament_data_df['end_date'], format='%Y%m%d')

# read game data
game_data_path = os.path.join(data_dir, game_data_name)
game_data_df = pd.read_csv(game_data_path, dtype = {
    'tournament_code': str,
    'date': str,
    'game_time_str': str
})
game_data_df['t1_picks'] = game_data_df['t1_picks'].apply(convert_bp_str_to_list)
game_data_df['t1_bans'] = game_data_df['t1_bans'].apply(convert_bp_str_to_list)
game_data_df['t2_picks'] = game_data_df['t2_picks'].apply(convert_bp_str_to_list)
game_data_df['t2_bans'] = game_data_df['t2_bans'].apply(convert_bp_str_to_list)

# filter game datas
## tournament level
filter_condition_list = []

if tournament_codes is not None:
    tournament_codes_str = [str(code) for code in tournament_codes]
    filter_condition_list.append(tournament_data_df['tournament_code'].isin(tournament_codes_str))

if tournament_tiers is not None:
    filter_condition_list.append(tournament_data_df['tier'].isin(tournament_tiers))

if tournament_start_date is not None:
    start_date_dt = pd.to_datetime(tournament_start_date, format='%Y%m%d')
    filter_condition_list.append(tournament_data_df['start_date'] >= start_date_dt)

if tournament_end_date is not None:
    end_date_dt = pd.to_datetime(tournament_end_date, format='%Y%m%d')
    filter_condition_list.append(tournament_data_df['end_date'] <= end_date_dt)

combined_condition = pd.Series([True] * len(tournament_data_df))

for condition in filter_condition_list:
    combined_condition = combined_condition & condition

filtered_tournament_df = tournament_data_df[combined_condition]


## game data level
updated_tournament_codes = filtered_tournament_df['tournament_code'].tolist()
tournament_codes_condition = game_data_df['tournament_code'].isin(updated_tournament_codes)

if tournament_stages == 'b':
    tournament_stages_condition = game_data_df['tournament_stage'] == 'bracket'
else:
    tournament_stages_condition = pd.Series([True] * len(game_data_df))

filtered_game_data_df = game_data_df[tournament_codes_condition & tournament_stages_condition]
total_num_games = filtered_game_data_df.shape[0]

if total_num_games == 0:
    print("Filtration rule leads to no game data, please reset them.")
    sys.exit()

######## print(filtered_game_data_df)

#### Analysis
num_heroes = hero_info_df.shape[0]

win_lose_matrix = np.zeros(shape=(num_heroes,num_heroes), dtype = np.int16)
hero_info_dict = dict(zip(hero_info_df['Name'], hero_info_df['Hero Code']))


game_rows_pbar = tqdm(filtered_game_data_df[['t1_picks', 't1_result', 't2_picks', 't2_result']].iterrows(), total = total_num_games, desc = "Progress")

for _, row in game_rows_pbar:
    if (row["t1_result"] == 1) & (row["t2_result"] == 0):
        win_team = row["t1_picks"]
        lose_team = row["t2_picks"]
    elif (row["t1_result"] == 0) & (row["t2_result"] == 1):
        win_team = row["t2_picks"]
        lose_team = row["t1_picks"]
    else:
        continue
    
    for win_hero in win_team:
        win_hero_idx = hero_info_dict[win_hero] - 1
        for lose_hero in lose_team:
            lose_hero_idx = hero_info_dict[lose_hero] - 1
            win_lose_matrix[win_hero_idx, lose_hero_idx] += 1

# convert win_lose_matrix to wr_matrix
wr_matrix = np.zeros(shape=(num_heroes, num_heroes+2), dtype = np.float32)

# calculate win rate matrix
for i in range(num_heroes):
    for j in range(num_heroes):
        num_wins = win_lose_matrix[i, j]
        num_lose = win_lose_matrix[j, i]

        num_games = num_wins + num_lose
        if num_games == 0:
            wr_matrix[i,j] = np.nan
        else:
            wr_matrix[i,j] = np.float32(num_wins)/np.float32(num_games)

# calculate overall win rate for each hero
for i in range(num_heroes):
    num_wins = np.sum(win_lose_matrix[i,:])
    num_lose = np.sum(win_lose_matrix[:,i])
    num_games = num_wins + num_lose

    wr_matrix[i, num_heroes] = num_games/5

    if num_games == 0:
        wr_matrix[i, num_heroes + 1] = np.nan
    else:
        wr_matrix[i, num_heroes + 1] = num_wins/num_games

wr_df = pd.DataFrame(wr_matrix,
                           index = hero_info_df['Name'].tolist(),
                           columns = hero_info_df['Name'].tolist() + ['N_games', 'Total_WR']
                           )


# remove heroes with pick rate below than threshold
final_wr_df = wr_df[wr_df['N_games'] > (total_num_games*pick_rate_threshold)]
# sort by WR
final_wr_df = final_wr_df.sort_values(by = ["Total_WR", 'N_games'], ascending=False)
remaining_heroes = final_wr_df.index.tolist()

# rearrange column sequence
wr_seq_list = remaining_heroes + ['N_games', 'Total_WR']
final_wr_df = final_wr_df[wr_seq_list]

# plot heatmap
wr_heatmap = sns.heatmap(
    final_wr_df[remaining_heroes], annot=False, cmap = 'coolwarm'
)


# output analysis result
curr_dt = datetime.now().strftime("%Y%m%d_%H%M%S")
analysis_result_name = f"{curr_dt}_hero_wr_matrix.csv"
analysis_result_path = os.path.join(result_dir, analysis_result_name)

final_wr_df.to_csv(analysis_result_path, index=True)
print(f"Analysis results saved as '{analysis_result_name}'")

heatmap_name = f"{curr_dt}_hero_wr_matrix_heatmap.png"
heatmap_path = os.path.join(result_dir, heatmap_name)
wr_heatmap.figure.savefig(heatmap_path)