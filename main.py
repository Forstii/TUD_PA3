import datetime
import os
import numpy
import pandas
import matplotlib
import h5py
import plotid
import numpy as np

import project.functions as fn

file_path = "/Users/adrianforst/Desktop/PA3/pa-ws2425/project/data/data_GdD_Datensatz_WS2425.h5"
brewing = "brewing_0001"
tank_id = "B002"
compound_path = f"{brewing}/{tank_id}"
measured_quantities = ("level", "temperature", "timestamp")
T_env = fn.read_metadata(file_path, brewing, "T_env")
specific_heat_capacity_beer = fn.read_metadata(file_path, brewing, "specific_heat_capacity_beer")
density_beer = fn.read_metadata(file_path, brewing, "density_beer")
tank_properties = ["mass_tank", "surface_area_tank", "footprint_tank", "heat_transfer_coeff_tank", "specific_heat_capacity_tank"]
df_data = {}

def main():
    for i in tank_properties:
        print(f"{i} " + str(fn.read_metadata(file_path, compound_path, i)))
    raw_data = {}
    for i in measured_quantities:
        raw_data[i] = fn.read_metadata(file_path, compound_path, i)
    print(raw_data)
if __name__ == "__main__":
    main()
