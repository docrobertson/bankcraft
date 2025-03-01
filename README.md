# BankCraft

An agent-based simulator for generating realistic financial transaction data, designed to support financial crime detection research and development.

## Motivation

BankCraft simulates a virtual economy where agents (people, businesses, employers) interact and conduct financial transactions. The simulation aims to:

1. Generate realistic patterns of legitimate financial activity
2. Support injection of fraudulent and criminal behavior patterns
3. Provide a testbed for developing and evaluating financial crime detection algorithms
4. Enable research into new approaches for identifying suspicious activity

## Features

- Agent-based modeling of financial behaviors and interactions
- Multiple transaction types (cash, wire, ACH, etc.)
- Realistic daily activity patterns (work, shopping, social interactions)
- Configurable parameters for population size, initial conditions, etc.
- Data collection for transaction analysis
- Visualization tools for monitoring simulation state
- Dynamic population changes (people moving in/out, businesses opening/closing)
- Modular model building and running with builder pattern
- Status dashboard for monitoring model execution progress and statistics

## Model Building

BankCraft uses a builder pattern to create and configure models, separating model construction from model execution:

```python
from bankcraft import BankCraftModelBuilder

# Create a fully configured default model
model = BankCraftModelBuilder.build_model(
    num_people=100,
    initial_money=1000,
    num_banks=3,
    width=50,
    height=50
)
```

### Default Model Builder

The `build_default_model` method creates a fully configured model with:

- Specified number of people, banks, and initial money
- Appropriate number of employers based on grid size
- Food and clothing merchants
- Social network connections between people
- Complete data collection setup

### Custom Model Builder

The `build_custom_model` method creates a minimal model with:

- Just the grid and basic infrastructure
- No agents added by default
- Allows for complete customization of the model

## Example

Here is a simple example of how to run BankCraft:

```python
from bankcraft import BankCraftModelBuilder
from bankcraft import Visualization

# Create and initialize model using the builder
model = BankCraftModelBuilder.build_model(
    num_people=100,
    initial_money=1000,
    num_banks=3,
    width=50,
    height=50
)

# Run simulation
model.run(steps=365)  # Simulate one year

# Alternative ways to run the simulation
model.run(duration="1 month, 2 weeks")  # Run for a specific duration
model.run_until(end_date)  # Run until a specific date

# Analyze results
transactions_df = model.get_transactions()
people_df = model.get_people()
agent_actions = model.get_agent_actions()

# Get a narrative diary for a specific agent
agent_diary = model.get_agent_diary(agent_id=42)

# Save data to CSV files
model.save_to_csv(base_filename="simulation_results")

# Visualize
vis = Visualization(model)
vis.grid_plot()
```

### Dynamic Population Changes

BankCraft now supports dynamic population changes during simulation:

```python
# Manually add a new person
new_person = model.add_person(initial_money=2000)

# Manually add a new employer
new_employer = model.add_employer()

# Remove a specific person
model.remove_person(person=some_person)

# Remove a random employer
model.remove_employer()

# Configure automatic population dynamics
model.person_move_in_rate = 0.001   # 0.1% chance per step
model.person_move_out_rate = 0.001  # 0.1% chance per step
model.business_open_rate = 0.0005   # 0.05% chance per step
model.business_close_rate = 0.0005  # 0.05% chance per step

# Run with automatic population changes
model.run(steps=1000)
```

## Status Dashboard

BankCraft includes a status dashboard that provides real-time information about model execution:

- Progress bar showing completion percentage
- Start date and time of the simulation
- Current date and time in the simulation
- Anticipated end date and time
- Number of people, businesses, and employers in the simulation
- Execution time

The dashboard can be enabled by setting the `show_dashboard` parameter to `True` when calling the `run` or `run_until` methods:

```python
# Run with dashboard
model.run(steps=100, show_dashboard=True)

# Run until a specific date with dashboard
end_date = model.current_time + datetime.timedelta(days=5)
model.run_until(end_date, show_dashboard=True)

# Customize dashboard update frequency (default is 10 steps)
model.run(steps=100, show_dashboard=True, dashboard_update_frequency=5)
```

The dashboard automatically adapts to both terminal and Jupyter notebook environments.

## Roadmap

- Enhanced transaction patterns and agent behaviors
- Implementation of various financial crime patterns
- Integration of regulatory compliance rules
- Advanced analytics and detection algorithms
- API for custom behavior injection
- Extended visualization and analysis tools

## Architecture

BankCraft is built with modularity and extensibility in mind:

1. **Transaction System**: Flexible framework for different transaction types
2. **Behavior Patterns**: Configurable agent behavior system
3. **Risk Scoring**: Framework for transaction risk assessment
4. **Agent Capabilities**: Modular approach to agent features
5. **Event System**: Robust activity monitoring and analysis
6. **Visualization**: Tools for understanding simulation state
7. **Model Building**: Separation of model building from running logic using the builder pattern
8. **Population Dynamics**: Support for dynamic agent population changes

## Access

BankCraft is currently under development. While open source, it is not yet ready for public use.
BankCraft may only be used if explicit permission is given.

## Contributing

While BankCraft is currently restricted, we welcome discussions about potential contributions. Please reach out to discuss collaboration opportunities.
