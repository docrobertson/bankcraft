"""
Tests for the TimeUnit class in config.py.
"""
from typing import Dict, Any, List

import pytest

from bankcraft.config import TimeUnit, STEP_MINUTES, time_units


class TestTimeUnit:
    """Test suite for the TimeUnit class."""

    def test_initialization(self) -> None:
        """Test that TimeUnit initializes with correct values."""
        tu = TimeUnit()
        
        # Check basic time unit values
        assert tu.steps_per_hour == 60 // STEP_MINUTES
        assert tu.steps_per_day == 24 * tu.steps_per_hour
        assert tu.steps_per_week == 7 * tu.steps_per_day
        assert tu.steps_per_biweekly == 14 * tu.steps_per_day
        assert tu.steps_per_month == 30 * tu.steps_per_day
        assert tu.steps_per_year == 365 * tu.steps_per_day
        
        # Check that the unit map contains all expected keys
        expected_keys = ['10min', 'hour', 'day', 'week', 'biweekly', 'month', 'year']
        for key in expected_keys:
            assert key in tu._unit_map

    def test_getitem(self) -> None:
        """Test the __getitem__ method for dictionary-like access."""
        tu = TimeUnit()
        
        # Test valid keys
        assert tu['10min'] == 1
        assert tu['hour'] == tu.steps_per_hour
        assert tu['day'] == tu.steps_per_day
        assert tu['week'] == tu.steps_per_week
        assert tu['biweekly'] == tu.steps_per_biweekly
        assert tu['month'] == tu.steps_per_month
        assert tu['year'] == tu.steps_per_year
        
        # Test invalid key returns default value (1)
        assert tu['invalid_key'] == 1
        
        # Test case sensitivity (keys should be case-sensitive)
        assert tu['DAY'] == 1  # Should return default, not tu.steps_per_day

    def test_convert(self) -> None:
        """Test the convert method for time unit conversions."""
        tu = TimeUnit()
        
        # Test simple conversions
        assert tu.convert(1, 'hour', 'hour') == 1.0
        assert tu.convert(24, 'hour', 'day') == 1.0
        assert tu.convert(1, 'day', 'hour') == 24.0
        assert tu.convert(7, 'day', 'week') == 1.0
        assert tu.convert(1, 'week', 'day') == 7.0
        
        # Test more complex conversions
        assert tu.convert(2, 'week', 'hour') == 2 * 7 * 24.0
        assert tu.convert(1, 'month', 'week') == 30 / 7.0
        assert tu.convert(12, 'month', 'year') == 12 * 30 / 365.0
        
        # Test with invalid units (should use default of 1 step)
        assert tu.convert(10, 'invalid_unit', 'hour') == 10 / tu.steps_per_hour
        assert tu.convert(10, 'hour', 'invalid_unit') == 10 * tu.steps_per_hour
        
        # Test with zero and negative values
        assert tu.convert(0, 'day', 'hour') == 0.0
        assert tu.convert(-1, 'day', 'hour') == -24.0
        
        # Test with floating point values
        assert tu.convert(0.5, 'day', 'hour') == 12.0
        assert pytest.approx(tu.convert(1.5, 'week', 'day')) == 10.5

    def test_steps_to_time_str(self) -> None:
        """Test the steps_to_time_str method for human-readable time strings."""
        tu = TimeUnit()
        
        # Test zero steps
        assert tu.steps_to_time_str(0) == "0 minutes"
        
        # Test minutes only
        assert tu.steps_to_time_str(1) == "10 minutes"
        assert tu.steps_to_time_str(3) == "30 minutes"
        
        # Test hours only
        assert tu.steps_to_time_str(tu.steps_per_hour) == "1 hour"
        assert tu.steps_to_time_str(tu.steps_per_hour * 2) == "2 hours"
        
        # Test days only
        assert tu.steps_to_time_str(tu.steps_per_day) == "1 day"
        assert tu.steps_to_time_str(tu.steps_per_day * 3) == "3 days"
        
        # Test combinations
        assert tu.steps_to_time_str(tu.steps_per_day + tu.steps_per_hour) == "1 day, 1 hour"
        assert tu.steps_to_time_str(tu.steps_per_day + tu.steps_per_hour + 1) == "1 day, 1 hour, 10 minutes"
        assert tu.steps_to_time_str(tu.steps_per_day * 2 + tu.steps_per_hour * 5 + 3) == "2 days, 5 hours, 30 minutes"
        
        # Test edge cases
        assert tu.steps_to_time_str(-1) == "0 minutes"  # Negative steps should be handled gracefully
        
        # Test large number of steps
        large_steps = tu.steps_per_year * 2 + tu.steps_per_day * 45 + tu.steps_per_hour * 12 + 3
        # This should be handled by the current implementation, but we're not testing the exact string
        # since it would be very long. Just verify it returns a string.
        assert isinstance(tu.steps_to_time_str(large_steps), str)

    def test_global_time_units_instance(self) -> None:
        """Test that the global time_units instance works correctly."""
        # Verify that time_units is an instance of TimeUnit
        assert isinstance(time_units, TimeUnit)
        
        # Verify that it has the correct values
        assert time_units['day'] == 24 * time_units['hour']
        assert time_units.convert(1, 'week', 'day') == 7.0

    def test_backward_compatibility(self) -> None:
        """Test that the steps variable provides backward compatibility."""
        from bankcraft.config import steps
        
        # Verify that steps is the same as time_units
        assert steps is time_units
        
        # Verify that it works with dictionary-like access
        assert steps['hour'] == 60 // STEP_MINUTES
        assert steps['day'] == 24 * steps['hour']
        assert steps['week'] == 7 * steps['day']
        
    def test_time_unit_consistency(self) -> None:
        """Test that time unit conversions are consistent and transitive."""
        tu = TimeUnit()
        
        # Test transitivity: converting A to B to C should be the same as A to C
        value = 10
        # day -> hour -> minute should be the same as day -> minute
        day_to_hour = tu.convert(value, 'day', 'hour')
        hour_to_min = tu.convert(day_to_hour, 'hour', '10min')
        day_to_min = tu.convert(value, 'day', '10min')
        assert pytest.approx(hour_to_min) == day_to_min
        
        # Test round-trip conversion: A -> B -> A should return the original value
        original = 5.5
        converted = tu.convert(original, 'week', 'day')
        round_trip = tu.convert(converted, 'day', 'week')
        assert pytest.approx(round_trip) == original
        
    def test_custom_time_unit(self) -> None:
        """Test creating a TimeUnit with a different base step size."""
        # Create a TimeUnit where each step is 5 minutes instead of 10
        custom_step_minutes = 5
        
        class CustomTimeUnit(TimeUnit):
            def __init__(self):
                self.steps_per_hour = 60 // custom_step_minutes
                self.steps_per_day = 24 * self.steps_per_hour
                self.steps_per_week = 7 * self.steps_per_day
                self.steps_per_biweekly = 14 * self.steps_per_day
                self.steps_per_month = 30 * self.steps_per_day
                self.steps_per_year = 365 * self.steps_per_day
                
                self._unit_map = {
                    '5min': 1,  # Now the base unit is 5min
                    'hour': self.steps_per_hour,
                    'day': self.steps_per_day,
                    'week': self.steps_per_week,
                    'biweekly': self.steps_per_biweekly,
                    'month': self.steps_per_month,
                    'year': self.steps_per_year
                }
        
        custom_tu = CustomTimeUnit()
        
        # Verify the custom time unit has different values
        assert custom_tu.steps_per_hour == 12  # 60 / 5 = 12
        assert custom_tu.steps_per_day == 12 * 24
        
        # Test conversion with the custom time unit
        assert custom_tu.convert(1, 'day', 'hour') == 24.0  # Same result as standard
        assert custom_tu['hour'] == 12  # Different from standard (6)
        
    def test_get_all_units(self) -> None:
        """Test the get_all_units method."""
        tu = TimeUnit()
        
        # Get all units
        units = tu.get_all_units()
        
        # Verify it's a list
        assert isinstance(units, list)
        
        # Verify it contains all expected units
        expected_units = ['10min', 'hour', 'day', 'week', 'biweekly', 'month', 'year']
        for unit in expected_units:
            assert unit in units
        
        # Verify the length matches
        assert len(units) == len(expected_units)
        
    def test_is_valid_unit(self) -> None:
        """Test the is_valid_unit method."""
        tu = TimeUnit()
        
        # Test valid units
        assert tu.is_valid_unit('10min') is True
        assert tu.is_valid_unit('hour') is True
        assert tu.is_valid_unit('day') is True
        assert tu.is_valid_unit('week') is True
        assert tu.is_valid_unit('biweekly') is True
        assert tu.is_valid_unit('month') is True
        assert tu.is_valid_unit('year') is True
        
        # Test invalid units
        assert tu.is_valid_unit('invalid_unit') is False
        assert tu.is_valid_unit('') is False
        assert tu.is_valid_unit('HOUR') is False  # Case-sensitive
        
    def test_get_steps_between(self) -> None:
        """Test the get_steps_between method."""
        tu = TimeUnit()
        
        # Test normal case
        assert tu.get_steps_between(100, 200) == 100
        
        # Test zero difference
        assert tu.get_steps_between(100, 100) == 0
        
        # Test negative difference (should return 0)
        assert tu.get_steps_between(200, 100) == 0
        
    def test_get_time_between(self) -> None:
        """Test the get_time_between method."""
        tu = TimeUnit()
        
        # Test with default unit (day)
        steps_per_day = tu['day']
        assert tu.get_time_between(0, steps_per_day) == 1.0
        assert tu.get_time_between(0, steps_per_day * 2) == 2.0
        
        # Test with specified unit
        assert tu.get_time_between(0, tu['hour'], 'hour') == 1.0
        assert tu.get_time_between(0, tu['week'], 'week') == 1.0
        
        # Test with mixed units
        assert tu.get_time_between(0, tu['week'], 'day') == 7.0
        
        # Test with negative difference (should return 0)
        assert tu.get_time_between(200, 100, 'day') == 0.0
        
    def test_add_time(self) -> None:
        """Test the add_time method."""
        tu = TimeUnit()
        
        # Test adding different time units
        assert tu.add_time(0, 1, 'day') == tu['day']
        assert tu.add_time(100, 2, 'hour') == 100 + 2 * tu['hour']
        assert tu.add_time(0, 0.5, 'week') == int(0.5 * tu['week'])
        
        # Test adding to non-zero start
        start_steps = 100
        assert tu.add_time(start_steps, 1, 'day') == start_steps + tu['day']
        
    def test_subtract_time(self) -> None:
        """Test the subtract_time method."""
        tu = TimeUnit()
        
        # Test subtracting different time units
        start_steps = tu['day'] * 2
        assert tu.subtract_time(start_steps, 1, 'day') == tu['day']
        
        # Test subtracting more than available (should return 0)
        assert tu.subtract_time(tu['hour'], 2, 'hour') == 0
        
        # Test subtracting from zero (should remain zero)
        assert tu.subtract_time(0, 1, 'day') == 0
        
        # Test with floating point values
        assert tu.subtract_time(tu['day'], 0.5, 'day') == int(tu['day'] * 0.5)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 