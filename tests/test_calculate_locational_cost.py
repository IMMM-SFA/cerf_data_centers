import pytest
from cerf_data_centers.calculate_locational_cost import calculate_locational_cost


def test_calculate_locational_cost_basic():
    # Basic test with typical values
    total_cost, cost_dict = calculate_locational_cost(
        campus_size_square_ft=1000000,
        land_cost_usd_per_sqft=10,
        elec_rate_usd_per_kwh=0.08,
        personal_prop_tax_rate=0.01,
        real_property_tax_rate=0.012,
        sales_tax_rate=0.07,
        interconnection_distance_km=5,
        equipment_capex_usd=200_000_000,
        building_capex_usd=250_000_000,
        interconnection_cost_usd_per_km=1_000_000,
        data_center_it_power_mw=36,
        data_center_pue=1.3
    )
    assert isinstance(total_cost, float)
    assert isinstance(cost_dict, dict)
    assert total_cost > 0
    # Check that all expected keys are present
    for key in [
        'property_cost_usd', 'building_capex', 'electricity_cost_usd',
        'total_property_tax_usd', 'total_sales_tax_usd', 'interconnection_cost_usd'
    ]:
        assert key in cost_dict

def test_cooling_type_mechanical_vs_other():
    # Test that mechanical cooling (mechanical_cool_fraction=1.0) increases energy cost
    args = dict(
        campus_size_square_ft=500000,
        land_cost_usd_per_sqft=8,
        elec_rate_usd_per_kwh=0.10,
        personal_prop_tax_rate=0.015,
        real_property_tax_rate=0.013,
        sales_tax_rate=0.06,
        interconnection_distance_km=2,
        equipment_capex_usd=100_000_000,
        building_capex_usd=120_000_000,
        interconnection_cost_usd_per_km=500_000,
        data_center_it_power_mw=20,
        data_center_pue=1.2
    )
    cost_mech, dict_mech = calculate_locational_cost(mechanical_cool_fraction=1.0, water_cool_fraction=0.0, **args)
    cost_other, dict_other = calculate_locational_cost(mechanical_cool_fraction=0.0, water_cool_fraction=1.0, **args)
    # Mechanical cooling should have higher energy cost due to higher electricity demand
    assert dict_mech['electricity_cost_usd'] > dict_other['electricity_cost_usd']
    assert cost_mech > cost_other

def test_facility_overhead_fraction():
    # If facility_overhead_frac is 0, facility overhead energy should be 0
    total_cost, cost_dict = calculate_locational_cost(
        campus_size_square_ft=100000,
        land_cost_usd_per_sqft=5,
        elec_rate_usd_per_kwh=0.09,
        personal_prop_tax_rate=0.012,
        real_property_tax_rate=0.011,
        sales_tax_rate=0.05,
        interconnection_distance_km=1,
        equipment_capex_usd=50_000_000,
        building_capex_usd=60_000_000,
        interconnection_cost_usd_per_km=200_000,
        data_center_it_power_mw=10,
        data_center_pue=1.1,
        facility_overhead_frac=0
    )
    # With facility_overhead_frac=0, all overhead energy should go to cooling
    assert cost_dict['cooling_energy_demand_mwh'] > 0

def test_assessed_property_fractions():
    # Test with custom assessed property fractions
    total_cost, cost_dict = calculate_locational_cost(
        campus_size_square_ft=200000,
        land_cost_usd_per_sqft=12,
        elec_rate_usd_per_kwh=0.07,
        personal_prop_tax_rate=0.02,
        real_property_tax_rate=0.015,
        sales_tax_rate=0.08,
        interconnection_distance_km=3,
        equipment_capex_usd=80_000_000,
        building_capex_usd=100_000_000,
        interconnection_cost_usd_per_km=750_000,
        data_center_it_power_mw=15,
        data_center_pue=1.25,
        assessed_real_property_frac=0.2,
        assessed_personal_property_frac=0.9
    )
    # Check that property tax is calculated as expected
    expected_real = (200000*12 + 100_000_000) * 0.2 * 0.015
    expected_personal = (80_000_000 * 0.9) * 0.02
    assert cost_dict['total_property_tax_usd'] == pytest.approx(expected_real + expected_personal)

def test_interconnection_cost_calculation():
    # Interconnection cost should be distance * cost per km
    total_cost, cost_dict = calculate_locational_cost(
        campus_size_square_ft=300000,
        land_cost_usd_per_sqft=15,
        elec_rate_usd_per_kwh=0.11,
        personal_prop_tax_rate=0.018,
        real_property_tax_rate=0.014,
        sales_tax_rate=0.09,
        interconnection_distance_km=7,
        equipment_capex_usd=120_000_000,
        building_capex_usd=140_000_000,
        interconnection_cost_usd_per_km=2_000_000,
        data_center_it_power_mw=25,
        data_center_pue=1.18
    )
    assert cost_dict['interconnection_cost_usd'] == 7 * 2_000_000

