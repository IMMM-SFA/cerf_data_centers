import rasterio
import numpy as np
import networkx as nx
from collections import deque


def get_region_suit_array(region_array, suit_array, region_id):
    
    """
    Get the suitability array for a specific region.
    Parameters:
    region_array (np.array): A 2D numpy array representing the region.
    suit_array (np.array): A 2D numpy array representing the suitability of each grid cell.
    region_id (int): The ID of the region for which to get the suitability array.

    Returns:
    np.array: A 2D numpy array representing the suitability of each grid cell in the specified region.
    """

    if region_id not in np.unique(region_array):
        raise ValueError(f"Region ID {region_id} not found in the region raster.")
    
    # create region mask
    region_mask = np.where(region_array == region_id, 1, 0)

    # create suitable region mask
    region_suit_array = suit_array * region_mask

    return region_suit_array


def get_connected_nodes(graph, start_node, min_block_size):
    """
    Get connected nodes from a starting node in a graph.

    Parameters:
    graph (networkx.Graph): The graph to search.
    start_node (any): The node from which to start the search.
    min_block_size (int): The minimum number of connected nodes (blocks) to return.    

    Returns:
    output_gdf (GeoDataFrame): A GeoDataFrame containing the siting results.

    """ 

    if start_node not in graph:
        raise ValueError("Start node not in graph.")

    visited = set()
    queue = deque([start_node])
    result = []

    # get connected nodes using Breadth-First Search (BFS)
    while queue and len(result) < min_block_size:
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
            result.append(node)
            queue.extend(n for n in graph.neighbors(node) if n not in visited)
    
    if len(result) < min_block_size:
        raise ValueError("Not enough connected nodes from the starting node.")

    return result


def build_graph(region_suit_array, min_block_size, raster_names, node_values):
    """
    Build a graph from the region suitability array.
    Parameters:
    region_suit_array (np.array): A 2D numpy array representing the suitability of each grid cell in the region.
    min_block_size (int): The minimum number of connected nodes (grid cells) required to consider a site valid.
    raster_names (list): A list of names corresponding to the raster data.
    node_values (dict): A dictionary containing values for each node, where keys are tuples of (row, col) and values are dictionaries of raster names and their corresponding values.
    
    Returns:
    G (networkx.Graph): A graph where nodes represent grid cells and edges represent connectivity between suitable grid cells.
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
    
    # For each raster, sample and assign values directly to nodes    
    for name in raster_names:
        for node in G.nodes:
            G.nodes[node][name] = node_values[node][name]

    return G


def site_based_on_locational_cost(G, number_of_sites, min_block_size, region_name, transform, attribute='locational_cost'):
    """                          
    Site based on the minimum locational cost

    Parameters:
    G (networkx.Graph): The graph representing the siting areas.
    number_of_sites (int): The desired number of sites to be selected.
    min_block_size (int): The minimum number of connected nodes required to consider a site valid.
    region_name (str): The name of the region for which sites are being selected.
    transform (Affine): The affine transformation to convert pixel coordinates to geographic coordinates.
    attribute (str): The attribute in the graph nodes that contains the locational cost.

    Returns:
    list: A list of dictionaries, each containing information about a selected site.
    """

    # Create a copy of the graph to avoid modifying the original
    H = G.copy()        
    i = 0 

    result_list = [] 
        
    # loop until we have the desired number of sites or not enough areas left big enough to site
    while len(result_list) < number_of_sites and H.number_of_nodes() > 0:
        try:
            # collect the node with the smallest locational cost
            min_node = min(
                (node for node, data in H.nodes(data=True) if attribute in data),
                key=lambda node: H.nodes[node][attribute]
            )
        except ValueError:
            # No nodes left
            break
    
        # Check how many connected components there are surrounding the min node
        connections = list(nx.node_connected_component(H, min_node))
        
        # if it has enough neighbors, get the connected nodes
        if len(connections) >= min_block_size:
            
            # get connected nodes up to block size for data center campus
            selected_neighbors = get_connected_nodes(H, min_node, min_block_size)

            # create a list of nodes that are now taken
            nodes_to_remove = [min_node] + selected_neighbors
    
            result_dict = {}

            # Min node info
            row, col = min_node
            x, y = rasterio.transform.xy(transform, row, col)

            # get neighbor info
            coord_list = []
            row_col_list = []
            for neighbor in selected_neighbors:
                row_n, col_n = neighbor
                x_n, y_n = rasterio.transform.xy(transform, row_n, col_n)
                coord_list.append((x_n,y_n))
                row_col_list.append((row_n, col_n))

            result_dict[i] = {
                'region_name': region_name,
                'min_node': (x,y),
                'locational_cost': H.nodes[min_node][attribute],
                'coord_list': coord_list,
                'row_col_list': row_col_list
            }
            result_list.append(result_dict)
            
            # Remove sited areas from available
            H.remove_nodes_from(nodes_to_remove)
            i+=1

        else:
            # Bad node (not enough neighbors): remove only the min_node and continue
            H.remove_node(min_node)

    return result_list