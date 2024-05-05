import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

def adjust_hero_name(hero_name):

    # if 'popol' in hero_name.lower():
    #     return 'popol'

    return hero_name.lower()


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

class CooccurenceMatrix:
    def __init__(self, total_num_heroes, team_num_heroes=5):
        self.cooccur_matrix = np.zeros(shape=(total_num_heroes, total_num_heroes), dtype = np.int16)
        self.team_num_heroes = team_num_heroes
        self.add_matrix = np.ones((self.team_num_heroes, self.team_num_heroes)) - np.identity(team_num_heroes, dtype = np.int16)
        
    def add_count(self, idx_list, val = 1):
        if len(idx_list) != self.team_num_heroes:
            print(f"Index list length is {len(idx_list)} instead of {self.team_num_heroes}!")
        else:
            row_slice_idx = [[idx] for idx in idx_list]
            self.cooccur_matrix[row_slice_idx, idx_list] = self.cooccur_matrix[row_slice_idx, idx_list] + self.add_matrix*val

    def get_normalized_cooccur_matrix(self):
        row_sums = self.cooccur_matrix.sum(axis = 1)
        non_zeros_idx = np.nonzero(row_sums)

        normalized_matrix = self.cooccur_matrix.copy().astype(np.float64)
        normalized_matrix[non_zeros_idx] = self.cooccur_matrix[non_zeros_idx] / row_sums[non_zeros_idx, np.newaxis]

        return row_sums, normalized_matrix

def compute_similarity(vector, matrix, similarity_type='euclidean'):

    if similarity_type == 'euclidean':
        # Calculate Euclidean distance
        distances = np.linalg.norm(matrix - vector, axis=1)
    elif similarity_type == 'cosine':
        # Calculate cosine similarity
        similarities = cosine_similarity(vector.reshape(1, -1), matrix)
        # Since cosine similarity returns similarity, we convert it to distance
        distances = 1 - similarities.flatten()
    else:
        raise ValueError("Invalid similarity type. Choose either 'euclidean' or 'cosine'.")

    return distances

def get_n_closest(vector, matrix, n=3, similarity_type='euclidean'):

    # compute similarity of vector to each row in matrix
    distances = compute_similarity(vector, matrix, similarity_type=similarity_type)

    # sort by distance, then get the index for the n lowest
    sorted_indices = np.argsort(distances)
    idx_n_closest = list(sorted_indices[:n])
    dist_n_closest = [distances[idx] for idx in sorted_indices[:n]]

    return idx_n_closest, dist_n_closest