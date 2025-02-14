"""
This module provides functions for reading, processing, and plotting data from HDF5 files.
Functions:
    read_metadata(file: str, dataset_path: str, attr_key: str) -> Any | None:
    read_data(file: str, dataset_path: str) -> np.ndarray | None:
    check_equal_length(*arrays: NDArray) -> bool:
    process_time_data(data: NDArray) -> NDArray:
    remove_negatives(array: NDArray) -> NDArray:
    linear_interpolation(time: NDArray, start_time: float, end_time: float
    start_y: float, end_y: float) -> NDArray:
        Perform linear interpolation for a given set of time points.
    interpolate_nan_data(time: NDArray, y_data: NDArray) -> NDArray:
    filter_data(data: NDArray, window_size: int) -> NDArray:
        Filter data using a moving average approach.
    calc_heater_heat_flux(p_heater: float, eta_heater: float) -> float:
    calc_convective_heat_flow(k_tank: float, area_tank: 
    float, t_total: NDArray, t_env: float) -> NDArray:
    calc_mass(level_data: NDArray, tank_footprint: float, density: float) -> NDArray:
    calc_transported_power(mass_flow: float, specific_heat_capacity: float,
    temperature: float) -> float:
    calc_enthalpy(mass: float, specific_heat_capacity: float, temperature: float) -> float:
    store_plot_data(data: dict[str, NDArray], file_path: str,
    group_path: str, metadata: dict[str, Any]) -> None:
    read_plot_data(file_path: str, group_path: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    plot_data(data: pd.DataFrame, metadata: dict[str, str]) -> Figure:
    publish_plot(fig: Figure, source_paths: str | list[str], destination_path: str) -> None:
"""

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
    """
    Reads metadata from an HDF5 file.
    Args:
        file (str): The path to the HDF5 file.
        dataset_path (str): The path to the dataset within the HDF5 file.
        attr_key (str): The key of the attribute to retrieve.
    Returns:
        Any | None: The value of the attribute if it exists, otherwise None.
    """

    with h5.File(file, 'r') as file_opened:
        dataset = file_opened[dataset_path]
        if dataset.attrs.get(attr_key) is not None:
            return dataset.attrs[attr_key]
        print("Attribute not found")
        return None


def read_data(file: str, dataset_path: str) -> np.ndarray | None:
    """
    Reads a dataset from an HDF5 file and returns it as a NumPy array.
    Args:
        file (str): The path to the HDF5 file.
        dataset_path (str): The path to the dataset within the HDF5 file.
    Returns:
    np.ndarray | None: The dataset as a NumPy array if found, otherwise None.
    """

    with h5.File(file, 'r') as file_opened:
        if dataset_path in file_opened:
            dataset = file_opened[dataset_path]
            if isinstance(dataset, h5.Group):
                print(f"Path '{dataset_path}' is a group, not a dataset.")
                return None
            data = np.array(dataset)
            return data
        print(f"Dataset '{dataset_path}' not found in file '{file}'")
        return None


def check_equal_length(*arrays: NDArray) -> bool:
    """
    Check if all input arrays have the same number of dimensions.
    Args:
        *arrays (NDArray): Variable number of input arrays to check.
    Returns:
    bool: True if all input arrays have the same number of dimensions, False otherwise.
    """

    last_element = arrays[0]
    for i in arrays:
        if last_element.ndim != i.ndim:
            return False
        last_element = i
    return True


def process_time_data(data: NDArray) -> NDArray:
    """
    Processes time data by normalizing it to the first timestamp and converting it 
    to seconds.
    Args:
        data (NDArray): An array of timestamps in nanoseconds.
    Returns:
    NDArray: An array of timestamps normalized to the first timestamp and converted to seconds.
    """

    first_timestamp = data[0]
    return (data - first_timestamp) * 1e-9


def remove_negatives(array: NDArray) -> NDArray:
    """
    Replaces negative values in the given array with NaN.
    Args:
        array (NDArray): Array with negative values to be replaced.
    Returns:
    NDArray: Array with negative values replaced by NaN.
    """

    for x, i in enumerate(array):
        if i < 0:
            array[x] = np.nan
    return array


def linear_interpolation(
        time: NDArray,
        start_time: float,
        end_time: float,
        start_y: float,
        end_y: float) -> NDArray:
    """Perform linear interpolation for a given set of time points.
        Args:
            time (NDArray): Array of time points at which to interpolate.
            start_time (float): The starting time of the interpolation interval.
            end_time (float): The ending time of the interpolation interval.
            start_y (float): The value at the start_time.
            end_y (float): The value at the end_time.
        Returns:
        NDArray: Array of interpolated values corresponding to the input time points."""
    interpolated_data = time.copy()
    for x, i in enumerate(interpolated_data):
        interpolated_data[x] = start_y + \
            (end_y - start_y) * ((i - start_time) / (end_time - start_time))
    return interpolated_data


def interpolate_nan_data(time: NDArray, y_data: NDArray) -> NDArray:
    """
    Interpolates NaN values in the provided y_data array using linear interpolation.
    Args:
        time (NDArray): An array of time values corresponding to y_data.
        y_data (NDArray): An array of data values that may contain NaNs.
    Returns:
        NDArray: A new array with NaN values replaced by interpolated values.
    Raises:
        ValueError: If the first or last value of y_data is NaN
    """
    active_gap = False
    start_index = None
    interpolated_data = y_data.copy()

    if np.isnan(y_data[0]) or np.isnan(y_data[-1]):
        exception = ValueError("First or last value is NaN")
        raise exception
    for x, i in enumerate(y_data):
        if np.isnan(i) and not active_gap:
            start_index = x - 1
            active_gap = True
        if not np.isnan(i) and active_gap:
            end_index = x
            interpolated_data[start_index:end_index] = linear_interpolation(
                time[start_index:end_index], time[start_index], time[end_index],
                        y_data[start_index], y_data[end_index])
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
        sma = padded_data[i - pad_width:i + pad_width + 1].mean()
        output.append(sma)
    return np.array(output)


