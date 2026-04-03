import os
from functools import cache
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

def logistic_function(x, L, k, x0):
    return L / (1 + np.exp(-k * (x - x0)))

def generate_daily_load_profile(
        l0, 
        peak_params=[{'start_time': 6 * 60, 'duration': 8*60, 'part_load': 0.6}], 
        noise_random_frac_of_l0=None, 
        interval=5, 
        transition_duration=30, 
        transition_smoothness=10.0, 
        random_state=None
    ):
    total_minutes = 24 * 60  # Total minutes in a day
    time_minutes = np.arange(0, total_minutes, interval)
    load_profile = np.full_like(time_minutes, l0, dtype=float)

    for peak in peak_params:
        ti = peak['start_time']
        pi = peak['duration']
        li = peak['part_load']

        ti_index = int(ti / interval)
        yi = li

        transition_up_start_index = ti_index
        transition_up_end_index = transition_up_start_index + int(transition_duration / interval)
        transition_down_start_index = ti_index + int(pi / interval)
        transition_down_end_index = transition_down_start_index + int(transition_duration / interval)

        transition_up_end_index = min(transition_up_end_index, len(time_minutes) - 1)
        transition_down_start_index = min(transition_down_start_index, len(time_minutes) - 1)
        transition_down_end_index = min(transition_down_end_index, len(time_minutes) - 1)

        if transition_up_start_index < len(time_minutes):
            increase_indices = np.arange(transition_up_start_index, transition_up_end_index)
            x_values = (increase_indices - transition_up_start_index) / (transition_up_end_index - transition_up_start_index)
            load_profile[increase_indices] = l0 + (yi - l0) * logistic_function(x_values, 1, transition_smoothness, 0.5)

        if transition_up_end_index < len(time_minutes):
            load_profile[transition_up_end_index:transition_down_start_index] = yi

        if transition_down_start_index < len(time_minutes):
            decrease_indices = np.arange(transition_down_start_index, transition_down_end_index)
            x_values = (decrease_indices - transition_down_start_index) / (transition_down_end_index - transition_down_start_index)
            load_profile[decrease_indices] = yi - (yi - l0) * logistic_function(x_values, 1, transition_smoothness, 0.5)

    if noise_random_frac_of_l0 is not None:
        if random_state is None:
            random_state = np.random.RandomState()

        noise_range = l0 * noise_random_frac_of_l0
        random_variation = random_state.uniform(-noise_range, noise_range, size=len(time_minutes))
        load_profile += random_variation
    
    return load_profile

