import os
import requests
from bs4 import BeautifulSoup
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))

# Get table
main_url = "https://mobile-legends.fandom.com/wiki/List_of_heroes"

response = requests.get(main_url)

soup = BeautifulSoup(response.text, 'html.parser')

table = soup.find('table')


def get_cell_text(cell):
    cell_text = cell.text.strip()
    if cell_text == "":
        return None
    else:
        return cell_text

# Parse table into df
hero_data = []

rows = table.find_all('tr')
first_row = rows[0]
headers = [header.text.strip() for header in first_row.find_all('th')]

for row in rows[1:]:
    cells = row.find_all('td')
    row_data = [get_cell_text(cell) for cell in cells]
    hero_data.append(row_data)

hero_df = pd.DataFrame(hero_data, columns=headers)

# Remove empty rows
hero_df = hero_df.dropna(how='all')

# get short hero name
hero_df['Name'] = hero_df['Hero'].str.split(',').str[0]

# rename hero code column
hero_df = hero_df.rename(columns = {
    'Hero order': 'Hero Code'
})

# Output to csv
csv_name = "hero_info.csv"
csv_path = os.path.join(script_dir, csv_name)

hero_df.to_csv(csv_path, index=False) 

print(f"DataFrame saved to {csv_path}")