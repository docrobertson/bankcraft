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

## Example

Here is a simple example of how to run BankCraft:

```python
from bankcraft import BankCraftModel
from bankcraft.visualization import Visualization

# Create and initialize model
model = BankCraftModel(
    num_people=100,
    initial_money=1000,
    num_banks=3,
    width=50,
    height=50
)

# Run simulation
model.run(365)  # Simulate one year

# Analyze results
transactions_df = model.get_transactions()
people_df = model.get_people()

# Visualize
vis = Visualization(model)
vis.grid_plot()
```

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

## Access

BankCraft is currently under development. While open source, it is not yet ready for public use.
BankCraft may only be used if explicit permission is given.

## Contributing

While BankCraft is currently restricted, we welcome discussions about potential contributions. Please reach out to discuss collaboration opportunities.