def test_water_cooling_calculation():
    # Test water cooling calculations
    total_cost, cost_dict = calculate_locational_cost(
        campus_size_square_ft=150000,
        land_cost_usd_per_sqft=10,
        elec_rate_usd_per_kwh=0.08,
        personal_prop_tax_rate=0.01,
        real_property_tax_rate=0.012,
        sales_tax_rate=0.07,
        interconnection_distance_km=4,
        equipment_capex_usd=90_000_000,
        building_capex_usd=110_000_000,
        interconnection_cost_usd_per_km=800_000,
        data_center_it_power_mw=18,
        data_center_pue=1.3,
        mechanical_cool_fraction=0.3,
        water_cool_fraction=0.7,
        cooling_water_intensity_gal_per_mwh=460,
        cooling_water_consumption_fraction=0.8
    )
    # Check that water demand and consumption are calculated correctly
    assert cost_dict['cooling_water_demand_mgy'] > 0
    assert cost_dict['cooling_water_consumption_mgy'] > 0
    assert cost_dict['cooling_water_consumption_mgy'] < cost_dict['cooling_water_demand_mgy']

def test_negative_or_zero_inputs():
    # Negative or zero values for costs should not cause errors, but may result in zero or negative costs
    total_cost, cost_dict = calculate_locational_cost(
        campus_size_square_ft=0,
        land_cost_usd_per_sqft=0,
        elec_rate_usd_per_kwh=0,
        personal_prop_tax_rate=0,
        real_property_tax_rate=0,
        sales_tax_rate=0,
        interconnection_distance_km=0,
        equipment_capex_usd=0,
        building_capex_usd=0,
        interconnection_cost_usd_per_km=0,
        data_center_it_power_mw=0,
        data_center_pue=1.0
    )
    assert total_cost == 0
    for key in ['property_cost_usd', 'electricity_cost_usd', 'total_property_tax_usd', 
                'total_sales_tax_usd', 'interconnection_cost_usd']:
        assert cost_dict[key] == 0

def test_pue_impact_on_energy_cost():
    # Higher PUE should result in higher energy costs
    args = dict(
        campus_size_square_ft=100000,
        land_cost_usd_per_sqft=8,
        elec_rate_usd_per_kwh=0.10,
        personal_prop_tax_rate=0.015,
        real_property_tax_rate=0.013,
        sales_tax_rate=0.06,
        interconnection_distance_km=2,
        equipment_capex_usd=50_000_000,
        building_capex_usd=60_000_000,
        interconnection_cost_usd_per_km=500_000,
        data_center_it_power_mw=10
    )
    cost_low_pue, dict_low_pue = calculate_locational_cost(data_center_pue=1.1, **args)
    cost_high_pue, dict_high_pue = calculate_locational_cost(data_center_pue=1.5, **args)
    
    assert dict_high_pue['electricity_cost_usd'] > dict_low_pue['electricity_cost_usd']
    assert cost_high_pue > cost_low_pue

def test_energy_demand_calculations():
    # Test that energy demand calculations are correct
    total_cost, cost_dict = calculate_locational_cost(
        campus_size_square_ft=200000,
        land_cost_usd_per_sqft=10,
        elec_rate_usd_per_kwh=0.08,
        personal_prop_tax_rate=0.01,
        real_property_tax_rate=0.012,
        sales_tax_rate=0.07,
        interconnection_distance_km=3,
        equipment_capex_usd=80_000_000,
        building_capex_usd=100_000_000,
        interconnection_cost_usd_per_km=750_000,
        data_center_it_power_mw=20,
        data_center_pue=1.3,
        facility_overhead_frac=0.1
    )
    
    # IT energy demand should be 20 MW * 8760 hours = 175,200 MWh
    expected_it_energy = 20 * 8760
    # Total facility energy should be IT energy * PUE
    expected_total_facility_energy = expected_it_energy * 1.3
    # Overhead energy should be total - IT
    expected_overhead = expected_total_facility_energy - expected_it_energy
    # Facility overhead energy (10% of overhead)
    expected_facility_overhead = expected_overhead * 0.1
    # Cooling energy should be overhead - facility overhead
    expected_cooling_energy = expected_overhead - expected_facility_overhead
    # Mechanical cooling is 50% of cooling energy (default mechanical_cool_fraction)
    expected_mechanical_cooling = expected_cooling_energy * 0.5
    
    assert cost_dict['cooling_energy_demand_mwh'] == pytest.approx(expected_mechanical_cooling)
    assert cost_dict['electricity_cost_usd'] > 0
