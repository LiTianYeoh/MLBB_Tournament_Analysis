# MLBB Tournament Analysis 
This project targets to perform some analysis on the professional Mobile Legends (MLBB) tournament game data. <br>
My original aim was to build a MLBB ban-pick model using machine learning. However, the progress towards this goal has been admittedly rather sluggish (with the excuse that I am a bit busy with work?).

## Data Scraping 
<p>
  <i>*Note: last updated on 05 May 2024</i> <br>
  The /scraping/tournament_game_info directory contains python script to scrape tournament data from Liquipedia. <br>
  <ul>
    <li>
      <b>0_scrape_tournament_list.py:</b> scrapes the list of tournament available in tournament list page such as https://liquipedia.net/mobilelegends/S-Tier_Tournaments, and output to {date_scraped}_tournament_urls.txt
    </li>
    <li>
      <b>1_scrape_tournament_game_info.py:</b> scrapes various tournament game info based on the .txt file above. It outputs a .csv file in game_data directory, and update the tournament_data.csv file.
    </li>
    <li>
      <b>2_consolidate_game_data.py:</b> consolidate all .csv file above into /output/consolidated_game_data_{date}.csv
    </li>
  </ul>
  The latest data is <i>consolidated_game_data_20240505.csv</i>
</p>

## Data Analysis
<p>
  The /analysis/ directory then does analysis on the data scraped. Need to manually transfer/update the 3 files located in /analysis/data directory. <br>
  <ol>
    <li>
      <b>indi_hero_bp.py:</b> creates a ban-pick table and other stats. More explanation on how to read the table can be found in my reddit post here: 
      https://www.reddit.com/r/MobileLegendsGame/comments/18ua27a/mlbb_tournament_dataset_scraped_from_liquipedia/
    </li>
    <li>
      <b>wr_matrix.py:</b> creates what I personally call as the "win rate matrix", where the value in i-th row j-th column entry represents the win rate of hero_i against hero_j.
    </li>
  </ol>
  The outputs will be all placed in /results/ directory.
</p>

## Vector Embedding
<p>
  The /vector_embedding/ directory does vector embedding on the scraped data, which is currently the main focus. Again, need to manually transfer/update the 2 files (consolidated_game_data, hero_info) located in /vector_embedding/data directory.<br>
  Current vector embedding is using couccurence matrix approach (as suggested by ChatGPT), which is simple to be implemented.
  <ol>
    <li>
      <b>cooccurrence_matrix.py:</b> construct the cooccurrence matrix, where the where the value in i-th row j-th column entry represents the chances of hero_j being in the same team given that hero_i is picked.
    </li>
    <li>
      <b>get_closest_hero.py:</b> based on the vector embedding, find N "most similar" heroes to a given hero. In the case of cooccurrence matrix approach, it means finding heroes that share similar teammates as the given hero.
    </li>
  </ol>
  The outputs will be all placed in /results/ directory. <br>
  <b>What's next:</b> perhaps to perform PCA on the coocccurence matrix to reduce the number of features/columns. Then explore on clustering on the heroes, and I shall think about what more can be done using the vector embedding.
</p>
