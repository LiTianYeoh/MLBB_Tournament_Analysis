import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import re

def convert_list_to_tuple(hero_list):
    if hero_list is None:
        return None
    else:
        return tuple(hero_list)

def get_soup(url, sleeptime = 2):
    time.sleep(sleeptime)

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    return soup
    

def check_duplicate_tournament(curr_tournament, existing_tournaments):
    if curr_tournament in existing_tournaments:
        return existing_tournaments.index(curr_tournament)
    else:
        return None

def check_qualifying_stage_url(a_elem):
    elem_text = a_elem.get_text().lower()
    if ("click" in elem_text) and ("result" in elem_text):
        return True
    else:
        return False

def get_tournament_data(tournament_data_elem):
    sub_divs = tournament_data_elem.find_all('div')
    sub_div_texts = [sub_div.get_text().strip() for sub_div in sub_divs]

    start_date = None
    end_date = None
    patch_code = None
    tier = None
    
    for i in range(len(sub_div_texts)-1):
        sub_div_text = sub_div_texts[i].lower()
        if ("start" in sub_div_text) and ("date" in sub_div_text):
            start_date = sub_div_texts[i+1].replace("-", "")
            if len(start_date) != 8:
                start_date = None
        if ("end" in sub_div_text) and ("date" in sub_div_text):
            end_date = sub_div_texts[i+1].replace("-", "")
            if len(end_date) != 8:
                end_date = None
        if ("patch" in sub_div_text):
            patch_code = sub_div_texts[i+1]
        if "liquipedia tier" in sub_div_text:
            tier_code = sub_div_texts[i+1]
            tier_pattern = re.compile(r'([SABCD])-Tier')
            tier_match = tier_pattern.search(tier_code)
            tier = tier_match.group(1) if tier_match else None

    return {
        'start_date': start_date,
        'end_date': end_date,
        'patch_code': patch_code,
        'tier': tier
    }

def get_points_list(result_list):
    # check if any game exist
    if len(result_list) == 0:
        return []
    
    points_list = [0]  # Initialize with 0 as the first value
    cumulative_value = 0

    for value in result_list[:-1]:
        if value is not None:
            cumulative_value += value
        points_list.append(cumulative_value)

    return points_list

def get_team_names(match_elem):
    header_elems = match_elem.find('div', class_ = "brkts-popup-header-dev")
    team_name_elems = header_elems.find_all('span', class_ = "name")

    try:
        t1_name_elem = team_name_elems[0]
        t1_name = t1_name_elem.find('a').get_text()
    except:
        t1_name = None

    try:
        t2_name_elem = team_name_elems[1]
        t2_name = t2_name_elem.find('a').get_text()
    except:
        t2_name = None

    return t1_name, t2_name

def _adjust_hero_name(hero_name):

    # if 'popol' in hero_name.lower():
    #     return 'popol'
    
    return hero_name.lower()
    
def match_hero_codes(hero_list, hero_info_dict):
    if hero_list is None:
        return None
    
    hero_codes = [hero_info_dict[_adjust_hero_name(hero_name)] for hero_name in hero_list]

    return hero_codes


def parse_game_elems(game_elems):

    t1_sides_data = []
    t1_picks_data = []
    t1_result_data = []

    t2_sides_data = []
    t2_picks_data = []
    t2_result_data = []

    game_time_str_data = []
    game_time_sec_data = []


    for game_elem in game_elems:
        pick_elems = game_elem.find_all('div', attrs={'class': False})
        t1_pick_elem = pick_elems[0]
        t2_pick_elem = pick_elems[1]

        t1_side, t1_heroes = parse_pick_elem(t1_pick_elem)
        t2_side, t2_heroes = parse_pick_elem(t2_pick_elem)

        if len(t1_heroes) == 0 and len(t2_heroes) == 0:
            # no hero pick data, skip to next game
            continue

        t1_sides_data.append(t1_side)
        t1_picks_data.append(t1_heroes)
        t2_sides_data.append(t2_side)
        t2_picks_data.append(t2_heroes)

        game_time_elem = game_elem.find('div', class_ = "brkts-popup-body-element-vertical-centered")
        game_time_str = game_time_elem.text.strip()
        
        game_time_str_data.append(game_time_str)
        game_time_sec_data.append(convert_game_time_str_sec(game_time_str))

        result_elems = game_elem.find_all('div', class_ = "brkts-popup-spaced")
        t1_res_elem = result_elems[0]
        t2_res_elem = result_elems[1]
        t1_result = check_green_tick(t1_res_elem)        
        t2_result = check_green_tick(t2_res_elem)

        t1_result_data.append(t1_result)
        t2_result_data.append(t2_result)

    t1_points_data = get_points_list(t1_result_data)
    t2_points_data = get_points_list(t2_result_data)

    return {
        't1_side': t1_sides_data,
        't1_picks': t1_picks_data,
        't1_result': t1_result_data,

        't2_side': t2_sides_data,
        't2_picks': t2_picks_data,
        't2_result': t2_result_data,

        'game_time_str': game_time_str_data,
        'game_time_sec': game_time_sec_data,
        't1_points': t1_points_data,
        't2_points': t2_points_data,
    }

def parse_pick_elem(team_pick_elem):
    hero_elems = team_pick_elem.find_all('div')
    hero_colors = []
    hero_names = []

    for hero_elem in hero_elems:

        #get team color
        curr_hero_color = hero_elems[0].get('class')[0]
        if 'blue' in curr_hero_color:
            hero_colors.append('blue')
        elif 'red' in curr_hero_color:
            hero_colors.append('red')
        else:
            hero_colors.append('unknown')

        #get hero names
        hero_a_tag = hero_elem.find('a')
        if hero_a_tag is not None:
            hero_name = hero_a_tag.get('title')
            hero_names.append(hero_name)

    # get team side
    first_color = hero_colors[0]

    # Compare the first element with the rest of the elements
    if all(element == first_color for element in hero_colors):
        team_side = first_color
    else:
        team_side = None

    return team_side, hero_names

