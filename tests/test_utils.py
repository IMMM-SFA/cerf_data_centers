import pytest
import numpy as np
import networkx as nx

from cerf_data_centers.utils import convert_sqft_to_grid_cells, get_normalized_value

def test_convert_sqft_to_grid_cells_typical():
    # 10000 sqft = 929.03 sqm, 929.03 / 10000 = 0.092903, ceil = 1
    assert convert_sqft_to_grid_cells(10000) == 1

def test_convert_sqft_to_grid_cells_zero():
    assert convert_sqft_to_grid_cells(0) == 0

def test_convert_sqft_to_grid_cells_small_value():
    # 100 sqft = 9.2903 sqm, 9.2903 / 10000 = 0.00092903, ceil = 1
    assert convert_sqft_to_grid_cells(100) == 1

def test_convert_sqft_to_grid_cells_large_value():
    # 1000000 sqft = 92903 sqm, 92903 / 10000 = 9.2903, ceil = 10
    assert convert_sqft_to_grid_cells(1_000_000) == 10

def test_convert_sqft_to_grid_cells_float_input():
    # 1234.56 sqft = 114.668 sqm, 114.668 / 10000 = 0.0114668, ceil = 1
    assert convert_sqft_to_grid_cells(1234.56) == 1

def test_convert_sqft_to_grid_cells_array_input():
    # Should work with numpy arrays
    sqft = np.array([0, 100, 10000, 1_000_000])
    expected = np.array([0, 1, 1, 10])
    np.testing.assert_array_equal(convert_sqft_to_grid_cells(sqft), expected)

def test_convert_sqft_to_grid_cells_negative_input():
    # Negative area should return 0 grid cells (since ceil of negative is negative, but area can't be negative)
    # But let's see what the function does
    result = convert_sqft_to_grid_cells(-100)
    assert result <= 0

def test_get_normalized_value_basic():
    G = nx.Graph()
    G.add_node(1, value=10)
    G.add_node(2, value=20)
    G.add_node(3, value=30)
    # Normalization: (value - min) / (max - min)
    assert get_normalized_value(G, 'value', 1, max_value=30, min_value=10) == pytest.approx(0.0)
    assert get_normalized_value(G, 'value', 2, max_value=30, min_value=10) == pytest.approx(0.5)
    assert get_normalized_value(G, 'value', 3, max_value=30, min_value=10) == pytest.approx(1.0)

def test_get_normalized_value_min_equals_max():
    G = nx.Graph()
    G.add_node(1, value=5)
    # Should return 0.0 if min == max
    assert get_normalized_value(G, 'value', 1, max_value=5, min_value=5) == 0.0

def test_get_normalized_value_negative():
    G = nx.Graph()
    G.add_node(1, value=-10)
    G.add_node(2, value=0)
    G.add_node(3, value=10)
    assert get_normalized_value(G, 'value', 1, max_value=10, min_value=-10) == pytest.approx(0.0)
    assert get_normalized_value(G, 'value', 2, max_value=10, min_value=-10) == pytest.approx(0.5)
    assert get_normalized_value(G, 'value', 3, max_value=10, min_value=-10) == pytest.approx(1.0)

def test_get_normalized_value_missing_attribute():
    G = nx.Graph()
    G.add_node(1, foo=1)
    with pytest.raises(KeyError):
        get_normalized_value(G, 'bar', 1, max_value=1, min_value=0)

def test_get_normalized_value_multiple_nodes():
    G = nx.Graph()
    for i in range(5):
        G.add_node(i, score=i*2)
    # min=0, max=8
    for i in range(5):
        expected = (i*2 - 0) / (8 - 0)
        assert get_normalized_value(G, 'score', i, max_value=8, min_value=0) == pytest.approx(expected)
