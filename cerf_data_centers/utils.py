import numpy as np
import networkx

def convert_sqft_to_grid_cells(
        sqft: float = 1000000,
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

def get_normalized_value(
        G: networkx.Graph,
        attribute: str, 
        node: tuple,
        max_value,
        min_value) -> float:
    """
    Normalize the value of a specified attribute for a given node in a graph.
    This function retrieves the values of the specified attribute for all nodes in the graph,
    finds the minimum and maximum values, and then normalizes the value for the specified node
    based on these min and max values.
    Parameters
    ----------
    G : networkx.Graph
        The graph containing the nodes.
    attribute : str
        The attribute to normalize (e.g., 'locational_cost').
    node : any
        The node for which to normalize the attribute value.
    Returns
    -------
    float
        The normalized value of the specified attribute for the given node.
        The value is normalized to a range between 0 and 1.

    """
    # collect node value for the specified attribute
    node_value = G.nodes[node][attribute]

    # Normalize the value for the specified node
    if max_value != min_value:
        normalized_value = (node_value - min_value) / (max_value - min_value)
    else:
        normalized_value = 0.0  

    return normalized_value
