import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timedelta
# Import the necessaries libraries
import plotly.graph_objects as go
import datetime as dt
from matplotlib.dates import DateFormatter
from matplotlib.ticker import FixedLocator, FixedFormatter


def plot_yearly_load_profile(
    yearly_profile,
    start_day_of_year=1,
    number_of_days=365,
    save_path=None,
    holidays={
        'New Year\'s Day': dt.datetime(2025, 1, 1),
        'Martin Luther King Jr. Day': dt.datetime(2025, 1, 15),
        'Washington\'s Birthday': dt.datetime(2025, 2, 18),
        'Memorial Day': dt.datetime(2025, 5, 26),
        'Independence Day': dt.datetime(2025, 7, 4),
        'Labor Day': dt.datetime(2025, 9, 2),
        'Columbus Day': dt.datetime(2025, 10, 13),
        'Veterans Day': dt.datetime(2025, 11, 11),
        'Thanksgiving Day': dt.datetime(2025, 11, 27),
        'Christmas Day': dt.datetime(2025, 12, 25)
    }
):
    """
    Plots a segment of the yearly load profile from a DataFrame with timestamps.
    Ticks are placed at 6 AM and 6 PM daily. Weekends and specified holidays are shaded.

    Parameters:
        yearly_profile (pd.DataFrame): Must contain 'timestamp' and 'fraction_IT_capacity' columns.
        start_day_of_year (int): Day of the year to start plotting from (1-based).
        number_of_days (int): Number of days to plot from the start day.
        save_path (str or None): If provided, saves the figure to this file path.
        holidays (dict): Dict of holiday names to datetime.datetime objects.
    """
    timestamp_format = '%I:%M %p %b %d, %Y'

    # Convert timestamps
    if isinstance(yearly_profile['timestamp'].iloc[0], str):
        timestamps = pd.to_datetime(yearly_profile['timestamp'], format=timestamp_format)
    else:
        timestamps = pd.to_datetime(yearly_profile['timestamp'])

    yearly_profile = yearly_profile.copy()
    yearly_profile['timestamp_dt'] = timestamps

    # Filter for plotting range
    year = timestamps.dt.year.iloc[0]
    start_date = dt.datetime(year, 1, 1) + dt.timedelta(days=start_day_of_year - 1)
    end_date = start_date + dt.timedelta(days=number_of_days)
    mask = (timestamps >= start_date) & (timestamps < end_date)
    sliced = yearly_profile.loc[mask]

    # Prepare tick positions and labels
    tick_positions = []
    tick_labels = []
    for day_offset in range(number_of_days):
        for hour in [6, 18]:  # 6 AM and 6 PM
            tick_time = start_date + dt.timedelta(days=day_offset, hours=hour)
            if sliced['timestamp_dt'].iloc[0] <= tick_time <= sliced['timestamp_dt'].iloc[-1]:
                tick_positions.append(tick_time)
                tick_labels.append(tick_time.strftime('%a %I %p %b %d'))

    # Plot
    fig, ax = plt.subplots(figsize=(18, 8))
    ax.plot(
        sliced['timestamp_dt'],
        sliced['fraction_IT_capacity'],
        label=f'Load profile: Days {start_day_of_year}–{start_day_of_year + number_of_days - 1} ({year})'
    )
    ax.set_xlabel('Date & Time', fontsize=18)
    ax.set_ylabel('Fraction IT capacity', fontsize=18)
    ax.grid(True)
    ax.legend(fontsize=18)
    ax.set_ylim(0, 1)

    # Shade weekends and holidays
    holiday_dates = set([d.date() for d in holidays.values()])
    unique_days = sliced['timestamp_dt'].dt.floor('D').unique()
    for day_start in unique_days:
        day_end = day_start + dt.timedelta(days=1)
        if day_start.weekday() >= 5 or day_start.date() in holiday_dates:
            ax.axvspan(day_start, day_end, color='lightgray', alpha=0.4)

    # Set x-ticks
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=18)
    ax.tick_params(axis='y', labelsize=18)

    # Clean up y-axis labels
    y_labels = [f"{tick:.2f}".rstrip('0').rstrip('.') for tick in ax.get_yticks()]
    ax.set_yticklabels(y_labels, fontsize=18)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight')
        plt.close()
    else:
        plt.show()


def browseable_plot_yearly_load_profile(yearly_load_profile, start_date, interval=15):
    total_intervals_per_day = 24 * 60 // interval
    num_days = len(yearly_load_profile) // total_intervals_per_day

    # Create time array in minutes
    time_minutes = np.arange(0, num_days * 24 * 60, interval)

    # Convert time_minutes to datetime objects
    time_datetime = [start_date + timedelta(minutes=int(t)) for t in time_minutes]

    # Extract days of the week (first three letters)
    days_of_week = [dt.strftime('%a') for dt in time_datetime]

    # Create unique days of the week for annotations
    unique_days = list(set(days_of_week))
    unique_days.sort(key=lambda day: days_of_week.index(day))

    # Create Plotly figure
    fig = go.Figure(data=go.Scatter(x=time_datetime, y=yearly_load_profile, mode='lines', name='Load Profile'))

    # Add annotations for days of the week
    annotations = []
    for i, day in enumerate(days_of_week):
        if i == 0 or days_of_week[i] != days_of_week[i - 1]:  # Only annotate when the day changes
            annotations.append(
                dict(
                    x=time_datetime[i],
                    y=1.05,  # Position slightly above the plot
                    text=day,
                    showarrow=False,
                    font=dict(size=12, color="black"),
                    xref="x",
                    yref="paper",
                    textangle=-90  # Rotate text vertically
                )
            )

    fig.update_layout(
        title='Yearly Load Profile',
        xaxis_title='Date and Time',
        yaxis_title='Load Fraction',
        xaxis=dict(rangeslider_visible=True),
        yaxis=dict(range=[0, 1]),
        height=600,
        width=1200,
        annotations=annotations
    )

    # Set the default renderer for Plotly
    import plotly.io as pio
    pio.renderers.default = 'notebook_connected'  # Change to 'colab' if using Google Colab

    fig.show()


