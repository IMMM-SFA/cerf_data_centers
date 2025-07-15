import pytest
import numpy as np
import networkx as nx
from affine import Affine

from cerf_data_centers import determine_sites


def test_get_region_suit_array_basic():
    region_array = np.array([[1, 2], [1, 2]])
    suit_array = np.array([[0.5, 0.8], [0.2, 0.9]])
    region_id = 1
    result = determine_sites.get_region_suit_array(region_array, suit_array, region_id)
    expected = np.array([[0.5, 0.0], [0.2, 0.0]])
    np.testing.assert_array_equal(result, expected)

def test_get_region_suit_array_invalid_region():
    region_array = np.array([[1, 2], [1, 2]])
    suit_array = np.array([[0.5, 0.8], [0.2, 0.9]])
    region_id = 3
    with pytest.raises(ValueError):
        determine_sites.get_region_suit_array(region_array, suit_array, region_id)

def test_get_connected_nodes_success():
    G = nx.Graph()
    G.add_edges_from([(1,2), (2,3), (3,4)])
    result = determine_sites.get_connected_nodes(G, 2, 3)
    assert set(result) == {2, 1, 3} or set(result) == {2, 3, 4}

def test_get_connected_nodes_not_enough():
    G = nx.Graph()
    G.add_edges_from([(1,2)])
    with pytest.raises(ValueError):
        determine_sites.get_connected_nodes(G, 1, 3)

def test_get_connected_nodes_start_node_not_in_graph():
    G = nx.Graph()
    G.add_edges_from([(1,2)])
    with pytest.raises(ValueError):
        determine_sites.get_connected_nodes(G, 99, 1)

def test_build_graph_and_node_attributes():
    arr = np.array([
        [0, 1, 1],
        [1, 1, 0],
        [0, 1, 1]
    ])
    min_block_size = 2
    raster_names = ['foo', 'bar']
    # All 1s are suitable, assign dummy values
    node_values = {}
    for row in range(arr.shape[0]):
        for col in range(arr.shape[1]):
            if arr[row, col] == 1:
                node_values[(row, col)] = {'foo': row+col, 'bar': row-col}
    G = determine_sites.build_graph(arr, min_block_size, raster_names, node_values)
    # All nodes in G should have foo and bar attributes
    for node in G.nodes:
        assert 'foo' in G.nodes[node]
        assert 'bar' in G.nodes[node]
    # No component should be smaller than min_block_size
    for component in nx.connected_components(G):
        assert len(component) >= min_block_size

def test_site_based_on_locational_cost_simple():
    # Build a simple graph with all required attributes
    G = nx.Graph()
    G.add_node((0,0), 
               locational_cost=1.0,
               total_weighted_siting_score=1.0,
               normalized_locational_cost=0.5,
               normalized_gravity_score=0.6,
               parameters={'test_param': 1.0})
    G.add_node((0,1), 
               locational_cost=2.0,
               total_weighted_siting_score=2.0,
               normalized_locational_cost=0.7,
               normalized_gravity_score=0.8,
               parameters={'test_param': 2.0})
    G.add_node((1,0), 
               locational_cost=3.0,
               total_weighted_siting_score=3.0,
               normalized_locational_cost=0.9,
               normalized_gravity_score=1.0,
               parameters={'test_param': 3.0})
    G.add_edge((0,0), (0,1))
    G.add_edge((0,0), (1,0))
    # All nodes are connected, min_block_size=2
    transform = Affine.translation(100, 200) * Affine.scale(10, -10)
    result = determine_sites.site_based_on_siting_score(
        G, number_of_sites=1, min_block_size=2, region_name="TestRegion", transform=transform
    )
    assert isinstance(result, list)
    assert len(result) == 1
    info = result[0][0]
    assert 'locational_cost' in info
    assert 'coord_list' in info

def test_site_based_on_locational_cost_not_enough_neighbors():
    # Only one node, min_block_size=2, should skip and return empty
    G = nx.Graph()
    G.add_node((0,0), 
               locational_cost=1.0,
               total_weighted_siting_score=1.0,
               normalized_locational_cost=0.5,
               normalized_gravity_score=0.6,
               parameters={'test_param': 1.0})
    transform = Affine.identity()
    result = determine_sites.site_based_on_siting_score(
        G, number_of_sites=1, min_block_size=2, region_name="TestRegion", transform=transform
    )
    assert isinstance(result, list)
    assert len(result) == 0

def test_site_based_on_locational_cost_multiple_sites():
    # Build a graph with two separate clusters
    G = nx.Graph()
    # First cluster
    G.add_node((0,0), 
               locational_cost=1.0,
               total_weighted_siting_score=1.0,
               normalized_locational_cost=0.5,
               normalized_gravity_score=0.6,
               parameters={'test_param': 1.0})
    G.add_node((0,1), 
               locational_cost=2.0,
               total_weighted_siting_score=2.0,
               normalized_locational_cost=0.7,
               normalized_gravity_score=0.8,
               parameters={'test_param': 2.0})
    G.add_edge((0,0), (0,1))
    # Second cluster
    G.add_node((2,2), 
               locational_cost=0.5,
               total_weighted_siting_score=0.5,
               normalized_locational_cost=0.3,
               normalized_gravity_score=0.4,
               parameters={'test_param': 0.5})
    G.add_node((2,3), 
               locational_cost=0.7,
               total_weighted_siting_score=0.7,
               normalized_locational_cost=0.4,
               normalized_gravity_score=0.5,
               parameters={'test_param': 0.7})
    G.add_edge((2,2), (2,3))
    transform = Affine.identity()
    result = determine_sites.site_based_on_siting_score(
        G, number_of_sites=2, min_block_size=2, region_name="TestRegion", transform=transform
    )
    assert isinstance(result, list)
    assert len(result) == 2
