import os
import time
import logging

import numpy as np
import rasterio
import yaml


def read_yaml(yaml_file: str) -> dict:
    """
    Read a YAML file and return its contents as a dictionary.

    Args:
        yaml_file (str): Path to the YAML file to be read.

    Returns:
        dict: Contents of the YAML file parsed into a dictionary.
    """
    with open(yaml_file, 'r') as yml:
        return yaml.load(yml, Loader=yaml.FullLoader)


def get_yaml(config_file: str) -> dict:
    """
    Read and parse a YAML configuration file.

    Args:
        config_file (str): Path to the YAML configuration file.

    Returns:
        dict: Parsed contents of the YAML file as a dictionary.

    Raises:
        AttributeError: If config_file is None.
        FileNotFoundError: If the specified config_file does not exist.
    """
    if config_file is None:
        msg = "Config file must be passed as an argument using:  config_file='<path to config.yml'>"
        raise AttributeError(msg)
    if os.path.isfile(config_file):
        return read_yaml(config_file)
    else:
        msg = f"Config file not found for path:  {config_file}."
        raise FileNotFoundError(msg)
        

def load_region_raster(siting_region_fn: str) -> tuple[np.ndarray, rasterio.Affine]:
    """
    Load the region raster from the specified file path.

    Args:
        siting_region_fn (str): Path to the siting region raster file.

    Returns:
        tuple[np.ndarray, rasterio.Affine]: 
            A tuple containing:
                - region_array (np.ndarray): The raster data as a 2D numpy array.
                - transform (rasterio.Affine): The affine transformation for the raster.
    """
    with rasterio.open(siting_region_fn) as src:
        region_array = src.read(1)
        transform = src.transform
    return region_array, transform


def load_raster_array(raster_fn: str) -> np.ndarray:
    """
    Load the raster from the specified file path.

    Args:
        raster_fn (str): Path to the raster file.

    Returns:
        np.ndarray: A 2D numpy array representing the raster.
    """
    with rasterio.open(raster_fn) as src:
        suit_array = src.read(1)
    return suit_array


def collect_constraints(
        suit_array: np.ndarray,
        transform: rasterio.Affine,
        raster_paths: list[str],
        raster_names: list[str],
        logger: logging.Logger
    ) -> dict[tuple[int, int], dict[str, float]]:
        """
        Collect and extract cost and constraint data for suitable siting locations.

        This function samples raster values for each constraint/cost layer at the locations
        where the suitability array indicates a suitable site (value == 1). The sampled
        values are stored in a dictionary keyed by (row, col) grid cell indices, with each
        value being a dictionary mapping constraint/cost names to their sampled values.

        Args:
            suit_array (np.ndarray): 2D array indicating suitable siting locations (1 = suitable).
            transform (rasterio.Affine): Affine transformation for converting array indices to coordinates.
            raster_paths (list[str]): List of file paths to cost/constraint raster files.
            raster_names (list[str]): List of names corresponding to each raster file.
            logger: Logger object for logging progress and information.

        Returns:
            dict[tuple[int, int], dict[str, float]]: 
                Dictionary mapping (row, col) indices of suitable locations to a dictionary
                of constraint/cost values for each raster name.
        """
        t0 = time.time()
        logger.info('Collecting cost and constraint data for suitable siting locations...')

        # Read in file paths and open datasets
        datasets = []
        for i, path in enumerate(raster_paths):
            logger.info(f"Loading {raster_names[i]} data from: {path}")
            datasets.append(rasterio.open(path))

        suit_rows, suit_cols = np.where(suit_array == 1)
        suitrow_suitcol = list(zip(suit_rows, suit_cols))
        xs, ys = rasterio.transform.xy(transform, suit_rows, suit_cols)
        xy_coords = list(zip(xs, ys))

        node_values: dict[tuple[int, int], dict[str, float]] = {}
        for node in suitrow_suitcol:
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

        logger.info(
            f"All cost and constraint data loaded in {round(((time.time() - t0) / 60), 2)} minutes."
        )

        return node_values
