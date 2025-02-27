# TimeUnit

## What is TimeUnit?

`TimeUnit` is a utility class for handling time conversions in the BankCraft simulation. It provides a clean, object-oriented approach to convert between different time units and simulation steps.

## Why use TimeUnit?

The `TimeUnit` class replaces the previous dictionary-based approach (`steps`) with a more robust solution that:

1. Maintains backward compatibility with existing code
2. Provides clear, readable methods for time conversions
3. Handles edge cases gracefully
4. Makes code more maintainable and less error-prone
5. Accurately handles larger time units like months and years

## Quick Examples

```python
from bankcraft.config import time_units

# Convert between time units
hours = time_units.convert(1, 'day', 'hour')  # 24.0
months = time_units.convert(1, 'year', 'month')  # 12.0

# Get human-readable time
time_str = time_units.steps_to_time_str(150)  # "1 day, 1 hour"
year_str = time_units.steps_to_time_str(time_units['year'])  # "1 year"

# Add/subtract time
new_steps = time_units.add_time(current_steps, 2, 'week')
new_steps = time_units.add_time(current_steps, 1, 'month')

# Parse time strings to steps
steps = time_units.time_str_to_steps("2 days, 4 hours")  # 312 steps
steps = time_units.time_str_to_steps("1 year, 2 months")  # Steps for 1 year and 2 months

# Run model for a specific duration
from bankcraft import BankCraftModel
model = BankCraftModel()
model.run(duration="1 week, 2 days")  # Run for 9 days of simulation time
model.run(duration="1 month")  # Run for a month of simulation time
```

## Improved Month and Year Handling

The TimeUnit class now uses more accurate calculations for months and years:

- A month is calculated as 30.436875 days (average days per month in a year)
- A year is calculated as 365.2425 days (accounts for leap years)

This provides more accurate conversions between time units, especially when dealing with longer time periods.

## Documentation

For full documentation, see `docs/time_unit.md`.
