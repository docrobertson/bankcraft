hunger_rate = 0.3  # threshold * 3 * (1/step['day'])
fatigue_rate = 0.2  # threshold * 3 * (1/step['day'])* 0.5
social_rate = 0.1
consumerism_rate = 0.03
work_rate = 0.1
motivation_threshold = 20

# Time constants - each simulation step represents 10 minutes
STEP_MINUTES = 10

class TimeUnit:
    """Class for handling time unit conversions in the simulation.
    
    The TimeUnit class provides methods for converting between different time units
    and calculating how many simulation steps each time unit represents. It replaces
    the previous dictionary-based approach with a more robust object-oriented solution
    while maintaining backward compatibility.
    
    Each simulation step represents 10 minutes of simulated time.
    
    Available time units:
    - '10min': 1 step (base unit)
    - 'hour': 6 steps
    - 'day': 144 steps
    - 'week': 1008 steps
    - 'biweekly': 2016 steps
    - 'month': 4320 steps (30 days)
    - 'year': 52560 steps (365 days)
    
    Examples:
        >>> from bankcraft.config import time_units
        >>> time_units.convert(1, 'day', 'hour')  # Convert 1 day to hours
        24.0
        >>> time_units['week']  # Get steps per week
        1008
        >>> time_units.steps_to_time_str(150)  # Human-readable time
        '1 day, 1 hour'
    
    For full documentation, see docs/time_unit.md
    """
    
    def __init__(self):
        """Initialize the TimeUnit with standard time periods."""
        self.steps_per_hour = 60 // STEP_MINUTES  # 6 steps per hour
        self.steps_per_day = 24 * self.steps_per_hour  # 144 steps per day
        self.steps_per_week = 7 * self.steps_per_day  # 1008 steps per week
        self.steps_per_biweekly = 14 * self.steps_per_day  # 2016 steps per two weeks
        
        # More accurate month and year calculations
        # Standard month (30.436875 days - average days per month in a year)
        self.steps_per_month = int(30.436875 * self.steps_per_day)  # ~4383 steps per month
        
        # Standard year (365.2425 days - accounts for leap years)
        self.steps_per_year = int(365.2425 * self.steps_per_day)  # ~52595 steps per year
        
        # Dictionary mapping time unit names to their step values
        self._unit_map = {
            '10min': 1,
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
    
    def __getitem__(self, key):
        """Allow dictionary-like access to time units."""
        return self._unit_map.get(key, 1)  # Default to 1 step (10 minutes)
    
    def convert(self, value, from_unit, to_unit):
        """Convert a value from one time unit to another.
        
        Args:
            value: The value to convert
            from_unit: The source time unit (e.g., 'day')
            to_unit: The target time unit (e.g., 'hour')
            
        Returns:
            The converted value
        """
        steps = value * self[from_unit]
        return steps / self[to_unit]
    
    def steps_to_time_str(self, steps):
        """Convert a number of steps to a human-readable time string.
        
        Args:
            steps: Number of simulation steps
            
        Returns:
            A string representation of the time (e.g., "2 days, 4 hours")
        """
        # Handle negative steps
        if steps < 0:
            return "0 minutes"
            
        # Calculate years, months, days, hours, minutes
        years = 0
        months = 0
        
        # First extract years if significant
        if steps >= self.steps_per_year:
            years = steps // self.steps_per_year
            steps = steps % self.steps_per_year
        
        # Then extract months if significant
        if steps >= self.steps_per_month:
            months = steps // self.steps_per_month
            steps = steps % self.steps_per_month
        
        # Calculate days, hours, minutes
        days = steps // self.steps_per_day
        remaining = steps % self.steps_per_day
        hours = remaining // self.steps_per_hour
        remaining = remaining % self.steps_per_hour
        minutes = (remaining * STEP_MINUTES)
        
        parts = []
        if years > 0:
            parts.append(f"{years} year{'s' if years != 1 else ''}")
        if months > 0:
            parts.append(f"{months} month{'s' if months != 1 else ''}")
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
            
        return ", ".join(parts) if parts else "0 minutes"
    
    def parse_time_str(self, time_str):
        """Parse a time string into years, months, days, hours, and minutes.
        
        Args:
            time_str: A string representation of time (e.g., "2 days, 4 hours, 30 minutes")
            
        Returns:
            A tuple of (years, months, days, hours, minutes)
            
        Raises:
            ValueError: If the time string format is invalid
        """
        years, months, days, hours, minutes = 0, 0, 0, 0, 0
        
        # Handle empty string
        if not time_str or time_str.strip() == "":
            return (years, months, days, hours, minutes)
        
        # Split by commas and process each part
        parts = [part.strip() for part in time_str.split(",")]
        
        for part in parts:
            if not part:
                continue
            
            # Split into value and unit
            try:
                value_str, unit = part.strip().split(" ", 1)
                value = int(value_str)
            except ValueError:
                raise ValueError(f"Invalid time format: {part}")
            
            # Normalize unit (remove trailing 's' if plural)
            unit = unit.lower()
            if unit.endswith('s'):
                unit = unit[:-1]
            
            # Assign to appropriate variable
            if unit == "year":
                years = value
            elif unit == "month":
                months = value
            elif unit == "day":
                days = value
            elif unit == "hour":
                hours = value
            elif unit == "minute":
                minutes = value
            else:
                raise ValueError(f"Unknown time unit: {unit}")
        
        return (years, months, days, hours, minutes)
    
    def time_str_to_steps(self, time_str):
        """Convert a time string to simulation steps.
        
        Args:
            time_str: A string representation of time (e.g., "2 days, 4 hours, 30 minutes")
            
        Returns:
            The number of simulation steps
            
        Raises:
            ValueError: If the time string format is invalid
        """
        years, months, days, hours, minutes = self.parse_time_str(time_str)
        
        # Convert to steps
        total_steps = (
            years * self.steps_per_year +
            months * self.steps_per_month +
            days * self.steps_per_day +
            hours * self.steps_per_hour +
            minutes // STEP_MINUTES
        )
        
        return total_steps
    
    def get_all_units(self):
        """Get a list of all available time units.
        
        Returns:
            List of time unit names
        """
        return list(self._unit_map.keys())
    
    def is_valid_unit(self, unit):
        """Check if a time unit is valid.
        
        Args:
            unit: The time unit to check
            
        Returns:
            True if the unit is valid, False otherwise
        """
        return unit in self._unit_map
    
    def get_steps_between(self, start_step, end_step):
        """Calculate the number of steps between two step counts.
        
        Args:
            start_step: The starting step count
            end_step: The ending step count
            
        Returns:
            The number of steps between start_step and end_step
        """
        return max(0, end_step - start_step)
    
    def get_time_between(self, start_step, end_step, unit='day'):
        """Calculate the time between two step counts in the specified unit.
        
        Args:
            start_step: The starting step count
            end_step: The ending step count
            unit: The time unit to return the result in
            
        Returns:
            The time between start_step and end_step in the specified unit
        """
        steps = self.get_steps_between(start_step, end_step)
        return steps / self[unit]
    
    def add_time(self, steps, value, unit):
        """Add a specified amount of time to a step count.
        
        Args:
            steps: The current step count
            value: The amount of time to add
            unit: The unit of the time to add
            
        Returns:
            The new step count after adding the specified time
        """
        return steps + int(value * self[unit])
    
    def subtract_time(self, steps, value, unit):
        """Subtract a specified amount of time from a step count.
        
        Args:
            steps: The current step count
            value: The amount of time to subtract
            unit: The unit of the time to subtract
            
        Returns:
            The new step count after subtracting the specified time
        """
        return max(0, steps - int(value * self[unit]))

# Create the time unit instance
time_units = TimeUnit()

# For backward compatibility with existing code
steps = time_units

workplace_radius = 10

small_meal_avg_cost = 3
medium_meal_avg_cost = 14
large_meal_avg_cost = 20
