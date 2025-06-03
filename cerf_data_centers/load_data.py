import numpy as np
import rasterio
import yaml
import time

import os


def read_yaml(yaml_file):
    """Read a YAML file."""
    with open(yaml_file, 'r') as yml:
        return yaml.load(yml, Loader=yaml.FullLoader)


def get_yaml(config_file):
    """Read the YAML config file.
    """

    # if config file not passed
    if config_file is None:
        msg = "Config file must be passed as an argument using:  config_file='<path to config.yml'>"
        raise AttributeError(msg)
    # check for path exists
    if os.path.isfile(config_file):
        return read_yaml(config_file)
    else:
        msg = f"""Config file not found for path:  {config_file}. """
        raise FileNotFoundError(msg)
        

def load_region_raster(siting_region_fn):
    """
    Load the region array from the given file path.

    Parameters:
    siting_region_fn (str): File path to the siting region

    Returns:
    tuple: A tuple containing the siting array, transform, crs, width, and height
    """

    with rasterio.open(siting_region_fn) as src:
        region_array = src.read(1)
        transform = src.transform
    return region_array, transform


def load_suitability_raster(suitability_fn):
    """
    Load the suitability raster from the given file path.
    
    Parameters:
    suitability_fn (str): File path to the suitability raster

    Returns:
    np.array: A numpy array representing the suitability raster
    """
    with rasterio.open(suitability_fn) as src:
        suit_array = src.read(1)
    return suit_array


def collect_constraints(suit_array, transform, raster_paths, raster_names, logger):
    """
    Collects and extracts cost data for available siting locations based on suitability criteria.

    Args:
    suit_array (np.array): suitability array.
    transform (Affine): Affine transformation to convert pixel coordinates to geographic coordinates.
    raster_paths (list): List of filepaths to cost raster files.
    raster_names (list): List of names corresponding to each cost raster file.

    Returns:
    dict: A dictionary containing cost values for each available siting location.
    """

    t0 = time.time()
    logger.info('Collecting cost and constraint data for suitable siting locations...')

    # read in file paths and open datasets
    datasets = []
    for i, path in enumerate(raster_paths):
        logger.info(f"Loading {raster_names[i]} data from: {path}")
        datasets.append(rasterio.open(path))
                        
    suit_rows, suit_cols = np.where(suit_array==1)
    suitrow_suitcol = list(zip(suit_rows, suit_cols))
    xs, ys = rasterio.transform.xy(transform, suit_rows, suit_cols)
    xy_coords = list(zip(xs, ys))

    node_values = {}
    for i, node in enumerate(suitrow_suitcol):
        node_values[node] = {}

    # For each raster, sample and assign values directly to nodes
    for ds, name in zip(datasets, raster_names):

        logger.info(f"Sampling data for {name}")

        sampled = list(ds.sample(xy_coords))
        for val, node in zip(sampled, suitrow_suitcol):
            node_values[node][name] = val[0]
    
    # Close datasets
    for ds in datasets:
        ds.close()

    logger.info(f"All cost and constraint data loaded in {round((((time.time() - t0))/60), 2)} minutes.")

    return node_values
