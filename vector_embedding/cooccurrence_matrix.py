import os
import numpy as np
import pandas as pd
from tqdm import tqdm
from utils_embedding import adjust_hero_name, convert_bp_str_to_list
from utils_embedding import CooccurenceMatrix
from datetime import datetime


# dataset names
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


# cooccurence matrix
num_heroes = hero_info_df.shape[0]
cooccur_matrix = CooccurenceMatrix(num_heroes)

hero_info_dict = dict(zip(hero_info_df['Name'], hero_info_df['Hero Code']))

total_num_games = game_data_df.shape[0]
game_rows_pbar = tqdm(game_data_df[['t1_picks', 't2_picks']].iterrows(), total = total_num_games, desc = "Progress")

for _, row in game_rows_pbar:
    t1_idx_list = [hero_info_dict[hero] - 1 for hero in row["t1_picks"]]
    cooccur_matrix.add_count(t1_idx_list)
    t2_idx_list = [hero_info_dict[hero] - 1 for hero in row["t1_picks"]]
    cooccur_matrix.add_count(t2_idx_list)
    
row_sums, norm_matrix = cooccur_matrix.get_normalized_cooccur_matrix()

cooccur_df = pd.DataFrame(norm_matrix,
                           index = hero_info_df['Name'].tolist(),
                           columns = hero_info_df['Name'].tolist()
)

cooccur_df['pick_count'] = row_sums.astype(np.float64) / 4



# output analysis result
curr_dt = datetime.now().strftime("%Y%m%d_%H%M%S")
analysis_result_name = f"{curr_dt}_hero_cooccurence_matrix.csv"
analysis_result_path = os.path.join(result_dir, analysis_result_name)

cooccur_df.to_csv(analysis_result_path, index=True)
print(f"Analysis results saved as '{analysis_result_name}'")