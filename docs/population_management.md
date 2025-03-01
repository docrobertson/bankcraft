# Population Management in BankCraft

This document describes how BankCraft manages population dynamics, including adding and removing people from the simulation.

## Unified Person Management

BankCraft now uses a unified approach to adding people to the model, whether during initial setup or during runtime. This simplifies the codebase and ensures consistent behavior.

### Key Methods

- `add_person(initial_money=1000, social_node=None)`: Adds a single person to the model with the specified initial money and optional social node ID.
- `add_people(num_people, initial_money=1000)`: Adds multiple people to the model at once, used primarily during model initialization.
- `remove_person(person=None)`: Marks a person as inactive rather than removing them from the model. If no person is specified, a random active person is selected.

## Active Status Tracking

Instead of completely removing people from the model when they leave, BankCraft now marks them as inactive. This allows for:

1. Continued access to their historical data
2. Analysis of both active and inactive populations
3. Tracking of when and why people left the community

### Implementation Details

- Each `Person` instance has an `active` boolean flag (default: `True`)
- When a person leaves, they are marked as `active = False` and removed from the grid
- The person remains in the model's agent list for data collection and analysis
- The `step` method in `Person` checks the `active` flag and skips processing for inactive people

### Data Collection

- The `active` status is included in the people data collected by the model
- The `get_people()` method returns data for both active and inactive people
- You can filter the data based on the `active` column to analyze different populations

## Example Usage

```python
# Create a model with initial population
model = BankCraftModelBuilder.build_model(num_people=5)

# Add a new person during runtime
new_person = model.add_person(initial_money=2000)

# Mark a person as inactive (leaving)
model.remove_person(new_person)

# Get data for all people, including inactive ones
people_data = model.get_people()

# Analyze active vs inactive people
active_people = people_data[people_data['active'] == True]
inactive_people = people_data[people_data['active'] == False]
```

See the full example in `examples/population_dynamics_example.py`.

## Benefits

1. **Historical Analysis**: Researchers can analyze the complete history of the simulation, including people who have left.
2. **Realistic Modeling**: People leaving is modeled as an event rather than deletion, more accurately reflecting real-world population dynamics.
3. **Data Integrity**: No data is lost when people leave the community.
4. **Simplified API**: A single consistent method for adding people, regardless of when they're added.

## Technical Implementation

When a person is marked as inactive:

1. They are removed from their employer
2. They are removed from friends' lists
3. They are removed from the spatial grid
4. Their `active` flag is set to `False`
5. A "left" action is logged in their action history
6. They remain in the model's agent list

The `handle_population_dynamics` method considers only active people when determining who might leave the community.