def plot_monthly_average_load_profiles(yearly_load_profile, interval=15, save_dir='./monthly_plots/'):
    # Create directory to save plots if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Constants
    total_intervals_per_day = 24 * 60 // interval
    num_days = len(yearly_load_profile) // total_intervals_per_day

    # Convert yearly load profile to a 2D array (days x intervals_per_day)
    load_profiles = np.array(yearly_load_profile).reshape(num_days, total_intervals_per_day)

    # Define months
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]

    # Initialize dictionaries to store weekday and weekend load profiles for each month
    monthly_weekday_profiles = {month: [] for month in months}
    monthly_weekend_profiles = {month: [] for month in months}

    # Iterate through each day and categorize by month and day type
    current_date = datetime(2025, 1, 1)
    for day in range(num_days):
        month_name = current_date.strftime("%B")
        if current_date.weekday() < 5:  # Weekday
            monthly_weekday_profiles[month_name].append(load_profiles[day])
        else:  # Weekend
            monthly_weekend_profiles[month_name].append(load_profiles[day])

        # Move to the next day
        current_date += timedelta(days=1)

    # Create a 3x4 grid of subplots
    fig, axes = plt.subplots(4, 3, figsize=(24, 24))
    axes = axes.flatten()

    # Convert time from intervals to hours for plotting
    time_hours = np.arange(0, 24, interval / 60)

    # Plot each month
    for i, month in enumerate(months):
        ax = axes[i]

        # Plot each day's load profile for weekdays
        if monthly_weekday_profiles[month]:
            for profile in monthly_weekday_profiles[month]:
                ax.plot(time_hours, profile, color='gray', alpha=0.2)

            # Calculate average weekday load profile
            avg_weekday_profile = np.mean(monthly_weekday_profiles[month], axis=0)
            ax.plot(time_hours, avg_weekday_profile, color='blue', linewidth=2, label='Average Weekday')

        # Plot each day's load profile for weekends
        if monthly_weekend_profiles[month]:
            for profile in monthly_weekend_profiles[month]:
                ax.plot(time_hours, profile, color='gray', alpha=0.2)

            # Calculate average weekend load profile
            avg_weekend_profile = np.mean(monthly_weekend_profiles[month], axis=0)
            ax.plot(time_hours, avg_weekend_profile, color='red', linewidth=2, label='Average Weekend')

        ax.set_xlabel('Time (hours)')
        ax.set_ylabel('Load Fraction')
        ax.set_title(f'{month} 2025')
        ax.grid(True)
        ax.legend()
        ax.set_ylim(0, 1)  # Set y-axis limit to [0, 1]

        # Add ticks for each hour
        ax.set_xticks(np.arange(0, 25, 1))
        ax.set_xticklabels([f"{int(t)}" for t in np.arange(0, 25, 1)])

    # Remove empty subplots
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    # Save the combined plot as a PNG file
    save_path = os.path.join(save_dir, '2025_monthly_load_profiles.png')
    plt.tight_layout()
    # plt.savefig(save_path, bbox_inches='tight')
    # plt.close(fig)
    plt.show()


def plot_power_components(power_components, save=False, start_day_of_year=100, number_of_days=1):
    # Convert timestamp to datetime if needed
    power_components["timestamp"] = pd.to_datetime(power_components["timestamp"])

    # Extract the year (assumes all data is from one year)
    year = power_components["timestamp"].dt.year.min()

    # Build the date range from day-of-year
    start_date = pd.Timestamp(f"{year}-01-01") + pd.Timedelta(days=start_day_of_year - 1)
    end_date = start_date + pd.Timedelta(days=number_of_days)

    # Filter the dataframe
    df_filtered = power_components[
        (power_components["timestamp"] >= start_date) &
        (power_components["timestamp"] < end_date)
    ]

    # Select columns to plot (preserving order)
    columns_to_plot = [
        col for col in power_components.columns
        if col != "timestamp" and "total" not in col.lower()
    ]

    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    df_filtered.set_index("timestamp")[columns_to_plot].plot(
        kind="area", stacked=True, ax=ax, alpha=0.9, colormap='tab20'
    )

    # Format ticks
    plt.xticks(rotation=45)
    ax.set_title(f"Stacked Power Components: Day {start_day_of_year} to {start_day_of_year + number_of_days - 1}")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Fraction IT capacity")
    plt.tight_layout()
    plt.show()

    if save:
        fig.savefig("feedback_img/power_components_one_day_plot.png", format="png", dpi=300, bbox_inches="tight")