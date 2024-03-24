import os
import pandas as pd
from utils_analysis import replace_error_date
from utils_analysis import convert_bp_str_to_list, check_ban_pick_result, _adjust_hero_name, get_all_stats
from datetime import datetime
from tqdm import tqdm
import sys

# define filtering rules
# None for no filtration
tournament_codes = [1] # list to include only stated values
tournament_tiers = ['S', 'A'] # list to include only stated values
tournament_stages =  None # b for bracket only
tournament_start_date = 20230101 # minimum starting date (inclusive), yyyymmdd
tournament_end_date = 20231231 # max end date (inclusive), yyyymmdd

# dataset names
tournament_data_name = "tournament_data.csv"
game_data_name = "consolidated_game_data.csv"
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
hero_info_df['Name'] = hero_info_df['Name'].apply(_adjust_hero_name)

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

if filtered_game_data_df.shape[0] == 0:
    print("Filtration rule leads to no game data, please reset them.")
    sys.exit()
######## print(filtered_game_data_df)

#### Analysis
num_games = filtered_game_data_df.shape[0]
#hero_info_df = hero_info_df.iloc[[1]]
stats_dict_list = []

# loop through all heroes
hero_rows_pbar = tqdm(hero_info_df.iterrows(), total = hero_info_df.shape[0], desc = "Progress")
for _, row in hero_rows_pbar:
    hero_code = row['Hero Code']
    hero_name = row['Name']

    hero_rows_pbar.set_postfix({
        'Hero': hero_name
    })

    # create a new copy of game data df for analysis
    temp_game_data_df = filtered_game_data_df.copy(deep=True)
    temp_game_data_df[['ban_side', 'ban_against_team', 'pick_side', 'pick_team', 'result']] = temp_game_data_df.apply(
        lambda row: check_ban_pick_result(hero_name,
            row['t1_name'], row['t1_side'], row['t1_bans'], row['t1_picks'], row['t1_result'],
            row['t2_name'], row['t2_side'], row['t2_bans'], row['t2_picks'], row['t2_result'],
        ),
        axis=1, result_type='expand'
    )

    #temp_game_data_df.to_csv(os.path.join(result_dir, 'test.csv'))
    all_stats = get_all_stats(num_games, temp_game_data_df)
    final_dict = {
        "hero_name": hero_name,
        "num_games": num_games
    }
    final_dict.update(all_stats)

    stats_dict_list.append(final_dict)


# aggregate all dict into 1, then convert to df
full_stats_dict = {}
for key in stats_dict_list[0].keys():
    full_stats_dict[key] = [d[key] for d in stats_dict_list]

full_stats_df = pd.DataFrame(full_stats_dict)
full_stats_df.sort_values(by = ['full_bp_rate', 'full_ban_rate', 'full_win_rate'], ascending=False, inplace=True)
full_stats_df = full_stats_df[[
    'hero_name', 'num_games',
    'blue_ban_num', 'red_ban_num', 'full_ban_num', 'full_ban_rate', 'blue_ban_ratio', 'red_ban_ratio',
    'mbat_team_name', 'mbat_ban_num', 'mbat_ban_ratio',
    'blue_pick_num', 'blue_pick_rate',
    'red_pick_num', 'red_pick_rate',
    'full_pick_num', 'full_pick_rate',
    'mpnt_team_name', 'mpnt_pick_num', 'mpnt_win_num', 'mpnt_win_rate',
    'full_bp_num', 'full_bp_rate',
    'full_win_num', 'full_lose_num', 'full_win_rate',
    'full_win_avg_game_time_sec', 'full_lose_avg_game_time_sec',
    'mwrt_team_name', 'mwrt_pick_num', 'mwrt_win_num', 'mwrt_win_rate',
]]



# output analysis result
curr_dt = datetime.now().strftime("%Y%m%d_%H%M%S")
analysis_result_name = f"{curr_dt}_individual_hero_bp_table.csv"
analysis_result_path = os.path.join(result_dir, analysis_result_name)

full_stats_df.to_csv(analysis_result_path, index=False)
print(f"Analysis results saved as '{analysis_result_name}'")





    

