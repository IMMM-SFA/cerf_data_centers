# CERF - Data Centers

## 1. Overview

**Purpose:**  
*An open-source geospatial Python package for assessing and analyzing future data center expansion feasibility*


## 2. Siting Algorithm

### 2.1 Computational Workflow

 **1. Load Data** - Load expansion configuration, geospatial raster of siting suitability, and locational cost layers for entire region

 **2. Create Graph Network of Suitable Subregion Areas** - For given subregion (e.g. state), create a graph network of suitable siting locations.

 **3. Calculate Locational Cost** - For each suitable grid cell in region (represented by graph node), calculate `locational cost` based on cost and constraint layers.

 **4. Determine Optimal Siting Locations** - Select suitable location with the lowest locational cost that meets minimum size criteria. Group with neighboring suitable cells up to indicated size to determine data center campus. Repeat for as many sites as indicated in configuration until either there are no more locations to site or no suitable locations remain.


### 2.2 Locational Cost Formulation


**Locational Cost (LC) to Site in Each Grid Cell**

$$LC = PC + BC + EC + PPT + RPT + ST + IC$$

Where,

| Variable | Description | Formulation |
|----------|-------------|------------------|
| PC | Property CAPEX Cost | Campus size (sqft) x Land Cost  ($/sqft) |
| BC | Building CAPEX Cost | Cost to construct building ($) |
| EC | Electricity Cost | Annual electricity demand (MWh) x Electricity Rate ($/MWh) |
| PPT | Personal Property Tax | Assessed personal property value ($) x Tax Rate (%) |
| RPT | Real Property Tax | Assessed real property value ($) x  Tax Rate (%) |
| ST | Sales Tax | Purchased Equipment and Electricity ($) x Sales Tax Rate (%) |
| IC | Interconnection Cost | Distance from POI (km) x Transmission Cost ($/km) |

Additional details:

- **Annual electricity demand (MWh)** = Data Center Power (MW) x Power Usage Effectiveness (PUE) x Operational Fraction x 8760
- **Assessed personal property value ($)** = Equipment CAPEX x Assessed Personal Property Fraction (default 80%)
- **Assessed real property value ($)** = ( Property Cost + Building CAPEX ) x  Assessed Real Property Fraction (default 16%)


## 3. Required Data Inputs

### 3.1 YAML Configuration File

`config.yml`: _YAML configuration file of number of sites by scenario and subregion, data center size, and required file paths with the following structure._

```yaml
settings:
    output_file: <path to where you'd like to store the output file in GeoPandas writeable format (e.g., shapefile)>
    region_raster_path: <path to your region raster file>
    siting_raster_path: <path to your siting suitability raster>

constraints:
    land_cost: <path to land cost raster>
    electricity_rate: <path to electricity rate raster>
    personal_prop_tax_rate: <path to personal property tax rate raster>
    real_property_tax_rate: <path to real property tax rate raster>
    sales_tax_rate: <path to sales tax rate raster>
    interconnection_distance: <path to POI distance raster>
    cooling_type: <path to cooling type raster>

expansion_plan:
    california:
        region_id: 6 
        campus_size_square_ft: 1000000
        equipment_capital_expenditure: 201600000
        building_capital_expenditure: 262200000
        interconnection_cost_km: 1000000
        data_center_power_mw: 36
        pue: 1.1
        n_sites: 10

    oregon:
        region_id: 41 
        campus_size_square_ft: 1000000
        equipment_capital_expenditure: 201600000
        building_capital_expenditure: 262200000
        interconnection_cost_km: 1000000
        data_center_power_mw: 36
        pue: 1.1
        n_sites: 3
```

The expansion plan requires the following inputs for each subregion:

| Variable | Description | Type |
|----------|-------------|------------------|
| region_id | Unique numeric ID for subregion that can be mapped to information in the `region_raster_path` | int |
| campus_size_square_ft | Total size in square feet of land required to house data center building(s). Used to determine the number of required grid cells for siting. | int |
| equipment_capital_expenditure | Cost of equipment CAPEX such as servers, mechanical and electrical systems, generators | int |
| building_capital_expenditure | Cost of data center building CAPEX ($) | int |
| interconnection_cost_km | $/km incurred to interconnect to the power system | int |
| data_center_power_mw | Storage and transaction processing capability of the data center (MW_e) | int |
| pue | Power Usage Effectiveness - The energy efficiency of data center. Measured as (total facility energy demand / IT equiment energy demand) | float |
| n_sites | Number of facilities to site in given subregion | int |

### 3.2 Geospatial Data

Geospatial rasters for spatial suitability and locational cost information must be provided at a resolution of 100m using the albers equal area conic projection (`ESRI:102003`). Input rasters can be prepared using any GIS and must all have the same spatial extent, origin, and pixel size.

#### 3.2.1 Region Raster

The `region_raster_path` indicates the spatial boundary of each subregion in the expansion plan that siting can occur within. The value of each grid cell should correspond to the region_id indicated in the configuration file.

#### 3.2.2 Siting Suitability Raster

The `siting_raster_path` indicates the composite binary suitability of siting of siting a data center in each grid cell. Values should be either 1 (suitable) or (0) unsuitable for siting.

#### 3.2.3 Locational Cost Rasters

The following raster cost/constraint layers are required. Paths to each of these files should be provided in the configuration file under the constraints section.


| Layer Config Name | Raster File | Description | Units |
|--|----------|-------------|------------------|
| `land_cost` | Land cost | Each grid cell value corresponds to property value | $/sqft |
| `electricity_rate` | Electricity rate | Each grid cell value corresponds to cost of electricity | $/kWh |
| `personal_prop_tax_rate` | Personal Property tax rate | Each grid cell value corresponds to the personal property tax | fraction |
| `real_property_tax_rate`| Real Property tax rate | Each grid cell value corresponds to the real estate property tax | fraction |
| `sales_tax_rate` | Sales tax rate | Each grid cell value corresponds to the sales tax rate on purchases of equipment | fraction |
| `interconnection_distance` | Distance to interconnection | Each grid cell value corresponds to its distance to nearest electric grid point of interconnection | km |
| `cooling_type` | Cooling type | Whether a grid cell would require mechanical (e.g., HVAC) (value=0) or water (e.g., adiabatic) (value=1) cooling technology | binary |




### Requirements

```
Python >= 3.11
```

### Dependencies

```
numpy >= 2.2.6
pandas >= 2.2.3
geopandas >= 1.1.0
rasterio >= 1.4.3
shapely >= 2.1.1
PyYAML >= 6.0.2
networkx >= 3.5
tqdm >= 4.67.1
```
