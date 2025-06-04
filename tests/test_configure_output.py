import pytest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, Point

from cerf_data_centers.configure_output import configure_output

@pytest.fixture
def sample_result_list():
    # Simulate two data centers in region 42
    return [
        {
            0: {
                'coord_list': [(100, 200), (110, 210), (120, 220)],
                'locational_cost': 5.5,
                'region_name': 'TestRegion'
            }
        },
        {
            1: {
                'coord_list': [(200, 300), (210, 310)],
                'locational_cost': 7.2,
                'region_name': 'TestRegion'
            }
        }
    ]

def test_configure_output_returns_geodataframe(sample_result_list):
    region_id = 42
    gdf = configure_output(sample_result_list, region_id)
    assert isinstance(gdf, gpd.GeoDataFrame)
    # Should have two rows, one for each data center
    assert len(gdf) == 2

def test_configure_output_columns(sample_result_list):
    region_id = 42
    gdf = configure_output(sample_result_list, region_id)
    expected_columns = {'id', 'region', 'xcoord', 'ycoord', 'cost', 'geometry'}
    assert expected_columns.issubset(set(gdf.columns))

def test_configure_output_id_and_region(sample_result_list):
    region_id = 42
    gdf = configure_output(sample_result_list, region_id)
    # IDs should be '42_0' and '42_1'
    assert set(gdf['id']) == {'42_0', '42_1'}
    # Region should be 'TestRegion'
    assert all(gdf['region'] == 'TestRegion')

def test_configure_output_costs(sample_result_list):
    region_id = 42
    gdf = configure_output(sample_result_list, region_id)
    # Costs should match those in the input
    costs = set(gdf['cost'])
    assert 5.5 in costs
    assert 7.2 in costs

def test_configure_output_geometry_is_polygon(sample_result_list):
    region_id = 42
    gdf = configure_output(sample_result_list, region_id)
    # After dissolve, geometry should be Polygon or MultiPolygon
    for geom in gdf['geometry']:
        assert geom.geom_type in ('Polygon', 'MultiPolygon')

def test_configure_output_crs(sample_result_list):
    region_id = 42
    gdf = configure_output(sample_result_list, region_id)
    # CRS should be ESRI:102003
    assert gdf.crs.to_string() == 'ESRI:102003'

def test_configure_output_empty_result():
    # If result_list is empty, should return empty GeoDataFrame
    gdf = configure_output([], 99)
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert len(gdf) == 0

def test_configure_output_single_point():
    # Test with a single data center, single point
    result_list = [
        {
            0: {
                'coord_list': [(1, 2)],
                'locational_cost': 1.1,
                'region_name': 'SingleRegion'
            }
        }
    ]
    gdf = configure_output(result_list, 7)
    assert len(gdf) == 1
    assert gdf.iloc[0]['id'] == '7_0'
    assert gdf.iloc[0]['region'] == 'SingleRegion'
    assert gdf.iloc[0]['cost'] == 1.1
    assert gdf.iloc[0]['geometry'].geom_type in ('Polygon', 'MultiPolygon')
