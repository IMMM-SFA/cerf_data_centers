import pytest
from cerf_data_centers.calculate_locational_cost import calculate_locational_cost


def test_calculate_locational_cost_basic():
    # Basic test with typical values
    total_cost, cost_dict = calculate_locational_cost(
        campus_size_square_ft=1000000,
        land_cost_sqft=10,
        elec_rate_per_kwh=0.08,
        personal_prop_tax_rate=0.01,
        real_property_tax_rate=0.012,
        sales_tax_rate=0.07,
        interconnection_distance_km=5,
        cooling_type=0,
        equipment_capex=200_000_000,
        building_capex=250_000_000,
        interconnection_cost_km=1_000_000,
        data_center_power_mw=36,
        pue=1.3
    )
    assert isinstance(total_cost, float)
    assert isinstance(cost_dict, dict)
    assert total_cost > 0
    # Check that all expected keys are present
    for key in [
        'property_cost', 'building_cost', 'energy_cost',
        'total_property_tax', 'total_sales_tax', 'interconnection_cost'
    ]:
        assert key in cost_dict

def test_cooling_type_mechanical_vs_other():
    # Test that mechanical cooling (cooling_type=0) increases energy cost
    args = dict(
        campus_size_square_ft=500000,
        land_cost_sqft=8,
        elec_rate_per_kwh=0.10,
        personal_prop_tax_rate=0.015,
        real_property_tax_rate=0.013,
        sales_tax_rate=0.06,
        interconnection_distance_km=2,
        equipment_capex=100_000_000,
        building_capex=120_000_000,
        interconnection_cost_km=500_000,
        data_center_power_mw=20,
        pue=1.2
    )
    cost_mech, dict_mech = calculate_locational_cost(cooling_type=0, **args)
    cost_other, dict_other = calculate_locational_cost(cooling_type=1, **args)
    # Mechanical cooling should have higher energy cost due to air_cooling_multiplier
    assert dict_mech['energy_cost'] > dict_other['energy_cost']
    assert cost_mech > cost_other

def test_zero_operational_fraction():
    # If operational_frac is 0, energy cost and energy sales tax should be 0
    total_cost, cost_dict = calculate_locational_cost(
        campus_size_square_ft=100000,
        land_cost_sqft=5,
        elec_rate_per_kwh=0.09,
        personal_prop_tax_rate=0.012,
        real_property_tax_rate=0.011,
        sales_tax_rate=0.05,
        interconnection_distance_km=1,
        cooling_type=1,
        equipment_capex=50_000_000,
        building_capex=60_000_000,
        interconnection_cost_km=200_000,
        data_center_power_mw=10,
        pue=1.1,
        operational_frac=0
    )
    assert cost_dict['energy_cost'] == 0
    # Sales tax on energy should be zero
    assert cost_dict['total_sales_tax'] == pytest.approx(50_000_000 * 0.05)

def test_assessed_property_fractions():
    # Test with custom assessed property fractions
    total_cost, cost_dict = calculate_locational_cost(
        campus_size_square_ft=200000,
        land_cost_sqft=12,
        elec_rate_per_kwh=0.07,
        personal_prop_tax_rate=0.02,
        real_property_tax_rate=0.015,
        sales_tax_rate=0.08,
        interconnection_distance_km=3,
        cooling_type=1,
        equipment_capex=80_000_000,
        building_capex=100_000_000,
        interconnection_cost_km=750_000,
        data_center_power_mw=15,
        pue=1.25,
        assessed_real_property_frac=0.2,
        assessed_personal_property_frac=0.9
    )
    # Check that property tax is calculated as expected
    expected_real = (200000*12 + 100_000_000) * 0.2 * 0.015
    expected_personal = (80_000_000 * 0.9) * 0.02
    assert cost_dict['total_property_tax'] == pytest.approx(expected_real + expected_personal)

def test_interconnection_cost_calculation():
    # Interconnection cost should be distance * cost per km
    total_cost, cost_dict = calculate_locational_cost(
        campus_size_square_ft=300000,
        land_cost_sqft=15,
        elec_rate_per_kwh=0.11,
        personal_prop_tax_rate=0.018,
        real_property_tax_rate=0.014,
        sales_tax_rate=0.09,
        interconnection_distance_km=7,
        cooling_type=1,
        equipment_capex=120_000_000,
        building_capex=140_000_000,
        interconnection_cost_km=2_000_000,
        data_center_power_mw=25,
        pue=1.18
    )
    assert cost_dict['interconnection_cost'] == 7 * 2_000_000

def test_rounding_of_total_cost():
    # The returned total cost should be rounded to two decimals
    total_cost, _ = calculate_locational_cost(
        campus_size_square_ft=123456,
        land_cost_sqft=7.89,
        elec_rate_per_kwh=0.123,
        personal_prop_tax_rate=0.017,
        real_property_tax_rate=0.013,
        sales_tax_rate=0.055,
        interconnection_distance_km=4.5,
        cooling_type=0,
        equipment_capex=65_432_100,
        building_capex=87_654_300,
        interconnection_cost_km=1_234_567,
        data_center_power_mw=12.34,
        pue=1.21
    )
    # Should have at most two decimals
    assert round(total_cost, 2) == total_cost

def test_negative_or_zero_inputs():
    # Negative or zero values for costs should not cause errors, but may result in zero or negative costs
    total_cost, cost_dict = calculate_locational_cost(
        campus_size_square_ft=0,
        land_cost_sqft=0,
        elec_rate_per_kwh=0,
        personal_prop_tax_rate=0,
        real_property_tax_rate=0,
        sales_tax_rate=0,
        interconnection_distance_km=0,
        cooling_type=1,
        equipment_capex=0,
        building_capex=0,
        interconnection_cost_km=0,
        data_center_power_mw=0,
        pue=1.0
    )
    assert total_cost == 0
    for v in cost_dict.values():
        assert v == 0
