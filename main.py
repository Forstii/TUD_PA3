"""main script for calculating the inner energy of a tank and plotting the data and storing the\n
plots using plotid lines 7-13 have to be customized based on path, filter sizes and filter group"""
import numpy as np
import project.functions as fn


BREWING = "brewing_0001"
TANK_ID = "B002"
FILTER_SIZES = (2, 26, 54, 205)
COMPOUND_PATH = f"{BREWING}/{TANK_ID}"

FILE_PATH = "/Users/adrianforst/Desktop/PA3/pa-ws2425/project/data/data_GdD_Datensatz_WS2425.h5"
H5_PATH = "/Users/adrianforst/Desktop/PA3/pa-ws2425/project/data/data_ GdD_plot_WS2425.h5"

measured_quantities = ("level", "temperature", "timestamp")
T_env = fn.read_metadata(FILE_PATH, BREWING, "T_env")
specific_heat_capacity_beer = fn.read_metadata(
    FILE_PATH, BREWING, "specific_heat_capacity_beer")
density_beer = fn.read_metadata(FILE_PATH, BREWING, "density_beer")
tank_properties = [
    "mass_tank",
    "surface_area_tank",
    "footprint_tank",
    "heat_transfer_coeff_tank",
    "specific_heat_capacity_tank"]
mass_tank = fn.read_metadata(FILE_PATH, COMPOUND_PATH, "mass_tank")
specific_heat_capacity_tank = fn.read_metadata(
    FILE_PATH, COMPOUND_PATH, "specific_heat_capacity_tank")
efficiency_heater = fn.read_metadata(
    FILE_PATH, COMPOUND_PATH, "efficiency_heater")
power_heater = fn.read_metadata(FILE_PATH, COMPOUND_PATH, "power_heater")
footprint_tank = fn.read_metadata(FILE_PATH, COMPOUND_PATH, "footprint_tank")
heat_transfer_coeff_tank = fn.read_metadata(
    FILE_PATH, COMPOUND_PATH, "heat_transfer_coeff_tank")
surface_area_tank = fn.read_metadata(
    FILE_PATH, COMPOUND_PATH, "surface_area_tank")

raw_data = {}
processed_data = {}
df_data = {}
metadata = {
    "legend_title": (
        "value after k corresponding to SMA window Size"
    ),
    "title": (
        f"Inner Energy calculated using SMA window Sizes of "
        f"{FILTER_SIZES[0]}, {FILTER_SIZES[1]}, {FILTER_SIZES[2]}, {FILTER_SIZES[3]}"
    ),
    "x_label": "time", # SI Units are used, conversion to hours and gJ done by plot function
    "x_unit": "hours",
    "y_label": "Inner Energy",
    "y_unit": "gigaJoules",
    "text" : "The calculation for the inner energy is based on datasets of temperature\n"
    "filling level of the beer vat as well as the surface area and the heat transfer\n"
    "coefficient of the vat. Depending on the set group (originally 0001/0002),\n"
    "heating elements are also taken into account if in accordance with\n"
    "the naming convention used for this project."
}

def main():
    """Main function for calculating the inner energy of a tank plotting the data\n 
    and storing the plots using plotid"""


    for i in tank_properties:
        print(f"{i} " + str(fn.read_metadata(FILE_PATH, COMPOUND_PATH, i)))

    for i in measured_quantities:
        read_data = fn.read_data(FILE_PATH, f"{COMPOUND_PATH}/{i}")
        raw_data[i] = read_data

    raw_arrays = raw_data.values()
    if not fn.check_equal_length(*raw_arrays):
        exception = ValueError("Arrays have different dimensions")
        raise exception

    df_data["time"] = fn.process_time_data(raw_data["timestamp"])

    for x, i in enumerate(FILTER_SIZES):
        processed_data[f"temperature_k_{i}"] = fn.filter_data(
            raw_data["temperature"], i)


    raw_data["level"] = fn.remove_negatives(raw_data["level"])
    raw_data["level"] = fn.interpolate_nan_data(
                        df_data["time"], raw_data["level"])

    heater_heat_flux = fn.calc_heater_heat_flux(
        power_heater, efficiency_heater)

    for i in FILTER_SIZES:
        #convective_heat_flow = fn.calc_convective_heat_flow(
        #    heat_transfer_coeff_tank,
        #    surface_area_tank,
        #    processed_data[f"temperature_k_{i}"*273,15],
        #    T_env)
        processed_data[f"level_k_{i}"] = fn.filter_data(raw_data["level"], i)
        mass_array = fn.calc_mass(
            processed_data[f"level_k_{i}"],
            footprint_tank,
            density_beer)
        inner_energy = []
        for x, y in enumerate(df_data["time"]):
            energy_tank = fn.calc_enthalpy(
            mass_tank, specific_heat_capacity_tank,
            (processed_data[f"temperature_k_{i}"][x]*273.15))
            energy_value = (
                y * heater_heat_flux
                # The convective heat flow is not included, as it would render
                # calculations based on temperature data obsolete.
                # (Nachgefragt in PA3 Fragestunde 11:00 bei Sascha Lamm)
                + mass_array[x] * specific_heat_capacity_beer
                * (processed_data[f"temperature_k_{i}"][x] * 273.15)
                + energy_tank
            )
            inner_energy.append(energy_value)
        df_data[f"inner_energy_k_{i}"] = np.array(inner_energy)

    for key in df_data:
        if key != "time":
            df_data[key] = df_data[key]/1e9
        else:
            df_data[key] = df_data[key]/3600

    fn.store_plot_data(df_data, H5_PATH, COMPOUND_PATH, metadata)

    data, df_metadata = fn.read_plot_data(H5_PATH, COMPOUND_PATH)
    figure = fn.plot_data(data, df_metadata)
    fn.publish_plot(figure, H5_PATH, "./plotid")



if __name__ == "__main__":
    main()
