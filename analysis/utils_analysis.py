import numpy as np
import pandas as pd

def adjust_hero_name(hero_name):

    # if 'popol' in hero_name.lower():
    #     return 'popol'

    return hero_name.lower()

def replace_error_date(date_str):
    if len(str(date_str)) != 8:
        return None
    else:
        return date_str

def robust_division(numerator, denom, error_value=0):
    if denom == 0:
        return error_value
    else:
        return numerator/denom
    
def convert_bp_str_to_list(bp_in_str):
    if pd.isna(bp_in_str):
        return []
    
    if bp_in_str[0] == '(' and bp_in_str[-1] == ')':
        inner_str = bp_in_str[1:-1]
        if inner_str == '':
            return []
        else:
            inner_list = inner_str.split(',')
            return [name.strip("\"' ").lower() for name in inner_list]
    else:
        return bp_in_str


def check_ban_pick_result(hero_name, t1_name, t1_side, t1_bans, t1_picks, t1_result, t2_name, t2_side, t2_bans, t2_picks, t2_result):

    if hero_name in t1_bans:
        ban_side = t1_side
        ban_against_team = t2_name
    elif hero_name in t2_bans:
        ban_side = t2_side
        ban_against_team = t1_name
    else:
        ban_side = None
        ban_against_team = None

    if hero_name in t1_picks:
        pick_side = t1_side
        pick_team = t1_name
        result = t1_result
    elif hero_name in t2_picks:
        pick_side = t2_side
        pick_team = t2_name
        result = t2_result
    else:
        pick_side = None
        pick_team = None
        result = None

    return ban_side, ban_against_team, pick_side, pick_team, result

def get_sides_bp_stats(bp_side_df):
    ban_counts = bp_side_df['ban_side'].value_counts()
    pick_counts = bp_side_df['pick_side'].value_counts()

    return {
        'blue_ban_num': ban_counts.get('blue', 0),
        'blue_pick_num': pick_counts.get('blue', 0),
        'red_ban_num': ban_counts.get('red', 0),
        'red_pick_num': pick_counts.get('red', 0),
    }

def get_win_lose_stats(res_gametime_df):
    win_games_df = res_gametime_df[res_gametime_df['result'] == 1]
    win_num = win_games_df.shape[0]
    win_avg_game_time_sec = win_games_df['game_time_sec'].mean()
    if pd.isna(win_avg_game_time_sec):
        win_avg_game_time_sec = 0

    lose_games_df = res_gametime_df[res_gametime_df['result'] == 0]
    lose_num = lose_games_df.shape[0]
    lose_avg_game_time_sec = lose_games_df['game_time_sec'].mean()
    if pd.isna(lose_avg_game_time_sec):
        lose_avg_game_time_sec = 0
    
        
    return {
        'full_win_num': win_num,
        'full_lose_num': lose_num,
        'full_win_avg_game_time_sec': round(win_avg_game_time_sec),
        'full_lose_avg_game_time_sec': round(lose_avg_game_time_sec),
    }

def get_derived_stats(num_games, sides_bp_stats, win_lose_stats):
    full_ban_num = sides_bp_stats['red_ban_num'] + sides_bp_stats['blue_ban_num']
    full_ban_rate = robust_division(full_ban_num, num_games, 0)
    full_pick_num = sides_bp_stats['red_pick_num'] + sides_bp_stats['blue_pick_num']
    full_pick_rate = robust_division(full_pick_num, num_games-full_ban_num, 0)
    full_bp_num = full_ban_num + full_pick_num
    full_bp_rate = robust_division(full_bp_num, num_games, 0)
    #print(full_pick_num == (win_lose_stats['full_win_num'] + win_lose_stats['full_lose_num']))
    full_win_rate = robust_division(win_lose_stats['full_win_num'], full_pick_num, 0)

    blue_ban_ratio = robust_division(sides_bp_stats['blue_ban_num'], full_ban_num, 0)
    red_ban_ratio = robust_division(sides_bp_stats['red_ban_num'], full_ban_num, 0)
    blue_pick_rate = robust_division(sides_bp_stats['blue_pick_num'], num_games - full_ban_num - sides_bp_stats['red_pick_num'], 0)
    red_pick_rate = robust_division(sides_bp_stats['red_pick_num'], num_games - full_ban_num - sides_bp_stats['blue_pick_num'], 0)

    return {
        'blue_ban_ratio': round(blue_ban_ratio, 4),
        'red_ban_ratio': round(red_ban_ratio, 4),
        'blue_pick_rate': round(blue_pick_rate, 4),
        'red_pick_rate': round(red_pick_rate, 4),
        'full_ban_num': full_ban_num,
        'full_ban_rate': round(full_ban_rate, 4),
        'full_pick_num': full_pick_num,
        'full_pick_rate': round(full_pick_rate, 4),
        'full_bp_num': full_bp_num,
        'full_bp_rate': round(full_bp_rate, 4),
        'full_win_rate': round(full_win_rate, 4)
    }

