from typing import Any

import h5py as h5
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
from numpy.typing import NDArray
import pandas as pd
from plotid.publish import publish
from plotid.tagplot import tagplot


def read_metadata(file: str, dataset_path: str, attr_key: str) -> Any | None:
    """get attribute from hdf5 file"""
    with h5.File(file, 'r') as file_opened:
        dataset = file_opened[dataset_path]
        if dataset.attrs.get(attr_key) is not None:
            return dataset.attrs[attr_key]
        else:
            print("Attribute not found")

def read_data(file: str, dataset_path: str) -> np.ndarray | None:
    """Read dataset from HDF5 file and return as numpy array"""
    with h5.File(file, 'r') as file_opened:
        if dataset_path in file_opened:
            dataset = file_opened[dataset_path]
            if isinstance(dataset, h5.Group):
                print(f"Path '{dataset_path}' is a group, not a dataset.")
                return None
            data = np.array(dataset)
            return data
        else:
            print(f"Dataset '{dataset_path}' not found in file '{file}'")
            return None


def check_equal_length(*arrays: NDArray) -> bool:
    last_element = arrays[0]
    for i in arrays:
        if last_element.ndim != i.ndim:
            return False
        last_element = i
    return True


def process_time_data(data: NDArray) -> NDArray:
    first_timestamp = data[0]
    return (data - first_timestamp)*1e-9

def remove_negatives(array: NDArray) -> NDArray:
    for x,i in enumerate(array):
        if i < 0:
            array[x] = np.nan
    return array
            

def linear_interpolation(
    time: NDArray, start_time: float, end_time: float, start_y: float, end_y: float
) -> NDArray:
    interpolated_data = time.copy()
    for x,i in enumerate(interpolated_data):
        interpolated_data[x] = start_y + (end_y - start_y) * ((i - start_time) / (end_time - start_time))
    return interpolated_data


def interpolate_nan_data(time: NDArray, y_data: NDArray) -> NDArray:
    active_gap = False
    interpolated_data = y_data.copy()

    if np.isnan(y_data[0]) or np.isnan(y_data[-1]):
        exception = ValueError("First or last value is NaN")
        raise exception
    else:
        for x,i in enumerate(y_data):
            if np.isnan(i) and active_gap == False:
                start_index = x-1
                active_gap = True
            if not np.isnan(i) and active_gap == True:
                end_index = x
                interpolated_data[start_index:end_index] = linear_interpolation(time[start_index:end_index], time[start_index], time[end_index], y_data[start_index], y_data[end_index])
                active_gap = False
        return interpolated_data


def filter_data(data: NDArray, window_size: int) -> NDArray:
    """Filter data using a moving average approach.

    Args:
        data (NDArray): Data to be filtered
        window_size (int): Window size of the filter

    Returns:
        NDArray: Filtered data
    """
    output = []
    pad_width = window_size // 2
    padded_data = np.pad(array=data, pad_width=pad_width, mode="edge")
    for i in range(pad_width, padded_data.size - pad_width):
        # Implementieren Sie hier den SMA!
        sma = padded_data[i-pad_width:i+pad_width+1].mean()
        output.append(sma)
    return np.array(output)


def calc_heater_heat_flux(P_heater: float, eta_heater: float) -> float:
    return P_heater*eta_heater


def calc_convective_heat_flow(
    k_tank: float, area_tank: float, t_total: NDArray, t_env: float
) -> NDArray:
    return k_tank*area_tank*(t_total-t_env)


def calc_mass(
    level_data: NDArray, tank_footprint: float, density: float
) -> NDArray:
    """level_data: level data in mm
    tank_footprint: tank footprint in m^2
    density: density in kg/m^3"""
    mass_array = level_data*tank_footprint*density/1000
    return mass_array


def calc_transported_power(
    mass_flow: float, specific_heat_capacity: float, temperature: float
) -> float:
    return mass_flow*specific_heat_capacity*temperature


def calc_enthalpy(mass: float, specific_heat_capacity: float, temperature: float
) -> float:
    return mass*specific_heat_capacity*temperature


def store_plot_data(
    data: dict[str, NDArray], file_path: str, group_path: str, metadata: dict[str, Any]
) -> None:
    pandas_df = pd.DataFrame(data)
    pandas_df.to_hdf(file_path, key=group_path, mode="w")
    with pd.HDFStore(file_path) as store:
        store.get_storer(group_path).attrs.metadata = metadata


def read_plot_data(
    file_path: str, group_path: str
) -> tuple[pd.DataFrame, dict[str, Any]]:
    with pd.HDFStore(file_path) as store:
        stored_metadata = store.get_storer(group_path).attrs.metadata
        stored_data = store[group_path]
    return stored_data, stored_metadata


def plot_data(data: pd.DataFrame, metadata: dict[str, str]) -> Figure:
    fig, ax = plt.subplots()

    # Plotten der Daten
    print(data)
    for column in data.columns[1:]:  # Überspringe die erste Spalte (Zeit)
        ax.plot(data.iloc[:, 0], data[column], label=column)

    # Beschriften der Achsen
    ax.set_xlabel(f"{metadata['x_label']} ({metadata['x_unit']})")
    ax.set_ylabel(f"{metadata['y_label']} ({metadata['y_unit']})")

    # Hinzufügen der Legende
    ax.legend(title=metadata["legend_title"])

    # Titel des Plots (optional)
    ax.set_title(metadata["legend_title"])

    plt.show()
    return fig



def publish_plot(
    fig: Figure, source_paths: str | list[str], destination_path: str
) -> None:
    tag_plot = tagplot(fig, engine="matplotlib", id_method="time", prefix="“GdD_WS_2425_2808064_“")
    publish(tag_plot, source_paths, destination_path)
if __name__ == "__main__":
    pass
