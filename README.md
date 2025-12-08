[![tests](https://github.com/IMMM-SFA/cerf_data_centers/actions/workflows/build.yml/badge.svg)](https://github.com/IMMM-SFA/cerf_data_centers/actions/workflows/build.yml)


# CERF Data Centers

A comprehensive tool for identifying optimal locations for data centers based on a combination of geospatial, economic, and infrastructure constraints and costs.

## What Does This Program Do?

**CERF Data Centers** is designed to help project feasible locations to build new data centers. It does this by:

- **Integrating geospatial data**: Uses raster files representing land cost, electricity rates, property taxes, and other constraints across a region.
- **Applying user-defined constraints**: Allows you to specify which factors are most important (e.g., land cost, energy cost, proximity to infrastructure).
- **Calculating locational costs**: For each potential site, the tool computes a total cost that includes land, building and equipemnt capex, energy, taxes, and interconnection.
- **Siting algorithm**: Finds clusters of suitable grid cells that meet the minimum size and constraint requirements for a data center campus.
- **Market gravity scoring**: Optionally incorporates market size and distance to market to prioritize sites with better access to demand.
- **Flexible configuration**: All inputs and parameters are specified in a YAML configuration file, making it easy to adapt to different regions or scenarios.
- **Output**: Produces a GeoDataFrame (and optionally a GeoJSON file) with the selected sites, their costs, and relevant attributes for further analysis or mapping.

### Typical Workflow
1. **Prepare input rasters**: Gather or generate raster files for all relevant constraints (land cost, electricity, taxes, etc.) and a region raster.
2. **Write a configuration file**: Specify the paths to your input files, the constraints to consider, and the data center requirements for each region.
3. **Run the tool**: Use the CLI or Python API to process the data and identify optimal sites.
4. **Review results**: Analyze the output GeoDataFrame or GeoJSON to see the recommended sites, their costs, and other attributes.

---

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

## How to Cite

If you use this package in your research, please cite:

```
Mongird, K., & Vernon, C. R. (2025). CERF-DC: A Python package to evaluate the feasibility and costs of data center siting options. Zenodo. https://doi.org/10.5281/zenodo.17859233
```