def calc_heater_heat_flux(p_heater: float, eta_heater: float) -> float:
    """
    Calculate the heat flux generated by a heater.
    Args:
        p_heater (float): The power of the heater in watts.
        eta_heater (float): The efficiency of the heater (a value between 0 and 1).
    Returns:
    float: The heat flux generated by the heater.
    """
    return p_heater * eta_heater


def calc_convective_heat_flow(k_tank: float,
                              area_tank: float,
                              t_total: NDArray,
                              t_env: float) -> NDArray:
    """
    Calculate the convective heat flow from a tank.
    Args:
        k_tank (float): Thermal conductivity of the tank material.
        area_tank (float): Surface area of the tank.
        t_total (NDArray): Array of total temperatures inside the tank.
        t_env (float): Environmental temperature outside the tank.
    Returns:
    NDArray: Array of convective heat flow values.
    """

    return k_tank * area_tank * (t_total - t_env)


def calc_mass(level_data: NDArray,
              tank_footprint: float,
              density: float) -> NDArray:
    """
    Calculate the mass of the liquid in a tank based on the 
    level data, tank footprint, and liquid density.
    Args:
        level_data (NDArray): An array of liquid levels in the tank.
        tank_footprint (float): The footprint area of the tank in square meters.
        density (float): The density of the liquid in kg/m^3.
    Returns:
        NDArray: An array of masses corresponding to the liquid levels.
    """
    mass_array = level_data * tank_footprint * density / 1000
    return mass_array


def calc_transported_power(mass_flow: float,
                           specific_heat_capacity: float,
                           temperature: float) -> float:
    """
    Calculate the transported power based on mass flow, specific heat capacity,
    and temperature.
    Args:
        mass_flow (float): The mass flow rate (kg/s).
        specific_heat_capacity (float): The specific heat capacity (J/kg·K).
        temperature (float): The temperature difference (K).
    Returns:
        float: The transported power (W).
    """
    return mass_flow * specific_heat_capacity * temperature


def calc_enthalpy(mass: float,
                  specific_heat_capacity: float,
                  temperature: float) -> float:
    """
    Calculate the enthalpy of a substance.
    Enthalpy is calculated using the formula:
    enthalpy = mass * specific_heat_capacity * temperature
    Args:
        mass (float): The mass of the substance in kilograms.
        specific_heat_capacity (float): The specific heat capacity
        of the substance in joules per 
        kilogram per degree Celsius (J/kg°C).
        temperature (float): The temperature change in degrees Celsius (°C).
    Returns:
    float: The calculated enthalpy in joules (J).
    """
    return mass * specific_heat_capacity * temperature


def store_plot_data(data: dict[str,NDArray],
                    file_path: str,
                    group_path: str,
                    metadata: dict[str,Any]) -> None:
    """
    Stores plot data into an HDF5 file along with metadata.
    Args:
        data (dict[str, NDArray]): A dictionary where keys are strings representing
        column names and values are numpy arrays containing the data.
        file_path (str): The path to the HDF5 file where the data will be stored.
        group_path (str): The path within the HDF5 file where the data will be stored.
        metadata (dict[str, Any]): A dictionary containing metadata to be stored with the data.
    Returns:
    None
    """
    pandas_df = pd.DataFrame(data)
    pandas_df.to_hdf(file_path, key=group_path, mode="w")
    with pd.HDFStore(file_path) as store:
        store.get_storer(group_path).attrs.metadata = metadata


def read_plot_data(file_path: str,
                   group_path: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Reads data and metadata from an HDF5 file.
    Args:
        file_path (str): The path to the HDF5 file.
        group_path (str): The path to the group within the HDF5 file.
    Returns:
    tuple[pd.DataFrame, dict[str, Any]]: A tuple containing the data as a
    pandas DataFrame and the metadata as a dictionary.
    """
    with pd.HDFStore(file_path) as store:
        stored_metadata = store.get_storer(group_path).attrs.metadata
        stored_data = store[group_path]
    return stored_data, stored_metadata


def plot_data(data: pd.DataFrame, metadata: dict[str, str]) -> Figure:
    """
    Plots the given data using matplotlib and returns the figure object.
    Args:
        data (pd.DataFrame): A pandas DataFrame containing the data to be plotted. 
                                The first column is assumed to be the x-axis (time) and 
                                the remaining columns are the y-axis values to be plotted.
        metadata (dict[str, str]): A dictionary containing metadata for the plot. 
                                    Expected keys are:
                                    - 'x_label': Label for the x-axis.
                                    - 'x_unit': Unit for the x-axis.
                                    - 'y_label': Label for the y-axis.
                                    - 'y_unit': Unit for the y-axis.
                                    - 'legend_title': Title for the legend.
    Returns:
    Figure: A matplotlib Figure object containing the plot.
    """
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


def publish_plot(fig: Figure,
                 source_paths: str | list[str],
                 destination_path: str) -> None:
    """
    Publishes a plot by tagging it and saving it to a specified destination.
    Args:
        fig (Figure): The figure object to be tagged and published.
        source_paths (str | list[str]): The source path(s) where the plot data is located.
        destination_path (str): The destination path where the tagged plot will be saved.
    Returns:
        None
    """

    tag_plot = tagplot(fig,
                       engine="matplotlib",
                       id_method="time",
                       prefix="“GdD_WS_2425_2808064_“")
    publish(tag_plot, source_paths, destination_path)

if __name__ == "__main__":
    pass
