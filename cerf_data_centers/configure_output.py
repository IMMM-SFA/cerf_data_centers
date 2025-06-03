from typing import List, Dict, Any

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


def configure_output(
    result_list: List[Dict[int, Dict[str, Any]]],
    region_id: int
) -> gpd.GeoDataFrame:
    """
    Configure the siting results into a GeoDataFrame with buffered geometries.

    Args:
        result_list (List[Dict[int, Dict[str, Any]]]): 
            A list where each element is a dictionary keyed by an integer, 
            containing siting results for each region. Each siting result 
            dictionary should have the keys 'coord_list', 'locational_cost', 
            and 'region_name'.
        region_id (int): 
            The ID of the region for which to configure the output.

    Returns:
        gpd.GeoDataFrame: 
            A GeoDataFrame containing the siting results, including 
            coordinates, region name, cost, and buffered geometries 
            dissolved by data center ID.
    """
    i_list, x_list, y_list, lc_list, r_list = [], [], [], [], []
    for i in range(len(result_list)):
        c = result_list[i][i]['coord_list']
        n = result_list[i][i]['locational_cost']
        r = result_list[i][i]['region_name']
        for j in c:
            i_list.append(str(region_id) + "_" + str(i))
            x_list.append(j[0])
            y_list.append(j[1])
            r_list.append(r)
            lc_list.append(n)

    data = {
        'id': i_list,
        'region': r_list,
        'xcoord': x_list,
        'ycoord': y_list,
        'cost': lc_list
    }
    df = pd.DataFrame.from_dict(data)

    geometry = [Point(xy) for xy in zip(df['xcoord'], df['ycoord'])]
    gdf = gpd.GeoDataFrame(df, crs='ESRI:102003', geometry=geometry)

    gdf['geometry'] = gdf['geometry'].buffer(50, cap_style=3)
    gdf = gdf.dissolve(by='id', as_index=False)

    return gdf
