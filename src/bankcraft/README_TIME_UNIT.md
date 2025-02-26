# TimeUnit

## What is TimeUnit?

`TimeUnit` is a utility class for handling time conversions in the BankCraft simulation. It provides a clean, object-oriented approach to convert between different time units and simulation steps.

## Why use TimeUnit?

The `TimeUnit` class replaces the previous dictionary-based approach (`steps`) with a more robust solution that:

1. Maintains backward compatibility with existing code
2. Provides clear, readable methods for time conversions
3. Handles edge cases gracefully
4. Makes code more maintainable and less error-prone

## Quick Examples

```python
from bankcraft.config import time_units

# Convert between time units
hours = time_units.convert(1, 'day', 'hour')  # 24.0

# Get human-readable time
time_str = time_units.steps_to_time_str(150)  # "1 day, 1 hour"

# Add/subtract time
new_steps = time_units.add_time(current_steps, 2, 'week')
```

## Documentation

For full documentation, see `docs/time_unit.md`. 