def generate_yearly_load_profile(l0=0.7, 
                                 weekday_peak_values=[0.7,0.7,0.7], 
                                 weekday_dynamic_range=0.,
                                 weekend_peak_values=[0.7,0.7,0.7], 
                                 weekend_dynamic_range=0., 
                                 interval=60,
                                 weekday_peak_duration=8*60,
                                 weekday_peak_duration_variability=0,
                                 weekend_peak_duration=4*60,
                                 weekend_peak_duration_variability=0,
                                 transition_duration=60,
                                 transition_smoothness=1.0, 
                                 minimum_noise_random_frac_of_l0=0.1,
                                 maximum_noise_random_frac_of_l0=0.1,
                                 weekday_peak_freqs=[0.8, 0.15, 0.05], 
                                 weekend_peak_freqs=[0.1, 0.9, 0.0],
                                 peak_load_possible_weekday_time_range=(6 * 60, 20 * 60),
                                 peak_load_possible_weekend_time_range=(10 * 60, 22 * 60),
                                 random_first_peak_delay_up_to=60,
                                 start_date=datetime(2025, 1, 1),
                                 num_days=365,
                                 us_holidays = {
                                    'New Year\'s Day': datetime(2025, 1, 1),
                                    'Martin Luther King Jr. Day': datetime(2025, 1, 15),
                                    'Washington\'s Birthday': datetime(2025, 2, 18),
                                    'Memorial Day': datetime(2025, 5, 26),
                                    'Independence Day': datetime(2025, 7, 4),
                                    'Labor Day': datetime(2025, 9, 2),
                                    'Columbus Day': datetime(2025, 10, 13),
                                    'Veterans Day': datetime(2025, 11, 11),
                                    'Thanksgiving Day': datetime(2025, 11, 27),
                                    'Christmas Day': datetime(2025, 12, 25)
                                },
                                random_state = None,
                                ):
    if random_state is None:
        random_state = np.random.RandomState()
    
    total_intervals_per_day = 24 * 60 // interval
    yearly_load_profile = np.zeros(num_days * total_intervals_per_day)
    noise_sampling_range = np.zeros(num_days * total_intervals_per_day)

    current_date = start_date
    for day in range(num_days):
        if current_date.weekday() < 5:  # Weekday
            possible_time_range = peak_load_possible_weekday_time_range
            peak_values = weekday_peak_values
            variation_range = weekday_dynamic_range
            peak_freqs = weekday_peak_freqs
            peak_duration = weekday_peak_duration
            peak_duration_variability = weekday_peak_duration_variability
        else:  # Weekend
            possible_time_range = peak_load_possible_weekend_time_range
            peak_values = weekend_peak_values
            variation_range = weekend_dynamic_range
            peak_freqs = weekend_peak_freqs
            peak_duration = weekend_peak_duration
            peak_duration_variability = weekend_peak_duration_variability

        # Check if the current date is a holiday
        if current_date in us_holidays.values():
            possible_time_range = peak_load_possible_weekend_time_range
            peak_values = weekend_peak_values
            variation_range = weekend_dynamic_range
            peak_freqs = weekend_peak_freqs

        # Determine number of peak periods for the day
        num_peaks = random_state.choice([1, 2, 3], p=peak_freqs)

        # Generate peak parameters for the day
        peak_params = []
        for peak_num in range(num_peaks):
            first_peak_start = random_state.uniform(0, random_first_peak_delay_up_to)
            first_peak_start += possible_time_range[0]
            peak_duration_actual = peak_duration * (1 + random_state.uniform(-1 * peak_duration_variability,
                                                                           peak_duration_variability))
            peak_value = peak_values[peak_num % len(peak_values)]
            peak_load_fraction = random_state.uniform(
                peak_value - variation_range * peak_value,
                peak_value + variation_range * peak_value
            )
            peak_params.append({
                'start_time': first_peak_start,
                'duration': peak_duration_actual,
                'part_load': peak_load_fraction
            })

        # Generate daily load profile
        daily_load_profile = generate_daily_load_profile(
            l0, 
            peak_params=peak_params, 
            noise_random_frac_of_l0=None, 
            interval=interval, 
            transition_duration=transition_duration, 
            transition_smoothness=transition_smoothness, 
            random_state=random_state
        )
  
        start_idx = day * total_intervals_per_day
        
        # Add the non-noised load profile to the yearly profile
        yearly_load_profile[start_idx:start_idx + total_intervals_per_day] = daily_load_profile
        
        # Add the noise to the load profile
        noise_range = l0 * random_state.uniform(minimum_noise_random_frac_of_l0, maximum_noise_random_frac_of_l0)
        noise_sampling_range[start_idx:start_idx + total_intervals_per_day] = noise_range

        current_date += timedelta(days=1)

    # Finally do a single sampling of each day's noise and add to the yearly profile
    yearly_load_profile += random_state.uniform(-noise_sampling_range,noise_sampling_range)

    # Create timestamps and formatted string
    total_intervals = num_days * total_intervals_per_day
    timestamps = [start_date + timedelta(minutes=i * interval) for i in range(total_intervals)]
    timestamp_strs = [dt.strftime('%I:%M %p %b %d, %Y') for dt in timestamps]

    # Construct DataFrame
    yearly_profile = pd.DataFrame({
        'timestamp': timestamp_strs,
        'fraction_IT_capacity': yearly_load_profile
    })

    return yearly_profile


