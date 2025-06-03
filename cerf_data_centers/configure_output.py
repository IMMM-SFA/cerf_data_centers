import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
        
        
def configure_output(result_list, region_id):
    """
    Configure the output of the siting results into a GeoDataFrame.

    Parameters:
        result_list (list): A list of dictionaries containing siting results for each region.
        region_id (int): The ID of the region for which to configure the output.

    Returns:
        gdf (GeoDataFrame): A GeoDataFrame containing the siting results with coordinates and costs.
    """

    # format siting output
    i_list, x_list, y_list, lc_list, r_list = [],[],[],[],[]
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
    
    # organize data into a dataframe
    data = {'id': i_list, 'region': r_list, 'xcoord': x_list, 'ycoord':y_list, 'cost':lc_list}
    df = pd.DataFrame.from_dict(data)
    
    # convert to a geodataframe
    geometry = [Point(xy) for xy in zip(df['xcoord'], df['ycoord'])]
    gdf = gpd.GeoDataFrame(df, crs='ESRI:102003', geometry=geometry)

    # buffer point geometries to create square polygons
    gdf['geometry'] = gdf['geometry'].buffer(50, cap_style=3)

    # dissolve grid cell polygons by data center ID
    gdf = gdf.dissolve(by='id', as_index=False)

    return gdf