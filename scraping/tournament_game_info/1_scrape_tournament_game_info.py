import os
import time
import pandas as pd
from datetime import datetime
from utils import get_soup, check_duplicate_tournament, check_qualifying_stage_url, get_tournament_data, get_game_data, match_hero_codes, clean_filename, convert_list_to_tuple
from tqdm import tqdm

tournament_urls_name = '20240505_tournament_urls.txt'

# get dircetory path
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, "output")
game_data_dir = os.path.join(output_dir, "game_data")
if not os.path.exists(game_data_dir):
    os.mkdir(game_data_dir)

# read hero info csv
hero_info_path = os.path.join(script_dir, "hero_info.csv")
hero_info_df = pd.read_csv(hero_info_path, usecols=['Name', 'Hero Code'])
hero_info_df['Name'] = hero_info_df['Name'].str.lower()

hero_info_dict = hero_info_df.set_index('Name')['Hero Code'].to_dict()


# read current tournament data if exist
tournament_data_path = os.path.join(output_dir, "tournament_data.csv")
if os.path.exists(tournament_data_path):
    tournament_data_df = pd.read_csv(tournament_data_path)
else:
    tournament_data_df = pd.DataFrame(
        columns = [
            'tournament_code', 'tournament_name', 'tier', 
            'start_date', 'end_date', 'patch_code',
            'url', 'last_updated', 'csv_name'
        ]
    )
tournament_code = tournament_data_df['tournament_code'].max()
if pd.isna(tournament_code):
    tournament_code = 0
existing_tournaments_url = tournament_data_df['url'].tolist()

# read tournament urls
tournament_urls_path = os.path.join(output_dir, tournament_urls_name)
with open(tournament_urls_path, 'r') as file:
    tournament_main_urls = file.read().splitlines()

# remove duplicate
new_tournament_main_urls = list(set(tournament_main_urls))
print(f"Found {len(tournament_main_urls)} URLs with {len(new_tournament_main_urls)-len(tournament_main_urls)} duplicates.")

#new_tournament_main_urls = new_tournament_main_urls[0:20]

# Scrape all tournament urls
tournament_pbar = tqdm(new_tournament_main_urls, desc = "Progress")
for tournament_main_url in tournament_pbar:

    # check for possible duplicate tournament
    potential_duplicate = check_duplicate_tournament(tournament_main_url, existing_tournaments_url)
    if potential_duplicate is not None:
        existing_tournament_name = existing_tournaments_url[potential_duplicate]
        warning_msg = f"!!! Warning: Duplicate tournament (by URL) found: {existing_tournament_name}"
        tqdm.write(warning_msg)
        continue
        #time.sleep(2)
        #warnings.warn(warning_msg)
    
    tournament_code += 1
    all_game_data_list = []

    # Get tournament main page
    main_soup = get_soup(tournament_main_url)

    ## Scrape tournament data
    tournament_name_elem = main_soup.find('h1', class_='firstHeading')
    tournament_name = tournament_name_elem.text.strip()
    tournament_pbar.set_postfix({
        'Code': tournament_code,
        'Tournament':tournament_name[:30]
    })
    #print(f"------ Found current tournament name: {tournament_name}")

    tournament_data_elem = main_soup.find('div', class_='fo-nttax-infobox-wrapper infobox-mobilelegends')
    # Get tournament data
    tournament_data_dict = get_tournament_data(tournament_data_elem)



    ## Scrape game data
    #print("-- Scraping Bracket Stage game data...")
    ko_stage_game_data_df = get_game_data(tournament_code, main_soup, verbose=False)
    ko_stage_game_data_df['tournament_stage'] = "bracket"
    all_game_data_list.append(ko_stage_game_data_df)

    ## Get qualifying stage url and data
    a_tags_elems = main_soup.find_all('a')
    qualifier_stage_elems = list(filter(check_qualifying_stage_url, a_tags_elems))
    for qualifier_stage_elem in qualifier_stage_elems:
        relative_url = qualifier_stage_elem.get('href')
        qualifier_stage_url = "https://liquipedia.net" + relative_url
        qualifier_soup = get_soup(qualifier_stage_url)

        qualifier_stage_game_data_df = get_game_data(tournament_code, qualifier_soup, verbose=False)
        qualifier_stage_game_data_df['tournament_stage'] = "qualifiers"
        all_game_data_list.append(qualifier_stage_game_data_df)

    full_game_data_df = pd.concat(all_game_data_list, ignore_index=True)

    # remove potential qualifier match that is also shown in main_url
    column_names = full_game_data_df.columns.tolist()
    column_names.remove("tournament_stage")
    full_game_data_df['t1_picks'] = full_game_data_df['t1_picks'].apply(convert_list_to_tuple)
    full_game_data_df['t1_bans'] = full_game_data_df['t1_bans'].apply(convert_list_to_tuple)
    full_game_data_df['t2_picks'] = full_game_data_df['t2_picks'].apply(convert_list_to_tuple)
    full_game_data_df['t2_bans'] = full_game_data_df['t2_bans'].apply(convert_list_to_tuple)

    full_game_data_df.drop_duplicates(subset=column_names, keep='last', inplace=True)


    #Convert hero name to codes
    # full_game_data_df['t1_picks'] = full_game_data_df['t1_picks'].apply(lambda x: match_hero_codes(x, hero_info_dict))
    # full_game_data_df['t1_bans'] = full_game_data_df['t1_bans'].apply(lambda x: match_hero_codes(x, hero_info_dict))
    # full_game_data_df['t2_picks'] = full_game_data_df['t2_picks'].apply(lambda x: match_hero_codes(x, hero_info_dict))
    # full_game_data_df['t2_bans'] = full_game_data_df['t2_bans'].apply(lambda x: match_hero_codes(x, hero_info_dict))

    # Output to csv
    #print(f"--- Saving scraped data ....")
    # Output game data
    game_data_csv_name = f"{tournament_code}_{clean_filename(tournament_name)}.csv"
    game_data_path = os.path.join(game_data_dir, game_data_csv_name)
    full_game_data_df.to_csv(game_data_path, index=False)
    #print(f"Game data saved as '{game_data_csv_name}'")

    # Update tournament_data_df
    # Get the current date
    last_updated = datetime.now().strftime('%Y%m%d')

    curr_tournament_row = {**tournament_data_dict,
        'tournament_code': tournament_code,
        'tournament_name': tournament_name,
        'url': tournament_main_url,
        'last_updated': last_updated,
        'csv_name': game_data_csv_name
    }

    curr_tournament_df = pd.DataFrame(curr_tournament_row, index = [0])

    tournament_data_df = pd.concat([tournament_data_df, curr_tournament_df], axis=0, ignore_index=True)
    tournament_data_df.to_csv(tournament_data_path, index=False)

    #print(f"Tournament data updated.")