@cache
def correct_l0(l0, average_weekday_duration, average_weekend_duration, average_weekday_increase, average_weekend_increase): # durations in hours
    # if the load average is provided as an input instead of the base load

    count_weekdays = 252
    count_weekend_days = 365 - 252 # includes holidays

    # figuring out formula
    # 24 * 365 * l0 = corrected_l0 * (
    #                ((24 - average_weekday_duration) *  + average_weekday_duration * (1+average_weekday_increase)) * count_weekdays + \
    #                ((24 - average_weekend_duration) + average_weekend_duration * (1+average_weekend_increase)) * count_weekend_days)
    
    corrected_l0 = 24 * 365 * l0 / (\
                       ((24 - average_weekday_duration) + average_weekday_duration * (1+average_weekday_increase)) * count_weekdays + \
                       ((24 - average_weekend_duration) + average_weekend_duration * (1+average_weekend_increase)) * count_weekend_days)

    return corrected_l0

def average_hourly_load(it_loads : pd.DataFrame , interval_size: int) -> pd.DataFrame:
    """
    Adjust the time granularity of it load data by averaging over a given 
    interval of minutes to the hour. This granularity will have to match 
    with weather data being used for the analysis.

    Args:
        it_loads (pd.DataFrame):
            The timeseries of IT load data. It's expected here that it 
            has a "timestamp" column representing the point in time.

        interval_size (int):
            The number of intervals per hour that there are.

    Raises:
        ValueError:
            When `time_granularity` is not one of 5, 15, 60.

    Returns:
        pd.DataFrame:
            Aggregated load data, where values of power have been averaged 
            within each given interval. The returned timestamp will be that 
            of the beginning of the interval.
    """    
    # If we just have 1 hour increments already, we can skip this
    if interval_size > 1:
        it_loads['bin'] = it_loads.index // interval_size
        res = it_loads.groupby("bin").mean(numeric_only=True).reset_index(drop = True)
        res["timestamp"] = it_loads.loc[it_loads.index[::interval_size],"timestamp"].reset_index(drop = True)

    return res


