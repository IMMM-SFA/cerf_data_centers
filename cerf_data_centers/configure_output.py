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
    i_list, x_list, y_list, lc_list, r_list, cs_list, ex_list, bx_list = [], [], [], [], [], [], [], []
    it_list, put_list, mcf_list,wcf_list, mec_list, mgy_list, mgyc_list, ekwh_list, ppt_list = [], [], [], [], [],[], [], [], []
    rpt_list, st_list, ikm_list, pc_list, ec_list, tpt_list, tst_list, ic_list = [], [], [], [], [], [], [], []
    ngs_list, nlc_list, wss_list = [], [], []

    for i in range(len(result_list)):
        c = result_list[i][i]['coord_list']
        n = result_list[i][i]['locational_cost']
        r = result_list[i][i]['region_name']
        cs = result_list[i][i]['campus_size_square_ft']
        ex = result_list[i][i]['equipment_capex']
        bx = result_list[i][i]['building_capex']
        it = result_list[i][i]['it_power_mw']
        put = result_list[i][i]['pue']
        mcf = result_list[i][i]['mechanical_cooling_frac']
        wcf = result_list[i][i]['water_cooling_frac']
        mec = result_list[i][i]['cooling_energy_demand_mwh']
        mgy = result_list[i][i]['cooling_water_demand_mgy']
        mgyc = result_list[i][i]['cooling_water_consumption_mgy']
        ekwh = result_list[i][i]['elec_rate_per_kwh']
        ppt = result_list[i][i]['personal_prop_tax_rate']
        rpt = result_list[i][i]['real_property_tax_rate']
        st = result_list[i][i]['sales_tax_rate']
        ikm = result_list[i][i]['interconnection_distance_km']
        pc = result_list[i][i]['property_cost_usd']
        ec = result_list[i][i]['electricity_cost_usd']
        tpt = result_list[i][i]['total_property_tax_usd']
        tst = result_list[i][i]['total_sales_tax_usd']
        ic = result_list[i][i]['interconnection_cost_usd']
        ngs = result_list[i][i]['normalized_gravity_score']
        nlc = result_list[i][i]['normalized_locational_cost']
        wss = result_list[i][i]['weighted_siting_score']

        for j in c:
            i_list.append(str(region_id) + "_" + str(i))
            x_list.append(j[0])
            y_list.append(j[1])
            r_list.append(r)
            lc_list.append(n)
            cs_list.append(cs)
            ex_list.append(ex)
            bx_list.append(bx)
            it_list.append(it)
            put_list.append(put)
            mcf_list.append(mcf)
            wcf_list.append(wcf)
            mec_list.append(mec)
            mgy_list.append(mgy)
            mgyc_list.append(mgyc)
            ekwh_list.append(ekwh)
            ppt_list.append(ppt)
            rpt_list.append(rpt)
            st_list.append(st)
            ikm_list.append(ikm)
            pc_list.append(pc)
            ec_list.append(ec)
            tpt_list.append(tpt)
            tst_list.append(tst)
            ic_list.append(ic)
            ngs_list.append(ngs)
            nlc_list.append(nlc)
            wss_list.append(wss)

    data = {
        'id': i_list,
        'region': r_list,
        'xcoord': x_list,
        'ycoord': y_list,
        'cost': lc_list,
        'campus_size_square_ft': cs_list,
        'equipment_capex': ex_list,
        'building_capex': bx_list,
        'data_center_it_power_mw': it_list,
        'data_center_pue': put_list,
        'mechanical_cooling_frac': mcf_list,
        'water_cooling_frac': wcf_list,
        'cooling_energy_demand_mwh': mec_list,
        'cooling_water_demand_mgy': mgy_list,
        'cooling_water_consumption_mgy': mgyc_list,
        'electricity_cost_per_kwh': ekwh_list,
        'personal_prop_tax_rate': ppt_list,
        'real_property_tax_rate': rpt_list,
        'sales_tax_rate': st_list,
        'interconnection_distance_km': ikm_list,
        'property_cost_usd': pc_list,
        'electricity_cost_usd': ec_list,
        'total_property_tax_usd': tpt_list,
        'total_sales_tax_usd': tst_list,
        'interconnection_cost_usd': ic_list,
        'normalized_gravity_score': ngs_list,
        'normalized_locational_cost': nlc_list,
        'weighted_siting_score': wss_list

    }
    df = pd.DataFrame.from_dict(data)

    geometry = [Point(xy) for xy in zip(df['xcoord'], df['ycoord'])]
    gdf = gpd.GeoDataFrame(df, crs='ESRI:102003', geometry=geometry)

    gdf['geometry'] = gdf['geometry'].buffer(50, cap_style=3)
    gdf = gdf.dissolve(by='id', as_index=False)

    return gdf
