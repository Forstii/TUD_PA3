import datetime
import os
import numpy
import pandas
import matplotlib.pyplot as plt
import h5py
import plotid
import numpy as np

import project.functions as fn

brewing = "brewing_0001"
tank_id = "B002"
filter_sizes = (2, 26, 54, 205)
compound_path = f"{brewing}/{tank_id}"

file_path = "/Users/adrianforst/Desktop/PA3/pa-ws2425/project/data/data_GdD_Datensatz_WS2425.h5"
h5_path = "/Users/adrianforst/Desktop/PA3/pa-ws2425/project/data/data_ GdD_plot_WS2425.h5"
group_path = compound_path

measured_quantities = ("level", "temperature", "timestamp")
T_env = fn.read_metadata(file_path, brewing, "T_env")
specific_heat_capacity_beer = fn.read_metadata(file_path, brewing, "specific_heat_capacity_beer")
density_beer = fn.read_metadata(file_path, brewing, "density_beer")
tank_properties = ["mass_tank", "surface_area_tank", "footprint_tank", "heat_transfer_coeff_tank", "specific_heat_capacity_tank"]
mass_tank = fn.read_metadata(file_path, compound_path, "mass_tank")
specific_heat_capacity_tank = fn.read_metadata(file_path, compound_path, "specific_heat_capacity_tank")
efficiency_heater = fn.read_metadata(file_path, compound_path, "efficiency_heater")
power_heater = fn.read_metadata(file_path, compound_path, "power_heater")
footprint_tank = fn.read_metadata(file_path, compound_path, "footprint_tank")
heat_transfer_coeff_tank = fn.read_metadata(file_path, compound_path, "heat_transfer_coeff_tank")
surface_area_tank = fn.read_metadata(file_path, compound_path, "surface_area_tank")

raw_data = {}
processed_data = {}
df_data = {}
metadata = {
"legend_title": f"Inner Energy calculated using SMA window Sizes of {filter_sizes[0]}, {filter_sizes[1]}, {filter_sizes[2]}, {filter_sizes[3]}",
"x_label": "time",
"x_unit": "s",
"y_label": "Inner Energy",
"y_unit": "J",
}


def main():
    
    for i in tank_properties:
        print(f"{i} " + str(fn.read_metadata(file_path, compound_path, i)))
    
    for i in measured_quantities:
        read_data = fn.read_data(file_path, f"{compound_path}/{i}")
        raw_data[i] = read_data

    raw_arrays = raw_data.values()
    if not fn.check_equal_length(*raw_arrays):
        exception = ValueError("Arrays have different dimensions")
        raise exception
    
    df_data["time"] = fn.process_time_data(raw_data["timestamp"])
    print(df_data["time"])

    for x,i in enumerate(filter_sizes):
        processed_data[f"temperature_k_{i}"] = fn.filter_data(raw_data["temperature"], i)
    print(processed_data)

    print(df_data["time"])

    raw_data["level"] = fn.remove_negatives(raw_data["level"])
    raw_data["level"] = fn.interpolate_nan_data(df_data["time"], raw_data["level"])

    print(df_data["time"])

    energy_tank = fn.calc_enthalpy(mass_tank,specific_heat_capacity_tank, T_env)
    heater_heat_flux = fn.calc_heater_heat_flux(power_heater, efficiency_heater)
    

    for c,i in enumerate(filter_sizes):
        convective_heat_flow = fn.calc_convective_heat_flow(heat_transfer_coeff_tank, surface_area_tank, processed_data[f"temperature_k_{i}"], T_env)
        processed_data[f"level_k_{i}"] = fn.filter_data(raw_data["level"], i)
        mass_array = fn.calc_mass(processed_data[f"level_k_{i}"], footprint_tank, density_beer)
        inner_energy = []
        for x,y in enumerate(df_data["time"]):
            energy_value = y * heater_heat_flux - convective_heat_flow[x] * y + mass_array[x]*specific_heat_capacity_beer*processed_data[f"temperature_k_{i}"][x] + energy_tank
            inner_energy.append(energy_value)
        df_data[f"inner_energy_k_{i}"] = np.array(inner_energy)

    fn.store_plot_data(df_data, h5_path, group_path, metadata)


    data, df_metadata = fn.read_plot_data(h5_path, group_path)
    figure = fn.plot_data(data, df_metadata)
    #fn.publish_plot(figure, h5_path, "./plotid")
    
    

if __name__ == "__main__":
    main()
