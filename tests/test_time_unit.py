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
        assert tu.steps_per_month == int(30.436875 * tu.steps_per_day)
        assert tu.steps_per_year == int(365.2425 * tu.steps_per_day)
        
        # Check that the unit map contains all expected keys
        expected_keys = ['10min', 'hour', 'day', 'week', 'biweekly', 'month', 'year']
        for key in expected_keys:
            assert key in tu._unit_map
            
        # Check month days dictionary
        assert len(tu._month_days) == 13  # 12 months + february_leap
        assert tu._month_days['february'] == 28
        assert tu._month_days['february_leap'] == 29

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
        assert pytest.approx(tu.convert(1, 'month', 'week'), 0.01) == 30.436875 / 7.0
        assert pytest.approx(tu.convert(12, 'month', 'year'), 0.01) == 12 * 30.436875 / 365.2425
        
        # Test month and year conversions
        assert pytest.approx(tu.convert(1, 'year', 'month'), 0.01) == 12.0
        assert pytest.approx(tu.convert(1, 'year', 'day'), 0.01) == 365.2425
        assert pytest.approx(tu.convert(1, 'month', 'day'), 0.01) == 30.436875
        
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
        
        # Test months only
        assert tu.steps_to_time_str(tu.steps_per_month) == "1 month"
        assert tu.steps_to_time_str(tu.steps_per_month * 2) == "2 months"
        
        # Test years only
        assert tu.steps_to_time_str(tu.steps_per_year) == "1 year"
        assert tu.steps_to_time_str(tu.steps_per_year * 5) == "5 years"
        
        # Test combinations
        assert tu.steps_to_time_str(tu.steps_per_day + tu.steps_per_hour) == "1 day, 1 hour"
        assert tu.steps_to_time_str(tu.steps_per_day + tu.steps_per_hour + 1) == "1 day, 1 hour, 10 minutes"
        assert tu.steps_to_time_str(tu.steps_per_day * 2 + tu.steps_per_hour * 5 + 3) == "2 days, 5 hours, 30 minutes"
        assert tu.steps_to_time_str(tu.steps_per_year + tu.steps_per_month + tu.steps_per_day) == "1 year, 1 month, 1 day"
        
        # Test edge cases
        assert tu.steps_to_time_str(-1) == "0 minutes"  # Negative steps should be handled gracefully
        
        # Test large number of steps
        large_steps = tu.steps_per_year * 2 + tu.steps_per_month * 3 + tu.steps_per_day * 15 + tu.steps_per_hour * 12 + 3
        time_str = tu.steps_to_time_str(large_steps)
        assert "2 years" in time_str
        assert "3 months" in time_str
        assert "15 days" in time_str
        assert "12 hours" in time_str
        assert "30 minutes" in time_str

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
        
        # Test month -> day -> hour should be the same as month -> hour
        month_to_day = tu.convert(value, 'month', 'day')
        day_to_hour = tu.convert(month_to_day, 'day', 'hour')
        month_to_hour = tu.convert(value, 'month', 'hour')
        assert pytest.approx(day_to_hour) == month_to_hour
        
        # Test year -> month -> day should be the same as year -> day
        year_to_month = tu.convert(value, 'year', 'month')
        month_to_day = tu.convert(year_to_month, 'month', 'day')
        year_to_day = tu.convert(value, 'year', 'day')
        assert pytest.approx(month_to_day) == year_to_day
        
        # Test round-trip conversion: A -> B -> A should return the original value
        original = 5.5
        converted = tu.convert(original, 'week', 'day')
        round_trip = tu.convert(converted, 'day', 'week')
        assert pytest.approx(round_trip) == original
        
        # Test round-trip for months and years
        original = 3.25
        converted = tu.convert(original, 'year', 'month')
        round_trip = tu.convert(converted, 'month', 'year')
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
                self.steps_per_month = int(30.436875 * self.steps_per_day)
                self.steps_per_year = int(365.2425 * self.steps_per_day)
                
                self._unit_map = {
                    '5min': 1,  # Now the base unit is 5min
                    'hour': self.steps_per_hour,
                    'day': self.steps_per_day,
                    'week': self.steps_per_week,
                    'biweekly': self.steps_per_biweekly,
                    'month': self.steps_per_month,
                    'year': self.steps_per_year
                }
                
                # Month lengths for specific month calculations
                self._month_days = {
                    'january': 31,
                    'february': 28,  # Non-leap year
                    'february_leap': 29,  # Leap year
                    'march': 31,
                    'april': 30,
                    'may': 31,
                    'june': 30,
                    'july': 31,
                    'august': 31,
                    'september': 30,
                    'october': 31,
                    'november': 30,
                    'december': 31
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
        
        # Test with month and year units
        assert tu.get_time_between(0, tu['month'], 'month') == 1.0
        assert tu.get_time_between(0, tu['year'], 'year') == 1.0
        
        # Test with mixed units
        assert tu.get_time_between(0, tu['week'], 'day') == 7.0
        assert pytest.approx(tu.get_time_between(0, tu['month'], 'day'), 0.01) == 30.436875
        assert pytest.approx(tu.get_time_between(0, tu['year'], 'month'), 0.01) == 12.0
        
        # Test with negative difference (should return 0)
        assert tu.get_time_between(200, 100, 'day') == 0.0
        
    def test_add_time(self) -> None:
        """Test the add_time method."""
        tu = TimeUnit()
        
        # Test adding different time units
        assert tu.add_time(0, 1, 'hour') == tu['hour']
        assert tu.add_time(0, 1, 'day') == tu['day']
        assert tu.add_time(0, 1, 'week') == tu['week']
        assert tu.add_time(0, 1, 'month') == tu['month']
        assert tu.add_time(0, 1, 'year') == tu['year']
        
        # Test adding to existing steps
        assert tu.add_time(100, 2, 'day') == 100 + 2 * tu['day']
        
    def test_subtract_time(self) -> None:
        """Test the subtract_time method."""
        tu = TimeUnit()
        
        # Test subtracting different time units
        assert tu.subtract_time(tu['hour'], 1, 'hour') == 0
        assert tu.subtract_time(tu['day'], 1, 'day') == 0
        assert tu.subtract_time(tu['week'], 1, 'week') == 0
        assert tu.subtract_time(tu['month'], 1, 'month') == 0
        assert tu.subtract_time(tu['year'], 1, 'year') == 0
        
        # Test subtracting from existing steps
        start_steps = 1000 + tu['day']
        assert tu.subtract_time(start_steps, 1, 'day') == 1000
        
        # Test subtracting more than available (should return 0)
        assert tu.subtract_time(tu['day'], 2, 'day') == 0
        
    def test_parse_time_str(self):
        """Test the parse_time_str method."""
        # Test basic parsing
        assert time_units.parse_time_str("1 day") == (0, 0, 1, 0, 0)
        assert time_units.parse_time_str("2 hours") == (0, 0, 0, 2, 0)
        assert time_units.parse_time_str("30 minutes") == (0, 0, 0, 0, 30)
        assert time_units.parse_time_str("1 year") == (1, 0, 0, 0, 0)
        assert time_units.parse_time_str("3 months") == (0, 3, 0, 0, 0)
        
        # Test compound time strings
        assert time_units.parse_time_str("1 day, 2 hours") == (0, 0, 1, 2, 0)
        assert time_units.parse_time_str("2 days, 3 hours, 30 minutes") == (0, 0, 2, 3, 30)
        assert time_units.parse_time_str("1 year, 2 months, 3 days") == (1, 2, 3, 0, 0)
        assert time_units.parse_time_str("2 years, 3 months, 4 days, 5 hours, 6 minutes") == (2, 3, 4, 5, 6)
        
        # Test whitespace handling
        assert time_units.parse_time_str("  1 day  ,  2 hours  ") == (0, 0, 1, 2, 0)
        
        # Test empty string
        assert time_units.parse_time_str("") == (0, 0, 0, 0, 0)
        
        # Test invalid formats
        with pytest.raises(ValueError):
            time_units.parse_time_str("1 invalid_unit")
            
        with pytest.raises(ValueError):
            time_units.parse_time_str("not_a_number day")
            
    def test_time_str_to_steps(self):
        """Test the time_str_to_steps method."""
        # Test basic conversions
        assert time_units.time_str_to_steps("1 hour") == time_units['hour']
        assert time_units.time_str_to_steps("2 days") == 2 * time_units['day']
        assert time_units.time_str_to_steps("1 month") == time_units['month']
        assert time_units.time_str_to_steps("1 year") == time_units['year']
        
        # Test compound time strings
        assert time_units.time_str_to_steps("1 day, 2 hours") == time_units['day'] + 2 * time_units['hour']
        assert time_units.time_str_to_steps("2 days, 3 hours, 30 minutes") == (
            2 * time_units['day'] + 3 * time_units['hour'] + 3  # 30 minutes = 3 steps
        )
        assert time_units.time_str_to_steps("1 year, 2 months, 3 days") == (
            time_units['year'] + 2 * time_units['month'] + 3 * time_units['day']
        )
        
        # Test empty string
        assert time_units.time_str_to_steps("") == 0
        
        # Test invalid formats
        with pytest.raises(ValueError):
            time_units.time_str_to_steps("1 invalid_unit")
            
    def test_month_year_conversions(self):
        """Test specific month and year conversions."""
        # Test month to days conversion
        assert pytest.approx(time_units.convert(1, 'month', 'day'), 0.01) == 30.436875
        
        # Test year to days conversion
        assert pytest.approx(time_units.convert(1, 'year', 'day'), 0.01) == 365.2425
        
        # Test year to months conversion
        assert pytest.approx(time_units.convert(1, 'year', 'month'), 0.01) == 12.0
        
        # Test multiple months to days
        assert pytest.approx(time_units.convert(3, 'month', 'day'), 0.01) == 3 * 30.436875
        
        # Test fractional months
        assert pytest.approx(time_units.convert(0.5, 'month', 'day'), 0.01) == 0.5 * 30.436875
        
        # Test fractional years
        assert pytest.approx(time_units.convert(0.25, 'year', 'month'), 0.01) == 3.0
        assert pytest.approx(time_units.convert(0.25, 'year', 'day'), 0.01) == 0.25 * 365.2425


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 