# MLBB Tournament Analysis 
This project targets to perform some analysis on the professional Mobile Legends (MLBB) tournament game data. <br>
My original aim was to build a MLBB ban-pick model using machine learning. However, the progress towards this goal has been admittedly rather sluggish (with the excuse that I am a bit busy with work?).

## Data Scraping 
<p>
  <i>*Note: last updated on 29 Dec 2023</i> <br>
  The /scraping/tournament_game_info directory contains python script to scrape tournament data from Liquipedia. <br>
  <ul>
    <li>
      <b>0_scrape_tournament_list.py:</b> scrapes the list of tournament available in tournament list page such as https://liquipedia.net/mobilelegends/S-Tier_Tournaments, and output to {date_scraped}_tournament_urls.txt
    </li>
    <li>
      <b>1_scrape_tournament_game_info.py:</b> scrapes various tournament game info based on the .txt file above. It outputs a .csv file in game_data directory, and update the tournament_data.csv file.
    </li>
    <li>
      <b>2_consolidate_game_data.py:</b> consolidate all .csv file above into /output/consolidated_game_data.csv
    </li>
  </ul>

</p>

## Data Analysis
<p>
  The /analysis/ directory then does analysis on the data scraped. Need to manually transfer/update the 3 files located in /analysis/data directory. <br>
  This will be the main focus on now, and currently there are 2 analysis scripts:
  <ol>
    <li>
      <b>indi_hero_bp.py:</b> creates a ban-pick table and other stats. More explanation on how to read the table can be found in my reddit post here: 
      https://www.reddit.com/r/MobileLegendsGame/comments/18ua27a/mlbb_tournament_dataset_scraped_from_liquipedia/
    </li>
    <li>
      <b>wr_matrix.py:</b> creates what I personally call as the "win rate matrix", where the value in i-th row j-th column entry represents the win rate of hero_i against hero_j.
    </li>
  </ol>
  The outputs will be all placed in /results/ directory. <br>
  <br>
  What I plan to do next is on vector embedding for mlbb heroes, most likely based on this: https://github.com/evanthebouncy/dota_hero_semantic_embedding <br>
</p>
