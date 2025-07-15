from tqdm import tqdm
import time
import logging
import geopandas as gpd
import pandas as pd
import click
import os
import sys
from pathlib import Path

from .load_data import load_region_raster, load_raster_array, collect_constraints, get_yaml
from .calculate_locational_cost import calculate_locational_cost
from .determine_sites import get_region_suit_array, build_graph, site_based_on_siting_score
from .calculate_gravity_score import calc_gravity_array_from_distance, calc_gravity_score
from .configure_output import configure_output
from .utils import convert_sqft_to_grid_cells, get_normalized_value


def run(config: str) -> gpd.GeoDataFrame:
    """
    Run the data center siting process based on the provided configuration file.

    Args:
        config (str): Path to the configuration file in YAML format.

    Returns:
        gpd.GeoDataFrame: A GeoDataFrame containing the siting results for all processed regions.

    This function performs the following steps:
        1. Loads configuration, region, and suitability rasters.
        2. Loads cost and constraint layers for suitable grid cells.
        3. Iterates over each region in the expansion plan:
            a. Extracts suitable siting areas for the region.
            b. Builds a graph of connected suitable areas.
            c. Calculates locational costs for each suitable grid cell.
            d. Selects sites based on minimum locational cost.
            e. Aggregates results into a GeoDataFrame.
        4. Optionally saves the output to a file if specified in the configuration.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If required configuration keys are missing.

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
    market_dict = config_dict['market_gravity']
    expansion_dict = config_dict['expansion_plan']

    # get cost and constraint layers as lists
    raster_names = list(constraint_dict.keys())
    raster_paths = list(constraint_dict.values())

    # load region array
    logger.info(f"Loading region raster from {settings_dict['region_raster_path']}")
    region_array, transform = load_region_raster(settings_dict['region_raster_path'])

    # load suitability array
    logger.info(f"Loading siting suitability raster from {settings_dict['siting_raster_path']}")
    suit_array = load_raster_array(raster_fn = settings_dict['siting_raster_path'])

    # load cost and constraint arrays in suitable grid cells
    node_values = collect_constraints(suit_array, transform, raster_paths, raster_names, logger)

    # load market size and distance to market
    market_array = load_raster_array(raster_fn = market_dict['market_raster_path'])

    logger.info(f"Calculating market gravity multipliers...")
    # get the gravity multiplier array based on distance to market and market size
    gravity_multiplier_array = calc_gravity_array_from_distance(market_array, suit_array)

    logger.info("Starting siting process...")
    output_gdf = gpd.GeoDataFrame()
    for region_name in list(expansion_dict.keys()):

        logger.info(f"Processing region: {region_name}")

        region_dict = expansion_dict[region_name]
        region_id = region_dict['region_id']
        campus_size_square_ft = region_dict['campus_size_square_ft']
        cooling_water_intensity_gal_per_mwh = region_dict.get('cooling_water_intensity_gal_per_mwh', 460)
        cooling_water_consumption_fraction = region_dict.get('cooling_water_consumption_fraction', .8)
        facility_overhead_frac = region_dict.get('facility_overhead_frac', 0)
        equipment_capex_usd = region_dict['equipment_capital_expenditure_usd']
        building_capex_usd = region_dict['building_capital_expenditure_usd']
        assessed_real_property_frac = region_dict.get('assessed_real_property_frac', .16)
        assessed_personal_property_frac = region_dict.get('assessed_personal_property_frac', .8)
        data_center_it_power_mw = region_dict['data_center_it_power_mw']
        data_center_pue = region_dict['data_center_pue']
        interconnection_cost_usd_per_km = region_dict['interconnection_cost_usd_per_km']
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
            G.nodes[node]['locational_cost'], node_parameter_dict = calculate_locational_cost(
                                campus_size_square_ft=campus_size_square_ft,
                                land_cost_usd_per_sqft=attrs['land_cost_per_sqft'],
                                elec_rate_usd_per_kwh=attrs['electricity_rate_per_kwh'],
                                personal_prop_tax_rate=attrs['personal_prop_tax_rate'],
                                real_property_tax_rate=attrs['real_property_tax_rate'],
                                sales_tax_rate=attrs['sales_tax_rate'],
                                interconnection_distance_km=attrs['interconnection_distance_km'],
                                mechanical_cool_fraction = attrs['mechanical_cool_fraction'],
                                water_cool_fraction = attrs['water_cool_fraction'],
                                equipment_capex_usd=equipment_capex_usd,
                                building_capex_usd=building_capex_usd,
                                interconnection_cost_usd_per_km=interconnection_cost_usd_per_km,
                                data_center_it_power_mw=data_center_it_power_mw,
                                data_center_pue=data_center_pue,
                                assessed_real_property_frac = assessed_real_property_frac,
                                assessed_personal_property_frac= assessed_personal_property_frac,
                                cooling_water_intensity_gal_per_mwh = cooling_water_intensity_gal_per_mwh,
                                cooling_water_consumption_fraction = cooling_water_consumption_fraction,
                                facility_overhead_frac = facility_overhead_frac
            )
            # add parameters to node attributes
            G.nodes[node]['parameters'] = node_parameter_dict

        max_locational_cost = max(data['locational_cost'] for _, data in G.nodes(data=True))
        min_locational_cost = min(data['locational_cost'] for _, data in G.nodes(data=True))

        logger.info(f"Calculating market gravity score...")
        for node, attrs in tqdm(list(G.nodes(data=True))):
    
            # calculate gravity score
            G.nodes[node]['gravity_score'] = calc_gravity_score(node, gravity_multiplier_array, data_center_it_power_mw, alpha=0.5)

        max_gravity_score = max(data['gravity_score'] for _, data in G.nodes(data=True))
        min_gravity_score = min(data['gravity_score'] for _, data in G.nodes(data=True))
        
        logger.info(f"Normalizing cost and market score...")
        for node, attrs in tqdm(list(G.nodes(data=True))):
            # get normalized locational cost
            G.nodes[node]['normalized_locational_cost'] = get_normalized_value(G, attribute='locational_cost', node=node, 
                                                                               max_value=max_locational_cost, 
                                                                               min_value=min_locational_cost)

            # get normalized gravity score
            G.nodes[node]['normalized_gravity_score'] = get_normalized_value(G, attribute='gravity_score', node=node,
                                                                               max_value=max_gravity_score,
                                                                               min_value=min_gravity_score)

            # get total weighted siting score
            norm_loc_cost = G.nodes[node]['normalized_locational_cost']
            norm_gravity_score = G.nodes[node]['normalized_gravity_score']
            cost_weight = settings_dict.get('cost_weight', 0.5)
            market_weight = settings_dict.get('market_weight', 0.5)

            G.nodes[node]['total_weighted_siting_score'] = (cost_weight * norm_loc_cost) +  (market_weight * norm_gravity_score)

        # site based on the minimum locational cost
        result_list = site_based_on_siting_score(
            G, number_of_sites, min_block_size, region_name, transform
        )

        logger.info(f"Sited {len(result_list)} data center(s) in region {region_name}.")
    
        region_gdf = configure_output(result_list, region_id)
        output_gdf = pd.concat([output_gdf, region_gdf])

    if settings_dict.get('output_file'):
        logger.info(f"Saving output to {settings_dict['output_file']}")
        output_gdf.to_file(settings_dict['output_file'])

    logger.info(f"All regions processed in {round((time.time() - t0)/60, 2)} minutes.")

    return output_gdf


@click.group()
def cli():
    """Data Center Siting Tool - Identifies optimal locations for data centers based on various constraints and costs."""
    pass


@cli.command()
@click.argument('config', type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option('-o', '--output', type=click.Path(dir_okay=False, path_type=Path),
              help='Path to save the output GeoJSON file (overrides config file setting)')
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose logging output')
@click.option('--log-file', type=click.Path(dir_okay=False, path_type=Path),
              help='Path to save the log file')
def site(config: Path, output: Path, verbose: bool, log_file: Path):
    """Run the data center siting process using the provided configuration file."""
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    if log_file:
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    else:
        logging.basicConfig(
            level=log_level,
            format=log_format
        )

    logger = logging.getLogger(__name__)

    try:
        # Run the siting process
        output_gdf = run(str(config))

        # Save output if specified via CLI
        if output:
            logger.info(f"Saving output to {output}")
            output_gdf.to_file(output)

    except Exception as e:
        logger.error(f"Error running data center siting: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