def get_notable_teams_stats(expanded_game_data_df):
    # TODO: get pick rate for each team, then get most pick rate team

    pick_games_df = expanded_game_data_df[expanded_game_data_df['pick_side'].notna()]
    pick_team_summary = pick_games_df.groupby('pick_team').agg(
        pick_num = ('pick_team', 'size'),
        win_num = ('result', 'sum')
    )
    if pick_team_summary.empty:
        pick_notable_teams_dict = {
            'mpnt_team_name': "",
            'mpnt_pick_num': 0,
            'mpnt_win_num': 0,
            'mpnt_win_rate': 0,
            'mwrt_team_name': "",
            'mwrt_pick_num': 0,
            'mwrt_win_num': 0,
            'mwrt_win_rate': 0,
        }
    else:
        pick_team_summary.reset_index(inplace=True)
        pick_team_summary['win_rate'] = pick_team_summary['win_num'] / pick_team_summary['pick_num']

        # get most pick number team
        mpnt = pick_team_summary.sort_values(by = ['pick_num', 'win_rate'], ascending=False).head(1)

        # get most win rate team
        mwrt = pick_team_summary.sort_values(by = ['win_rate', 'pick_num'], ascending=False).head(1)

        pick_notable_teams_dict = {
            'mpnt_team_name': mpnt['pick_team'].iloc[0],
            'mpnt_pick_num': mpnt['pick_num'].iloc[0],
            'mpnt_win_num': mpnt['win_num'].iloc[0],
            'mpnt_win_rate': round(mpnt['win_rate'].iloc[0], 4),
            'mwrt_team_name': mwrt['pick_team'].iloc[0],
            'mwrt_pick_num': mwrt['pick_num'].iloc[0],
            'mwrt_win_num': mwrt['win_num'].iloc[0],
            'mwrt_win_rate': round(mwrt['win_rate'].iloc[0], 4),
        }



    ban_games_df = expanded_game_data_df[expanded_game_data_df['ban_side'].notna()]
    ban_team_summary = ban_games_df.groupby('ban_against_team').agg(
        ban_num = ('ban_against_team', 'size'),
    )
    if ban_team_summary.empty:
        ban_notable_teams_dict =  {
            'mbat_team_name': "",
            'mbat_ban_num': 0,
        }
    else:
        ban_team_summary.reset_index(inplace=True)

        # get most ban against team
        mbat = ban_team_summary.sort_values(by = ['ban_num'], ascending=False).head(1)

        ban_notable_teams_dict = {
            'mbat_team_name': mbat['ban_against_team'].iloc[0],
            'mbat_ban_num':  mbat['ban_num'].iloc[0],
        }

    notable_teams_dict = {}
    notable_teams_dict.update(pick_notable_teams_dict)
    notable_teams_dict.update(ban_notable_teams_dict)

    return notable_teams_dict

def get_all_stats(num_games, expanded_game_data_df):
    sides_bp_stats = get_sides_bp_stats(expanded_game_data_df[['ban_side', 'pick_side']])
    win_lose_stats = get_win_lose_stats(expanded_game_data_df[['result', 'game_time_sec']])
    derived_stats = get_derived_stats(num_games, sides_bp_stats, win_lose_stats)
    notable_team_stats = get_notable_teams_stats(expanded_game_data_df)

    mbat_ban_ratio = robust_division(notable_team_stats['mbat_ban_num'], derived_stats['full_ban_num'], 0)
    
    all_stats = {
        'mbat_ban_ratio': mbat_ban_ratio
    }
    all_stats.update(sides_bp_stats)
    all_stats.update(win_lose_stats)
    all_stats.update(derived_stats)
    all_stats.update(notable_team_stats)

    return all_stats

def get_np_zero_matrix(n, dtype=np.float16):
    return np.zeros(shape=(n,n), dtype = dtype)