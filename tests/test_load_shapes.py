from datetime import datetime
from unittest import TestCase

import numpy as np

from shape_maker.load_shapes import generate_yearly_load_profile


class YearlyLoadProfileTest(TestCase):
    def test_weekday_holiday_uses_weekend_peak_duration_and_variability(self):
        options = {
            "l0": 0.4,
            "interval": 5,
            "weekday_peak_values": [0.9] * 3,
            "weekend_peak_values": [0.9] * 3,
            "weekday_peak_freqs": [1, 0, 0],
            "weekend_peak_freqs": [1, 0, 0],
            "weekday_peak_duration": 480,
            "weekday_peak_duration_variability": 0.5,
            "weekend_peak_duration": 240,
            "weekend_peak_duration_variability": 0,
            "transition_duration": 0,
            "minimum_noise_random_frac_of_l0": 0,
            "maximum_noise_random_frac_of_l0": 0,
            "random_first_peak_delay_up_to": 0,
            "num_days": 1,
        }
        dates = {
            "weekday_holiday": datetime(2025, 1, 1),
            "weekday": datetime(2025, 1, 2),
            "weekend": datetime(2025, 1, 4),
        }
        profiles = {}
        for label, start_date in dates.items():
            profile = generate_yearly_load_profile(
                start_date=start_date,
                random_state=np.random.RandomState(0),
                **options,
            )
            profiles[label] = profile["fraction_IT_capacity"].to_numpy()

        np.testing.assert_array_equal(profiles["weekday_holiday"], profiles["weekend"])
        weekend_peak_samples = np.count_nonzero(profiles["weekend"] > options["l0"])
        self.assertEqual(weekend_peak_samples, 48)
        self.assertGreater(np.count_nonzero(profiles["weekday"] > options["l0"]), weekend_peak_samples)
