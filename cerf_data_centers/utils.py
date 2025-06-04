import numpy as np


def convert_sqft_to_grid_cells(
        sqft: float | int | np.ndarray,
        grid_cell_width_meters: float = 100,
        grid_cell_height_meters: float = 100) -> int | np.ndarray:
    """
    Convert area in square feet to the number of grid cells.

    Parameters
    ----------
    sqft : float, int, or numpy.ndarray
        Area in square feet. Can be a scalar or a numpy array.
    grid_cell_width_meters : float, optional
        Width of the grid cell in meters. Default is 100.
    grid_cell_height_meters : float, optional
        Height of the grid cell in meters. Default is 100.

    Returns
    -------
    int or numpy.ndarray
        Number of grid cells required to cover the input area.
        The result is always rounded up to the nearest integer.
    """
    SQFT_TO_SQM = 0.092903
    square_meters = sqft * SQFT_TO_SQM

    grid_cells = np.ceil(square_meters / (grid_cell_width_meters * grid_cell_height_meters))
    return grid_cells