def check_green_tick(result_elem):
    if result_elem.find('i') is not None:
        #if 'green' in result_elem.find('i').get('class').lower():
        return 1
    elif result_elem.find('img') is not None:
        if 'no' in result_elem.find('img').get('src').lower():
            return 0
    else:
        return None

    # img_elem = result_elem.find('img')
    # src_text = img_elem.get('src')
    # if 'green' in src_text.lower():
    #     return 1
    # if 'no' in src_text.lower():
    #     return 0
    # else:
    #     return None
    
def parse_ban_elem(ban_elem):
    ban_table_elem = ban_elem.find('table')

    t1_bans_data = []
    t2_bans_data = []

    rows = ban_table_elem.find_all('tr')
    for row in rows[1:]:
        cells = row.find_all('td')
        t1_bans_cell = cells[0]
        t2_bans_cell = cells[2]

        t1_bans_elems = t1_bans_cell.find_all('a')
        t2_bans_elems = t2_bans_cell.find_all('a')

        t1_bans = [elem.get('title') for elem in t1_bans_elems]
        t2_bans = [elem.get('title') for elem in t2_bans_elems]

        if len(t1_bans) == 0 and len(t2_bans) == 0:
            # don't save ban data is is empty
            continue

        t1_bans_data.append(t1_bans)
        t2_bans_data.append(t2_bans)

    return {
        't1_bans': t1_bans_data,
        't2_bans': t2_bans_data
    }

def convert_game_time_str_sec(game_time_str):
    time_parts_str = game_time_str.split(':')
    try:
        time_parts_int = [int(part) for part in time_parts_str]

        if len(time_parts_int) == 3:
            return (time_parts_int[0] * 3600) + (time_parts_int[1]* 60) + time_parts_int[2]
        elif len(time_parts_int) == 2:
            return (time_parts_int[0]* 60) + time_parts_int[1]
        else:
            return None
    except:
        return None
    
def convert_match_date(match_datetime_raw):
    try:
        match_date_raw = match_datetime_raw.split("-")[0].strip()
        match_date = datetime.strptime(match_date_raw, "%B %d, %Y").strftime("%Y%m%d")
        return match_date
    except:
        return None

def get_game_data(tournament_code, soup, verbose = False):
    # Get list of elements containing match info
    match_elems = soup.find_all('div', class_='brkts-popup brkts-match-info-popup')
    if verbose is True:
        print(f"- Found {len(match_elems)} number of matches.")

    game_data_df = pd.DataFrame(
        columns = [
            'tournament_code', 'date', 
            't1_name', 't1_side', 't1_picks', 't1_bans', 't1_result',
            't2_name', 't2_side', 't2_picks', 't2_bans', 't2_result',
            'game_time_str', 'game_time_sec', 
            'match_format_BON', 'game_no', 't1_points', 't2_points'
        ]
    )
    for match_elem in match_elems:

        t1_name, t2_name = get_team_names(match_elem)
        if verbose is True:
            print(t1_name, t2_name)

        # Zoom into match details element
        match_details_elem = match_elem.find('div', class_ = "brkts-popup-body")

        date_elem = match_details_elem.find('span', class_ = "timer-object")
        match_datetime_raw = date_elem.text.strip()
        match_date = convert_match_date(match_datetime_raw)

        # Get game info except for ban
        game_elems = match_details_elem.find_all('div', class_ = "brkts-popup-body-element brkts-popup-body-game")
        # if no game info, skip match_elem
        if len(game_elems) == 0:
            continue
        game_data_dict = parse_game_elems(game_elems)
        
        # Get ban info
        ban_elem = match_details_elem.find('div', class_ = "brkts-popup-mapveto")
        if ban_elem is None:
            num_games = len(game_data_dict['t1_picks'])
            ban_data_dict = {
                't1_bans': [[] for _ in range(num_games)],
                't2_bans': [[] for _ in range(num_games)]
            }
        else:
            ban_data_dict = parse_ban_elem(ban_elem)

        match_data_dict = {**game_data_dict, **ban_data_dict}

        # Create match_data_df
        if verbose is True:
            print(match_data_dict)
        match_data_df = pd.DataFrame.from_dict(match_data_dict, orient='index').transpose()

        if len(game_data_dict['t1_points']) > 0:
            match_format_BON = 2*max(game_data_dict['t1_points'][-1], game_data_dict['t2_points'][-1]) + 1
        else:
            match_format_BON = 0

        match_data_df['tournament_code'] = tournament_code
        match_data_df['date'] = match_date
        match_data_df['t1_name'] = t1_name
        match_data_df['t2_name'] = t2_name
        match_data_df['match_format_BON'] = match_format_BON
        match_data_df['game_no'] = range(1, len(match_data_df) + 1)

        game_data_df = pd.concat([game_data_df, match_data_df], ignore_index=True)

    return game_data_df


def check_tournament_codes(file_name, tournament_codes):
    root, file_ext = os.path.splitext(file_name)
    file_tournament_code = root.split("_")[0]
    if (file_ext == ".csv") and (file_tournament_code in tournament_codes):
        return True
    else:
        return False

def clean_filename(filename):
    # Replace characters not allowed in file names with underscores
    cleaned_filename = re.sub(r'[\\/:"*?<>|]+', '_', filename)
    return cleaned_filename