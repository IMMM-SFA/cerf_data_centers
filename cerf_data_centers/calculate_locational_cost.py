from typing import Dict, Tuple


def calculate_locational_cost(
    campus_size_square_ft: float,
    land_cost_usd_per_sqft: float,
    elec_rate_usd_per_kwh: float,
    personal_prop_tax_rate: float,
    real_property_tax_rate: float,
    sales_tax_rate: float,
    interconnection_distance_km: float,
    equipment_capex_usd: float,
    building_capex_usd: float,
    interconnection_cost_usd_per_km: float,
    data_center_it_power_mw: float,
    data_center_pue: float,
    assessed_real_property_frac: float = 0.16,
    assessed_personal_property_frac: float = 0.80,
    mechanical_cool_fraction = .5,
    water_cool_fraction = .5,
    cooling_water_intensity_gal_per_mwh = 460,
    cooling_water_consumption_fraction = .8,
    facility_overhead_frac = 0
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate the locational cost for a data center campus based on various parameters.

    Args:
        campus_size_square_ft (float): Size of the campus in square feet.
        land_cost_usd_per_sqft (float): Cost of land per square foot.
        elec_rate_usd_per_kwh (float): Electricity rate in $/kWh.
        personal_prop_tax_rate (float): Personal property tax rate (as a decimal, e.g., 0.01 for 1%).
        real_property_tax_rate (float): Real property tax rate (as a decimal).
        sales_tax_rate (float): Sales tax rate (as a decimal).
        interconnection_distance_km (float): Distance to interconnection in kilometers.
        equipment_capex_usd (float): Capital expenditure for equipment in dollars.
        building_capex_usd (float): Capital expenditure for building in dollars.
        interconnection_cost_usd_per_km (float): Cost per kilometer for interconnection in dollars.
        data_center_it_power_mw (float): Power capacity of the data center IT in megawatts (MW).
        data_center_pue (float): Power Usage Effectiveness of the data center.
        assessed_real_property_frac (float, optional): Fraction of real property assessed for tax. Defaults to 0.16.
        assessed_personal_property_frac (float, optional): Fraction of personal property assessed for tax. Defaults to 0.80.
        mechanical_cool_fraction (float, optional): Fraction of year that mechanical cooling is used. Defaults to 0.5.
        water_cool_fraction (float, optional): Fraction of year that water cooling is used. Defaults to 0.5.
        cooling_water_intensity_gal_per_mwh (float, optional): Water intensity for cooling in gallons per MWh. Defaults to 475.
        cooling_water_consumption_fraction (float, optional): Fraction of cooling water consumed. Defaults to 0.8.
        facility_overhead_frac (float, optional): Fraction of overhead energy demand (non-IT demand) for the facility that does not go towards cooling. Defaults to 0.

    Returns:
        Tuple[float, Dict[str, float]]: 
            - Total locational cost in dollars.
            - Dictionary of individual parameters and cost components, including:
              'campus_size_square_ft', 'equipment_capex', 'building_capex', 'it_power_mw',
                'pue', 'mechanical_cooling_frac', 'water_cooling_frac',
                'cooling_energy_demand_mwh', 'cooling_water_demand_mgy', 'cooling_water_consumption_mgy',
                'elec_rate_per_kwh', 'personal_prop_tax_rate', 'real_property_tax_rate',
                'sales_tax_rate', 'interconnection_distance_km',
                'property_cost_usd', 'electricity_cost_usd', 'total_property_tax_usd',
                'total_sales_tax_usd', 'interconnection_cost_usd'.
    """
    HOURS_PER_YEAR = 8760
    MWH_TO_KWH = 1000

    # energy demand for IT load
    it_energy_demand_mwh = data_center_it_power_mw * HOURS_PER_YEAR

    # energy demand for entire facility (IT load + cooling)
    total_facility_energy_demand_mwh = it_energy_demand_mwh * data_center_pue

    # overhead energy demand (cooling, lighting, etc.)
    overhead_energy_demand_mwh = total_facility_energy_demand_mwh - it_energy_demand_mwh

    # facility overhead energy demand (lighting, fans, etc.)
    facility_overhead_energy_demand_mwh = overhead_energy_demand_mwh * facility_overhead_frac

    # IT cooling energy demand 
    cooling_energy_demand_mwh = overhead_energy_demand_mwh - facility_overhead_energy_demand_mwh

    # Calculate energy demand for different cooling types
    mechanical_cooling_energy_mwh = mechanical_cool_fraction * cooling_energy_demand_mwh
    water_cooling_energy_mwh = water_cool_fraction * cooling_energy_demand_mwh

    # Calculate total water demand and consumption for cooling
    cooling_water_demand_mgy = (water_cooling_energy_mwh * cooling_water_intensity_gal_per_mwh) / 1e6
    cooling_water_consumption_mgy = cooling_water_demand_mgy * cooling_water_consumption_fraction 

    # Calculate total electricity demand for the facility (including IT, IT cooling, and facility overhead)
    total_electricity_demand_mwh = it_energy_demand_mwh + mechanical_cooling_energy_mwh + facility_overhead_energy_demand_mwh

    # Electricity cost
    electricity_cost_usd = (total_electricity_demand_mwh * MWH_TO_KWH) * elec_rate_usd_per_kwh

    # Property cost
    property_cost_usd = campus_size_square_ft * land_cost_usd_per_sqft
    land_building_cost_usd = property_cost_usd + building_capex_usd

    # Property taxes
    real_property_taxes_usd = land_building_cost_usd * assessed_real_property_frac * real_property_tax_rate
    personal_property_taxes_usd = (equipment_capex_usd * assessed_personal_property_frac) * personal_prop_tax_rate
    total_property_tax_usd = real_property_taxes_usd + personal_property_taxes_usd

    # Sales taxes
    equipment_sales_tax_usd = equipment_capex_usd * sales_tax_rate
    energy_sales_tax_usd = electricity_cost_usd * sales_tax_rate
    total_sales_tax_usd = equipment_sales_tax_usd + energy_sales_tax_usd

    # Interconnection costs
    interconnection_cost_usd = interconnection_distance_km * interconnection_cost_usd_per_km

    # Total cost
    total_cost_usd = [
        land_building_cost_usd +
        equipment_capex_usd +
        electricity_cost_usd +
        total_property_tax_usd +
        total_sales_tax_usd +
        interconnection_cost_usd
    ]

    parameter_dict: Dict[str, float] = {
        'campus_size_square_ft': campus_size_square_ft,
        'equipment_capex': equipment_capex_usd,
        'building_capex': building_capex_usd,
        'it_power_mw': data_center_it_power_mw,
        'pue': data_center_pue,
        'mechanical_cooling_frac': mechanical_cool_fraction,
        'water_cooling_frac': water_cool_fraction,

        'cooling_energy_demand_mwh': mechanical_cooling_energy_mwh,
        'cooling_water_demand_mgy': cooling_water_demand_mgy,
        'cooling_water_consumption_mgy': cooling_water_consumption_mgy,
        
        'elec_rate_per_kwh': elec_rate_usd_per_kwh,
        'personal_prop_tax_rate': personal_prop_tax_rate,
        'real_property_tax_rate': real_property_tax_rate,
        'sales_tax_rate': sales_tax_rate,
        'interconnection_distance_km': interconnection_distance_km,
        
        'property_cost_usd': property_cost_usd,
        'electricity_cost_usd': electricity_cost_usd,
        'total_property_tax_usd': total_property_tax_usd,
        'total_sales_tax_usd': total_sales_tax_usd,
        'interconnection_cost_usd': interconnection_cost_usd,
    }

    return sum(total_cost_usd), parameter_dict
