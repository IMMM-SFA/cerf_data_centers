import numpy as np

def convert_sqft_to_grid_cells(sqft):

    square_meters = sqft * 0.092903

    grid_cells = np.ceil(square_meters / (100 * 100))

    return grid_cells
