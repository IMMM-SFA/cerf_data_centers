[![tests](https://github.com/IMMM-SFA/cerf_data_centers/actions/workflows/build.yml/badge.svg)](https://github.com/IMMM-SFA/cerf_data_centers/actions/workflows/build.yml)


# CERF Data Centers

A tool for identifying optimal locations for data centers based on various constraints and costs.

## Installation

You can install the package using pip:

```bash
# Install from the repository
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

## Command Line Interface

The tool provides a command-line interface through the `cerf-siting` command. The CLI is built using Click and provides a modern, user-friendly interface.

### Basic Usage

```bash
cerf-siting site config.yaml
```

### Available Commands

- `site`: Run the data center siting process
- `--help`: Show help message and exit

### Command Line Options

For the `site` command:

- `config`: Path to the configuration file in YAML format (required)
- `-o, --output`: Path to save the output GeoJSON file (overrides config file setting)
- `-v, --verbose`: Enable verbose logging output
- `--log-file`: Path to save the log file

### Examples

```bash
# Basic usage with config file
cerf-siting site config.yaml

# Run with verbose logging
cerf-siting site config.yaml --verbose

# Run with custom output file
cerf-siting site config.yaml --output results.geojson

# Run with log file
cerf-siting site config.yaml --log-file siting.log

# Get help
cerf-siting --help
cerf-siting site --help
```

### Configuration File

The configuration file should be in YAML format and include the following sections:

- `settings`: General settings including paths to input files
- `constraints`: Cost and constraint layers
- `expansion_plan`: Data center specifications for each region

Example configuration structure:
```yaml
settings:
  region_raster_path: "path/to/region.tif"
  siting_raster_path: "path/to/suitability.tif"
  output_file: "output.geojson"  # optional

constraints:
  land_cost_per_sqft: "path/to/land_cost.tif"
  electricity_rate_per_kwh: "path/to/electricity.tif"
  # ... other constraint layers

expansion_plan:
  region_name:
    region_id: 1
    campus_size_square_ft: 1000000
    equipment_capital_expenditure: 1000000
    building_capital_expenditure: 500000
    data_center_power_mw: 10
    pue: 1.5
    interconnection_cost_km: 1000
    n_sites: 1
```

## Python API

You can also use the tool programmatically:

```python
from cerf_data_centers.run_siting import run

# Run the siting process
output_gdf = run("config.yaml")
```

## Development

To set up the development environment:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
```

## Requirements

- Python >= 3.7
- Dependencies:
  - tqdm >= 4.65.0
  - geopandas >= 0.13.0
  - pandas >= 1.5.0
  - pyyaml >= 6.0
  - click >= 8.0.0
  - numpy >= 1.20.0
  - rasterio >= 1.3.0
  - shapely >= 2.0.0
  - networkx >= 3.0.0
