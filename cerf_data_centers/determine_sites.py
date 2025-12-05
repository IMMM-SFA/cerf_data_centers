from collections import deque
from typing import List, Dict, Any
from affine import Affine

import rasterio
import numpy as np
import networkx as nx


def get_region_suit_array(
    region_array: np.ndarray,
    suit_array: np.ndarray,
    region_id: int
) -> np.ndarray:
    """
    Return the suitability array for a specific region.

    Args:
        region_array (np.ndarray): 
            A 2D numpy array representing region IDs for each grid cell.
        suit_array (np.ndarray): 
            A 2D numpy array representing the suitability value of each grid cell.
        region_id (int): 
            The ID of the region for which to extract the suitability array.

    Returns:
        np.ndarray: 
            A 2D numpy array where only the cells belonging to the specified region
            retain their suitability values, and all other cells are set to zero.

    Raises:
        ValueError: If the specified region_id is not present in region_array.
    """
    if region_id not in np.unique(region_array):
        raise ValueError(f"Region ID {region_id} not found in the region raster.")

    # Create a mask for the specified region
    region_mask = np.where(region_array == region_id, 1, 0)

    # Apply the mask to the suitability array
    region_suit_array = suit_array * region_mask

    return region_suit_array


def get_connected_nodes(
    graph: nx.Graph,
    start_node,
    min_block_size: int
) -> list:
    """
    Perform a breadth-first search (BFS) to find a set of connected nodes in a graph,
    starting from a specified node, and return at least `min_block_size` nodes.

    Args:
        graph (nx.Graph): The graph in which to search for connected nodes.
        start_node: The node from which to start the search.
        min_block_size (int): The minimum number of connected nodes to return.

    Returns:
        list: A list of nodes representing a connected component containing at least
            `min_block_size` nodes, starting from `start_node`.

    Raises:
        ValueError: If `start_node` is not present in the graph, or if there are not
            enough connected nodes reachable from `start_node` to satisfy `min_block_size`.
    """
    if start_node not in graph:
        raise ValueError("Start node not in graph.")

    visited = set()
    queue = deque([start_node])
    result = []

    # Get connected nodes using Breadth-First Search (BFS)
    while queue and len(result) < min_block_size:
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
            result.append(node)
            queue.extend(n for n in graph.neighbors(node) if n not in visited)

    if len(result) < min_block_size:
        raise ValueError("Not enough connected nodes from the starting node.")

    return result


def build_graph(
    region_suit_array: "np.ndarray",
    min_block_size: int,
    raster_names: list[str],
    node_values: dict[tuple[int, int], dict[str, float]]
) -> "nx.Graph":
    """
    Build a graph from the region suitability array, where each node represents a suitable grid cell
    and edges connect adjacent suitable cells. Node attributes are populated with raster values.

    Args:
        region_suit_array (np.ndarray): 2D numpy array representing the suitability of each grid cell in the region.
                                        Suitable cells should have a value of 1.
        min_block_size (int): Minimum number of connected nodes (grid cells) required for a site to be considered valid.
        raster_names (list[str]): List of raster data names to be used as node attributes.
        node_values (dict[tuple[int, int], dict[str, float]]): Dictionary mapping (row, col) tuples to dictionaries
                                                               of raster names and their corresponding values.

    Returns:
        nx.Graph: A NetworkX graph where nodes represent suitable grid cells and edges represent connectivity
                  between adjacent suitable cells. Node attributes are populated with raster values.
    """
    rows, cols = np.where(region_suit_array == 1)
    one_pixels = set(zip(rows, cols))

    neighbor_offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    G = nx.Graph()

    # Add nodes and edges
    for row, col in one_pixels:
        G.add_node((row, col))
        for dr, dc in neighbor_offsets:
            neighbor = (row + dr, col + dc)
            if neighbor in one_pixels:
                G.add_edge((row, col), neighbor)

    for component in list(nx.connected_components(G)):
        if len(component) < min_block_size:
            G.remove_nodes_from(component)

    # Assign raster values to each node
    for name in raster_names:
        for node in G.nodes:
            G.nodes[node][name] = node_values[node][name]

    return G


