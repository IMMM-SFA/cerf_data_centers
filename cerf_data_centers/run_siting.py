from tqdm import tqdm
import time
import logging

from .load_data import load_region_raster, load_suitability_raster, collect_constraints, get_yaml
from .calculate_locational_cost import calculate_locational_cost
from .determine_sites import get_region_suit_array, build_graph, site_based_on_locational_cost
from .configure_output import configure_output
from .utils import convert_sqft_to_grid_cells


def run(config):
    """
    Run the siting process based on the provided configuration file.

    Parameters:
    config (str): Path to the configuration file in YAML format.

    Returns:
    output_gdf (GeoDataFrame): A GeoDataFrame containing the siting results.
    """

    t0 = time.time()
    fmt = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=fmt)
    logger = logging.getLogger(__name__)

    logger.info("Application started")

    logger.info(f"Using configuration file: {config}")
    config_dict = get_yaml(config)

    settings_dict = config_dict['settings']
    constraint_dict = config_dict['constraints']
    expansion_dict = config_dict['expansion_plan']

    # get cost and constraint layers as lists
    raster_names = list(constraint_dict.keys())
    raster_paths = list(constraint_dict.values())

    # load region array
    logger.info(f"Loading region raster from {settings_dict['region_raster_path']}")
    region_array, transform = load_region_raster(settings_dict['region_raster_path'])

    # load suitability array
    logger.info(f"Loading siting suitability raster from {settings_dict['siting_raster_path']}")
    suit_array = load_suitability_raster(settings_dict['siting_raster_path'])

    # load cost and constraint arrays in suitable grid cells
    node_values = collect_constraints(suit_array, transform, raster_paths, raster_names, logger)

    logger.info("Starting siting process...")
    output_gdf = gpd.GeoDataFrame()
    for region_name in list(expansion_dict.keys()):

        logger.info(f"Processing region: {region_name}")

        region_dict = expansion_dict[region_name]
        region_id = region_dict['region_id']
        campus_size_square_ft = region_dict['campus_size_square_ft']
        equipment_capex = region_dict['equipment_capital_expenditure']
        building_capex = region_dict['building_capital_expenditure']
        data_center_power_mw = region_dict['data_center_power_mw']
        pue = region_dict['pue']
        interconnection_cost_km = region_dict['interconnection_cost_km']
        number_of_sites = region_dict['n_sites']

        # determine the number of collected blocks
        min_block_size = convert_sqft_to_grid_cells(campus_size_square_ft)

        # get suitable siting areas for region
        logger.info(f"Extracting suitable siting areas...")
        region_suit_array = get_region_suit_array(region_array, suit_array, region_id)

        # build connected component graph of suitable areas that meet minimum size criteria
        logger.info(f"Building siting graph...")
        G = build_graph(region_suit_array, min_block_size, raster_names, node_values)
        
        # calculate locational cost in each suitable grid cell
        logger.info(f"Calculating locational costs...")
        for node, attrs in tqdm(list(G.nodes(data=True))):
            G.nodes[node]['locational_cost'], _ = calculate_locational_cost(campus_size_square_ft, 
                                                            land_cost_sqft = attrs['land_cost_per_sqft'], 
                                                            elec_rate_per_kwh = attrs['electricity_rate_per_kwh'], 
                                                            personal_prop_tax_rate = attrs['personal_prop_tax_rate'],
                                                            real_property_tax_rate = attrs['real_property_tax_rate'],
                                                            sales_tax_rate = attrs['sales_tax_rate'],
                                                            interconnection_distance_km = attrs['interconnection_distance_km'],
                                                            cooling_type = attrs['cooling_type'],
                                                            equipment_capex = equipment_capex,
                                                            building_capex = building_capex,
                                                            interconnection_cost_km = interconnection_cost_km,
                                                            data_center_power_mw = data_center_power_mw,
                                                            pue = pue,
                                                        )
                                                    
        # site based on the minimum locational cost
        result_list = site_based_on_locational_cost(G, number_of_sites, min_block_size, region_name, transform)

        logger.info(f"Sited {len(result_list)} data center(s) in region {region_name}.")
    
        region_gdf = configure_output(result_list, region_id)
        output_gdf = pd.concat([output_gdf, region_gdf])

    if settings_dict.get('output_file'):
        logger.info(f"Saving output to {settings_dict['output_file']}")
        output_gdf.to_file(settings_dict['output_file'])

    logger.info(f"All regions processed in {round((time.time() - t0)/60, 2)} minutes.")

    return output_gdf


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Run the data center siting.")
    parser.add_argument("config", type=str, help="Path to the configuration file (YAML format).")
    args = parser.parse_args()

    # Check if the config file exists
    if not os.path.isfile(args.config):
        raise FileNotFoundError(f"Configuration file {args.config} not found.")

    # Run the siting process
    output_gdf = run(args.config)
