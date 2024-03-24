import os
import time
from datetime import datetime
from utils import get_soup

# get dircetory name
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, "output")

main_urls = [
    "https://liquipedia.net/mobilelegends/S-Tier_Tournaments",
    "https://liquipedia.net/mobilelegends/A-Tier_Tournaments",
    "https://liquipedia.net/mobilelegends/B-Tier_Tournaments",
    #"https://liquipedia.net/mobilelegends/C-Tier_Tournaments",
    #"https://liquipedia.net/mobilelegends/D-Tier_Tournaments",
]

# initiate empty list of tournament urls
tournament_urls = []

for main_url in main_urls:
    print(f"Scraping tournament urls from '{main_url}'...")
    main_soup = get_soup(main_url)

    # get tournament rows element
    tournament_rows = main_soup.find_all('div', class_='divRow')

    # scrape all tournament urls
    for tournament_elem in tournament_rows:
        tournament_url_elem = tournament_elem.find('div', class_ = 'Tournament').find('b').find('a')
        tournament_url = tournament_url_elem.get('href')
        tournament_name = tournament_url_elem.get_text()
        # check is winner exist, i.e. tournament have finished
        tournament_winner_elem = tournament_elem.find('div', class_ = 'FirstPlace')
        winner_player_elem = tournament_winner_elem.find('span', class_ = 'Player')
        if winner_player_elem is None:
            warning_msg = f"Omitting tournament '{tournament_name}' as could not find the winner."
            #print(warning_msg)
            continue
        winner_a_tag = winner_player_elem.find('a')
        if winner_a_tag is None:
            warning_msg = f"Omitting tournament '{tournament_name}' as could not find the winner."
            #print(warning_msg)
            continue
        tournament_urls.append("https://liquipedia.net" + tournament_url)
        #print(f"Scraped tournament url for {tournament_name}")


num_tournaments = len(tournament_urls)

# output to .txt file
curr_date = datetime.now().strftime('%Y%m%d')
tournament_urls_name = f"{curr_date}_tournament_urls.txt"
tournament_urls_path = os.path.join(output_dir, tournament_urls_name)

# Write the URLs to the file
with open(tournament_urls_path, 'w') as file:
    for tournament_url in tournament_urls:
        file.write(tournament_url + '\n')
print(f"{num_tournaments} tournament urls saved at '{tournament_urls_name}'")