def generate_specific_it_load_profiles(
        l0, 
        interval = 15, 
        noise_style="low_noise", 
        diurnal_style="flat",
        random_state = None,
        num_days=365,
        start_date=datetime(2025, 1, 1),
        hourly_averaging=True,
    ):

    if noise_style=="low_noise":
        noise_random_frac_of_l0 = 0.03  # Percentage of l0 as the minimum daily noise
        maximum_noise_random_frac_of_l0 = 0.07  # Maximum daily noise as percentage
    
    elif noise_style=="high_noise": 
        noise_random_frac_of_l0 = 0.12  # Percentage of l0 as the minimum daily noise
        maximum_noise_random_frac_of_l0 = 0.18  # Maximum daily noise as percentage
    
    if diurnal_style=="flat":
        weekday_peak_duration=0.
        weekend_peak_duration=0.
        peak_load_possible_weekday_time_range=(6 * 60, 20 * 60) # not relevant, as the peak is set to l0
        peak_load_possible_weekend_time_range=(10 * 60, 22 * 60) # not relevant, as the peak is set to l0
        weekday_peak_values = [l0,l0,l0]  # Possible peak load fractions for weekdays
        weekday_peak_freqs=[1.,0,0]
        weekend_peak_values = [l0,l0,l0]  # Possible peak load fractions for weekends
        weekend_peak_freqs=[1.,0,0]

        l0_corrected = l0 + 0. # remains the same as there is no diurnal pattern
    
    elif diurnal_style=="business_diurnal":
        weekday_peak_duration=9*60
        weekend_peak_duration=0.
        
        peak_load_possible_weekday_time_range=(8 * 60, 17 * 60)
        peak_load_possible_weekend_time_range=(16 * 60, 21 * 60) # not relevant, as we keep weekend flat
        weekday_peak_values = [1.1*l0,l0,l0]  # Possible peak load fractions for weekdays
        weekday_peak_freqs=[1.,0,0]
        weekend_peak_values = [l0,l0,l0]  # Possible peak load fractions for weekends
        weekend_peak_freqs=[1.,0,0]

        average_weekday_duration = (peak_load_possible_weekday_time_range[1] - peak_load_possible_weekday_time_range[0])/60
        average_weekend_duration = (peak_load_possible_weekend_time_range[1] - peak_load_possible_weekend_time_range[0])/60
        average_weekday_increase = (np.array(weekday_peak_values) * np.array(weekday_peak_freqs)).sum() - l0
        average_weekend_increase = (np.array(weekend_peak_values) * np.array(weekend_peak_freqs)).sum() - l0

        l0_corrected = correct_l0(l0, average_weekday_duration, average_weekend_duration, average_weekday_increase, average_weekend_increase)
    
    elif diurnal_style=="business_high_diurnal":
        weekday_peak_duration=9*60
        weekend_peak_duration=0.
        
        peak_load_possible_weekday_time_range=(8 * 60, 17 * 60)
        peak_load_possible_weekend_time_range=(16 * 60, 21 * 60) # not relevant, as we keep weekend flat
        weekday_peak_values = [1.35*l0,l0,l0]  # Possible peak load fractions for weekdays
        weekday_peak_freqs=[1.,0,0]
        weekend_peak_values = [l0,l0,l0]  # Possible peak load fractions for weekends
        weekend_peak_freqs=[1.,0,0]

        average_weekday_duration = (peak_load_possible_weekday_time_range[1] - peak_load_possible_weekday_time_range[0])/60
        average_weekend_duration = (peak_load_possible_weekend_time_range[1] - peak_load_possible_weekend_time_range[0])/60
        average_weekday_increase = (np.array(weekday_peak_values) * np.array(weekday_peak_freqs)).sum() - l0
        average_weekend_increase = (np.array(weekend_peak_values) * np.array(weekend_peak_freqs)).sum() - l0

        l0_corrected = correct_l0(l0, average_weekday_duration, average_weekend_duration, average_weekday_increase, average_weekend_increase)

    elif diurnal_style=="customer_diurnal":
        weekday_peak_duration=5*60
        weekend_peak_duration=5*60
        
        peak_load_possible_weekday_time_range=(16 * 60, 21 * 60)
        peak_load_possible_weekend_time_range=(16 * 60, 21 * 60)
        weekday_peak_values = [1.1*l0,l0,l0]  # Possible peak load fractions for weekdays
        weekday_peak_freqs=[1.,0,0] # just one peak level
        weekend_peak_values = [1.1*l0,l0,l0]  # Possible peak load fractions for weekends
        weekend_peak_freqs=[1.,0,0]

        average_weekday_duration = (peak_load_possible_weekday_time_range[1] - peak_load_possible_weekday_time_range[0])/60
        average_weekend_duration = (peak_load_possible_weekend_time_range[1] - peak_load_possible_weekend_time_range[0])/60
        average_weekday_increase = (np.array(weekday_peak_values) * np.array(weekday_peak_freqs)).sum() - l0
        average_weekend_increase = (np.array(weekend_peak_values) * np.array(weekend_peak_freqs)).sum() - l0

        l0_corrected = correct_l0(l0, average_weekday_duration, average_weekend_duration, average_weekday_increase, average_weekend_increase)

    elif diurnal_style=="customer_high_diurnal":
        weekday_peak_duration=5*60
        weekend_peak_duration=5*60
        
        peak_load_possible_weekday_time_range=(16 * 60, 21 * 60)
        peak_load_possible_weekend_time_range=(16 * 60, 21 * 60)
        weekday_peak_values = [1.35*l0,l0,l0]  # Possible peak load fractions for weekdays
        weekday_peak_freqs=[1.,0,0] # just one peak level
        weekend_peak_values = [1.35*l0,l0,l0]  # Possible peak load fractions for weekends
        weekend_peak_freqs=[1.,0,0]

        average_weekday_duration = (peak_load_possible_weekday_time_range[1] - peak_load_possible_weekday_time_range[0])/60
        average_weekend_duration = (peak_load_possible_weekend_time_range[1] - peak_load_possible_weekend_time_range[0])/60
        average_weekday_increase = (np.array(weekday_peak_values) * np.array(weekday_peak_freqs)).sum() - l0
        average_weekend_increase = (np.array(weekend_peak_values) * np.array(weekend_peak_freqs)).sum() - l0

        l0_corrected = correct_l0(l0, average_weekday_duration, average_weekend_duration, average_weekday_increase, average_weekend_increase)
    
    weekday_dynamic_range = 0.05  # Variation range for weekday peak loads
    weekend_dynamic_range = 0.05  # Variation range for weekend peak loads
    
    transition_duration = 60  # Transition duration in minutes
    transition_smoothness = 10.0  # Steepness of the logistic transition
    
    random_first_peak_delay_up_to=0*60
    
    # Generate yearly load profile
    yearly_load_profile_for_power_components = generate_yearly_load_profile(
        l0=l0_corrected,
        weekday_peak_duration=weekday_peak_duration,
        weekday_peak_duration_variability=0,
        weekend_peak_duration=weekend_peak_duration,
        weekend_peak_duration_variability=0,
        peak_load_possible_weekday_time_range=peak_load_possible_weekday_time_range,
        peak_load_possible_weekend_time_range=peak_load_possible_weekend_time_range,
        weekday_peak_values=weekday_peak_values,
        weekday_peak_freqs=weekday_peak_freqs,
        weekday_dynamic_range=weekday_dynamic_range,
        weekend_peak_values=weekend_peak_values,
        weekend_peak_freqs=weekend_peak_freqs,
        weekend_dynamic_range=weekend_dynamic_range,
        transition_duration=transition_duration,
        transition_smoothness=transition_smoothness,
        minimum_noise_random_frac_of_l0=noise_random_frac_of_l0,
        interval=interval,
        maximum_noise_random_frac_of_l0=maximum_noise_random_frac_of_l0,
        random_first_peak_delay_up_to=random_first_peak_delay_up_to,
        start_date=start_date,
        num_days=num_days,
        random_state=random_state
    )

    # points_per_hr = number of intervals per hour
    points_per_hr = len(yearly_load_profile_for_power_components) / (24*num_days)
    if (points_per_hr - np.floor(points_per_hr)) > 0: 
        raise ValueError("your data is not easily divisible into hour increments. 5, 15 or 60 minute intervals are recommended.")
    
    if interval != 60 and hourly_averaging==True:
        yearly_load_profile_for_power_components = average_hourly_load(yearly_load_profile_for_power_components,int(points_per_hr))

    result = {'yearly_load_profile_for_power_components':yearly_load_profile_for_power_components, 'l0': l0_corrected}

    return result

def create_power_components_dataset(yearly_itload_profile, fractional_itload_components, flat_loads_as_percent_of_itcapacity, itload_following_load_efficiencies, file_name=None, save=False):

    power_components = pd.DataFrame()
    power_components['timestamp'] = yearly_itload_profile['timestamp'].copy() 
    
    power_components['it_load_total'] = yearly_itload_profile['fraction_IT_capacity'].copy()
    
    for key in fractional_itload_components.keys():
        power_components[key] = fractional_itload_components[key] * power_components['it_load_total']
    
    for key in flat_loads_as_percent_of_itcapacity.keys():
        power_components[key] = flat_loads_as_percent_of_itcapacity[key]
    
    for key in itload_following_load_efficiencies.keys():
        power_components[key] = (itload_following_load_efficiencies[key] - 1) * power_components['it_load_total']
    
    power_components['total'] = power_components.iloc[:,2:].sum(axis=1)

    if save:
        if not os.path.isdir("power_components_database"):
            os.mkdir("power_components_database")
        power_components.to_excel(os.path.join("power_components_database", file_name), index = False)

    return power_components