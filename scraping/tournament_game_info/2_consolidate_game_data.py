import os
import pandas as pd
from datetime import datetime
from utils import check_tournament_codes


# output name
tournament_data_name = "tournament_data.csv"

curr_date = datetime.now().strftime("%Y%m%d")
output_name = f"consolidated_game_data_{curr_date}.csv"


# get dircetory path
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, "output")
game_data_dir = os.path.join(output_dir, "game_data")

# read tournament_data.csv
tournament_data_path = os.path.join(output_dir, tournament_data_name)
tournament_data_df = pd.read_csv(tournament_data_path)
all_tournaments_csv = tournament_data_df['csv_name'].tolist()

# list all csv in output
all_data_names = os.listdir(game_data_dir)
files_to_include = list(set(all_data_names) & set(all_tournaments_csv))

# read all found game data
if len(files_to_include) == 0:
    print("No valid tournament game data found.")
else:
    game_data_list = []
    print(f"Consolidating {len(files_to_include)} tournament(s) game data...")

    for file_name in files_to_include:
        file_path = os.path.join(game_data_dir, file_name)
        game_data = pd.read_csv(file_path)
        game_data_list.append(game_data)

    full_game_data_df = pd.concat(game_data_list, ignore_index=True)
    full_game_data_df.sort_values(by = ['tournament_code'], ascending=True, inplace=True)

    # Output to csv
    csv_path = os.path.join(output_dir, output_name)
    full_game_data_df.to_csv(csv_path, index=False)
    print(f"Game data saved as '{csv_path}'")
