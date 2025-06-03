import pytest
import numpy as np

from cerf_data_centers.utils import convert_sqft_to_grid_cells

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
