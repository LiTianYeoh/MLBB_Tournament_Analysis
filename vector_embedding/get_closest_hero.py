import os
import numpy as np
import pandas as pd
from datetime import datetime
from utils_embedding import get_n_closest



# define param:
closest_n = 5                       # number of closest hero to find
similarity_type = 'euclidean'         # 'euclidean' or 'cosine'



# dataset names
coo_mat_csv_name = "20240505_204513_hero_cooccurence_matrix.csv"

# get dircetory path
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, "data")
result_dir = os.path.join(script_dir, "results")


# read datasets
# read coocurrence matrix
coo_mat_csv_path = os.path.join(result_dir, coo_mat_csv_name)
cooccur_df = pd.read_csv(coo_mat_csv_path, index_col=0)


# drop last column of pick_count
hero_pick_count = cooccur_df['pick_count'].copy()
cooccur_df.drop(columns = ['pick_count'], inplace=True)

# get all heroes
hero_list = cooccur_df.index.tolist()

# convert to cooccurence matrix
cooccur_matrix = cooccur_df.to_numpy(dtype=np.float64)

# prepare final matrix
pre_final_df = []

for idx in range(len(hero_list)):
    curr_hero = hero_list[idx]
    curr_hero_pick = hero_pick_count[curr_hero]
    curr_vector = cooccur_matrix[idx, :]

    # take n+1 closest as the closest is always the hero itself
    closest_idx, dist = get_n_closest(curr_vector, cooccur_matrix, n=closest_n+1, similarity_type=similarity_type)
    closest_heroes = [hero_list[idx] for idx in closest_idx]

    # cross the list to become [hero_1, dist_1, hero_2, list_2, ...]
    closest_heroes_dist = [val for pair in zip(closest_heroes[1:], dist[1:]) for val in pair]

    pre_final_df.append([curr_hero, curr_hero_pick]+closest_heroes_dist)


# convert to df
colnames = ['hero', 'pick_count'] + [f'{prefix}_{suffix}' for suffix in range(1, closest_n+1) for prefix in ['closest', 'dist']]
final_df = pd.DataFrame(pre_final_df, columns=colnames)

# output analysis result
curr_dt = datetime.now().strftime("%Y%m%d_%H%M%S")
analysis_result_name = f"closest_{closest_n}_heroes_{similarity_type}.xlsx"
analysis_result_path = os.path.join(result_dir, analysis_result_name)

final_df.to_excel(analysis_result_path, index=False)
print(f"Analysis results saved as '{analysis_result_name}'")