def site_based_on_siting_score(
    G: nx.Graph,
    number_of_sites: int,
    min_block_size: int,
    region_name: str,
    transform: Affine,
    attribute: str = 'total_weighted_siting_score'
) -> List[Dict[int, Dict[str, Any]]]:
    """
    Select sites based on the minimum locational cost and gravity score from a graph of suitable areas.

    Args:
        G (nx.Graph): The graph representing the siting areas, where nodes are grid cells and
            node attributes include locational cost and other relevant data.
        number_of_sites (int): The desired number of sites to be selected.
        min_block_size (int): The minimum number of connected nodes required to consider a site valid.
        region_name (str): The name of the region for which sites are being selected.
        transform (Affine): The affine transformation to convert pixel coordinates to geographic coordinates.
        attribute (str, optional): The attribute in the graph nodes that contains the locational cost.
            Defaults to 'locational_cost'.

    Returns:
        List[Dict[int, Dict[str, Any]]]: A list of dictionaries, each containing information about a selected site.
            Each dictionary has a single key (site index) mapping to a dictionary with the following keys:
                - 'region_name' (str): Name of the region.
                - 'min_node' (Tuple[float, float]): Geographic coordinates (x, y) of the minimum cost node.
                - 'locational_cost' (float): Locational cost value for the site.
                - 'coord_list' (List[Tuple[float, float]]): List of geographic coordinates (x, y) for the selected nodes.
                - 'row_col_list' (List[Tuple[int, int]]): List of (row, col) indices for the selected nodes.
    """
    # Create a copy of the graph to avoid modifying the original
    H = G.copy()
    i = 0

    result_list: List[Dict[int, Dict[str, Any]]] = []

    # Loop until we have the desired number of sites or not enough areas left big enough to site
    while len(result_list) < number_of_sites and H.number_of_nodes() > 0:
        try:
            # Collect the node with the smallest locational cost
            min_node = min(
                (node for node, data in H.nodes(data=True) if attribute in data),
                key=lambda node: H.nodes[node][attribute]
            )
        except ValueError:
            # No nodes left
            break

        # Check how many connected components there are surrounding the min node
        connections = list(nx.node_connected_component(H, min_node))

        # If it has enough neighbors, get the connected nodes
        if len(connections) >= min_block_size:
            # Get connected nodes up to block size for data center campus
            selected_neighbors = get_connected_nodes(H, min_node, min_block_size)

            # Create a list of nodes that are now taken
            nodes_to_remove = [min_node] + selected_neighbors

            result_dict: Dict[int, Dict[str, Any]] = {}

            # Min node info
            row, col = min_node
            x, y = rasterio.transform.xy(transform, row, col)

            # Get neighbor info
            coord_list = []
            row_col_list = []
            for neighbor in selected_neighbors:
                row_n, col_n = neighbor
                x_n, y_n = rasterio.transform.xy(transform, row_n, col_n)
                coord_list.append((x_n, y_n))
                row_col_list.append((row_n, col_n))

            result_dict[i] = {
                'region_name': region_name,
                'min_node': (x, y),
                'weighted_siting_score': H.nodes[min_node][attribute],
                'locational_cost': H.nodes[min_node]['locational_cost'],
                'normalized_locational_cost': H.nodes[min_node]['normalized_locational_cost'],
                'normalized_gravity_score': H.nodes[min_node]['normalized_gravity_score'],
                'coord_list': coord_list,
                'row_col_list': row_col_list
            }

            # attach parameters to the result dict
            result_dict[i].update(H.nodes[min_node]['parameters'])
            
            # Add the result to the result list
            result_list.append(result_dict)

            # Remove sited areas from available
            H.remove_nodes_from(nodes_to_remove)
            i += 1

        else:
            # Bad node (not enough neighbors): remove only the min_node and continue
            H.remove_node(min_node)

    return result_list
