

def calculate_locational_cost(campus_size_square_ft, 
                        land_cost_sqft, 
                        elec_rate_per_kwh, 
                        personal_prop_tax_rate,
                        real_property_tax_rate, 
                        sales_tax_rate ,
                        interconnection_distance_km ,
                        cooling_type ,
                        equipment_capex ,
                        building_capex , 
                        interconnection_cost_km,
                        data_center_power_mw,
                        pue,
                        operational_frac = 1,
                        assessed_real_property_frac = 0.16,
                        assessed_personal_property_frac = 0.80,
                        air_cooling_multiplier = 1.25
                        ):
    """
    Calculate the locational cost for a data center campus based on various parameters.
    
    Parameters:
        campus_size_square_ft (float): Size of the campus in square feet.
        land_cost_sqft (float): Cost of land per square foot.
        elec_rate_per_kwh (float): Electricity rate in $/kWh.
        personal_prop_tax_rate (float): Personal property tax rate.
        real_property_tax_rate (float): Real property tax rate.
        sales_tax_rate (float): Sales tax rate.
        interconnection_distance_km (float): Distance to interconnection in kilometers.
        cooling_type (int): Type of cooling system (0 for mechanical, 1 for other).
        equipment_capex (float): Capital expenditure for equipment.
        building_capex (float): Capital expenditure for building.
        interconnection_cost_km (float): Cost per kilometer for interconnection.
        data_center_power_mw (float): Power capacity of the data center in MW.
        pue (float): Power Usage Effectiveness of the data center.
        operational_frac (float): Fraction of the year the data center is operational (default is 1).
        assessed_real_property_frac (float): Fraction of real property assessed for tax (default is 0.16).
        assessed_personal_property_frac (float): Fraction of personal property assessed for tax (default is 0.80).
        air_cooling_multiplier (float): Multiplier for mechanical cooling (default is 1.25).
    Returns:
        tuple: Total locational cost in millions and a dictionary of individual costs.
    """

    HOURS_PER_YEAR = 8760
    MWH_TO_KWH = 1000

    # calculate facility power capacity
    if cooling_type == 0: # mechanical cooling
        facility_power_cap_mw = (data_center_power_mw * pue) * air_cooling_multiplier
    else:
        facility_power_cap_mw = (data_center_power_mw * pue)

    # calculate total electricity demand
    total_mwh_per_year = facility_power_cap_mw * (operational_frac * HOURS_PER_YEAR)

    # energy cost
    energy_cost = (total_mwh_per_year * MWH_TO_KWH) * elec_rate_per_kwh

    # property cost
    property_cost = campus_size_square_ft * land_cost_sqft
    land_building_cost = property_cost + building_capex

    # property taxes
    real_property_taxes = land_building_cost * assessed_real_property_frac * real_property_tax_rate
    personal_property_taxes = (equipment_capex * assessed_personal_property_frac) * personal_prop_tax_rate
    total_property_tax = real_property_taxes + personal_property_taxes

    # sales taxes
    equipment_sales_tax = equipment_capex * sales_tax_rate
    energy_sales_tax = energy_cost * sales_tax_rate
    total_sales_tax = equipment_sales_tax + energy_sales_tax

    # interconnection costs
    interconnection_cost = interconnection_distance_km * interconnection_cost_km

    cost_dict = {'property_cost': property_cost, 
                 'building_cost': building_capex,
                 'energy_cost': energy_cost, 
                 'total_property_tax': total_property_tax , 
                 'total_sales_tax': total_sales_tax ,
                 'interconnection_cost': interconnection_cost ,
                }
    cost_list = [cost_dict[i] for i in cost_dict.keys()]     

    return round((sum(cost_list)/1000000), 2), cost_dict