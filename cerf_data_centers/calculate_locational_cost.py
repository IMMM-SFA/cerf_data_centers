from typing import Dict, Tuple


def calculate_locational_cost(
    campus_size_square_ft: float,
    land_cost_sqft: float,
    elec_rate_per_kwh: float,
    personal_prop_tax_rate: float,
    real_property_tax_rate: float,
    sales_tax_rate: float,
    interconnection_distance_km: float,
    cooling_type: int,
    equipment_capex: float,
    building_capex: float,
    interconnection_cost_km: float,
    data_center_power_mw: float,
    pue: float,
    operational_frac: float = 1,
    assessed_real_property_frac: float = 0.16,
    assessed_personal_property_frac: float = 0.80,
    air_cooling_multiplier: float = 1.25
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate the locational cost for a data center campus based on various parameters.

    Args:
        campus_size_square_ft (float): Size of the campus in square feet.
        land_cost_sqft (float): Cost of land per square foot.
        elec_rate_per_kwh (float): Electricity rate in $/kWh.
        personal_prop_tax_rate (float): Personal property tax rate (as a decimal, e.g., 0.01 for 1%).
        real_property_tax_rate (float): Real property tax rate (as a decimal).
        sales_tax_rate (float): Sales tax rate (as a decimal).
        interconnection_distance_km (float): Distance to interconnection in kilometers.
        cooling_type (int): Type of cooling system (0 for mechanical, 1 for other).
        equipment_capex (float): Capital expenditure for equipment in dollars.
        building_capex (float): Capital expenditure for building in dollars.
        interconnection_cost_km (float): Cost per kilometer for interconnection in dollars.
        data_center_power_mw (float): Power capacity of the data center in megawatts (MW).
        pue (float): Power Usage Effectiveness of the data center.
        operational_frac (float, optional): Fraction of the year the data center is operational. Defaults to 1.
        assessed_real_property_frac (float, optional): Fraction of real property assessed for tax. Defaults to 0.16.
        assessed_personal_property_frac (float, optional): Fraction of personal property assessed for tax. Defaults to 0.80.
        air_cooling_multiplier (float, optional): Multiplier for mechanical cooling. Defaults to 1.25.

    Returns:
        Tuple[float, Dict[str, float]]: 
            - Total locational cost in millions of dollars (rounded to two decimals).
            - Dictionary of individual cost components, including:
                'property_cost', 'building_cost', 'energy_cost', 
                'total_property_tax', 'total_sales_tax', 'interconnection_cost'.
    """
    HOURS_PER_YEAR = 8760
    MWH_TO_KWH = 1000

    # Calculate facility power capacity
    if cooling_type == 0:  # mechanical cooling
        facility_power_cap_mw = (data_center_power_mw * pue) * air_cooling_multiplier
    else:
        facility_power_cap_mw = (data_center_power_mw * pue)

    # Calculate total electricity demand
    total_mwh_per_year = facility_power_cap_mw * (operational_frac * HOURS_PER_YEAR)

    # Energy cost
    energy_cost = (total_mwh_per_year * MWH_TO_KWH) * elec_rate_per_kwh

    # Property cost
    property_cost = campus_size_square_ft * land_cost_sqft
    land_building_cost = property_cost + building_capex

    # Property taxes
    real_property_taxes = land_building_cost * assessed_real_property_frac * real_property_tax_rate
    personal_property_taxes = (equipment_capex * assessed_personal_property_frac) * personal_prop_tax_rate
    total_property_tax = real_property_taxes + personal_property_taxes

    # Sales taxes
    equipment_sales_tax = equipment_capex * sales_tax_rate
    energy_sales_tax = energy_cost * sales_tax_rate
    total_sales_tax = equipment_sales_tax + energy_sales_tax

    # Interconnection costs
    interconnection_cost = interconnection_distance_km * interconnection_cost_km

    cost_dict: Dict[str, float] = {
        'property_cost': property_cost,
        'building_cost': building_capex,
        'energy_cost': energy_cost,
        'total_property_tax': total_property_tax,
        'total_sales_tax': total_sales_tax,
        'interconnection_cost': interconnection_cost,
    }
    cost_list = [cost_dict[i] for i in cost_dict.keys()]

    return round((sum(cost_list) / 1_000_000), 2), cost_dict
