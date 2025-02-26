# TimeUnit Documentation

## Overview

The `TimeUnit` class provides a clean, consistent way to handle time conversions in the BankCraft simulation. It replaces the previous dictionary-based approach with a more robust object-oriented solution while maintaining backward compatibility.

In the simulation, each step represents 10 minutes of simulated time. The `TimeUnit` class helps convert between different time units (minutes, hours, days, etc.) and the corresponding number of simulation steps.

## Core Functionality

### Time Unit Conversions

The primary purpose of the `TimeUnit` class is to convert between different time units:

```python
from bankcraft.config import time_units

# Convert 1 day to hours
hours = time_units.convert(1, 'day', 'hour')  # Returns 24.0

# Convert 2 weeks to days
days = time_units.convert(2, 'week', 'day')   # Returns 14.0

# Convert 1 month to weeks
weeks = time_units.convert(1, 'month', 'week')  # Returns approximately 4.29
```

### Dictionary-like Access

For backward compatibility, the `TimeUnit` class supports dictionary-like access to get the number of steps for each time unit:

```python
# Get steps per day (144 steps)
steps_per_day = time_units['day']

# Get steps per week (1008 steps)
steps_per_week = time_units['week']
```

### Human-Readable Time Strings

Convert a number of steps to a human-readable time string:

```python
# Convert 150 steps to a human-readable string
time_str = time_units.steps_to_time_str(150)  # Returns "1 day, 1 hour"
```

### Parsing Time Strings

Parse time strings into simulation steps:

```python
# Parse a simple time string
steps = time_units.time_str_to_steps("2 days")  # Returns 288 steps

# Parse a compound time string
steps = time_units.time_str_to_steps("1 day, 6 hours, 30 minutes")  # Returns 180 steps

# Use in model.run() for duration-based simulation
model.run(duration="2 days, 4 hours")  # Run for 2 days and 4 hours of simulation time
```

The `parse_time_str` method breaks down a time string into its components:

```python
# Parse a time string into (days, hours, minutes)
days, hours, minutes = time_units.parse_time_str("2 days, 4 hours, 30 minutes")
# Returns (2, 4, 30)
```

### Time Calculations

Calculate time between events or add/subtract time:

```python
# Calculate days between two step counts
days = time_units.get_time_between(1000, 1288, 'day')  # Returns 2.0

# Add 2 weeks to a step count
new_steps = time_units.add_time(1000, 2, 'week')  # Returns 3016

# Subtract 3 days from a step count
new_steps = time_units.subtract_time(3000, 3, 'day')  # Returns 2568
```

## Available Time Units

The following time units are available:

- `'10min'`: 1 step (base unit)
- `'hour'`: 6 steps
- `'day'`: 144 steps
- `'week'`: 1008 steps
- `'biweekly'`: 2016 steps
- `'month'`: 4320 steps
- `'year'`: 52560 steps

## Running the Model with Time Specifications

The `BankCraftModel` class now supports running the simulation for a specified duration or until a specific end date:

```python
from bankcraft import BankCraftModel
from bankcraft.config import time_units

model = BankCraftModel()

# Run for a specific number of steps
model.run(steps=100)

# Run for a specific duration using a time string
model.run(duration="2 days, 4 hours")

# Run until a specific end date
import datetime
end_date = model.current_time + datetime.timedelta(days=7)
model.run(until_date=end_date)
# Alternatively:
model.run_until(end_date)
```

## Backward Compatibility

For backward compatibility with existing code, the global `steps` variable is an alias for the `time_units` instance:

```python
from bankcraft.config import steps

# These are equivalent
steps['day'] == time_units['day']  # True
```

## Best Practices

1. Use the `convert()` method for time unit conversions instead of manual calculations
2. Use `steps_to_time_str()` for human-readable output in logs or UI
3. Use `add_time()` and `subtract_time()` instead of manual step calculations
4. For new code, prefer using `time_units` over `steps` for clarity
5. Use time strings with `time_str_to_steps()` for more readable code when specifying durations
6. When running the model, use the `duration` parameter with a time string for more intuitive simulation control 