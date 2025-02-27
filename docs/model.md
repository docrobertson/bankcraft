# BankCraft Model Documentation

This document provides detailed information about the BankCraftModel and BankCraftModelBuilder classes, which are the core components of the BankCraft simulation framework.

## BankCraftModelBuilder

The `BankCraftModelBuilder` class is responsible for creating and configuring instances of the `BankCraftModel` class. It follows the builder pattern to separate model construction from model execution, making it easier to create different types of models with different configurations.

### Methods

#### `build_default_model`

Creates a fully configured model with all necessary components for a standard simulation.

```python
@staticmethod
def build_default_model(num_people=6, initial_money=1000, num_banks=1, width=15, height=15):
    """Build a default BankCraftModel with standard configuration.
    
    Args:
        num_people (int): Number of people to create
        initial_money (int): Initial money for each person
        num_banks (int): Number of banks to create
        width (int): Width of the grid
        height (int): Height of the grid
        
    Returns:
        BankCraftModel: A fully initialized model
    """
```

The default model includes:

- The specified number of people with the given initial money
- The specified number of banks
- Businesses for recurring payments (rent, utilities, etc.)
- Employers (number based on grid size)
- Food and clothing merchants
- A social network connecting all people

#### `build_custom_model`

Creates a minimal model with just the basic infrastructure, allowing for complete customization.

```python
@staticmethod
def build_custom_model(width=15, height=15, **kwargs):
    """Build a custom BankCraftModel with specific configuration.
    
    Args:
        width (int): Width of the grid
        height (int): Height of the grid
        **kwargs: Custom configuration parameters
        
    Returns:
        BankCraftModel: A model instance ready for customization
    """
```

The custom model includes:

- A grid of the specified dimensions
- Basic time and data collection setup
- Empty collections for banks, employers, and businesses
- No agents are added by default

## BankCraftModel

The `BankCraftModel` class is the core simulation engine of BankCraft. It manages all agents, handles their interactions, and collects data about the simulation.

### Key Properties

- `grid`: The spatial grid where agents are placed
- `current_time`: The current simulation time
- `banks`: List of bank agents
- `employers`: List of employer agents
- `invoicer`: Dictionary of business agents for recurring payments
- `agents`: Collection of all agents in the model (from Mesa)

### Running the Simulation

The model provides several methods for running the simulation:

#### `step`

Executes a single step of the simulation.

```python
def step(self):
    """Execute one step of the model."""
```

Each step:

1. Handles dynamic population changes
2. Activates each agent in random order
3. Collects data
4. Advances the simulation time

#### `run`

Runs the simulation for a specified number of steps, duration, or until a specific date.

```python
def run(self, steps=None, duration=None, until_date=None):
    """Run the model for a specified number of steps, duration, or until a specific date.
    
    Args:
        steps (int, optional): Number of steps to run. Defaults to None.
        duration (str, optional): Duration to run as a string (e.g., "2 days, 4 hours"). Defaults to None.
        until_date (datetime.datetime, optional): Date to run until. Defaults to None.
        
    Returns:
        BankCraftModel: The model instance
    """
```

Examples:

```python
# Run for 100 steps
model.run(steps=100)

# Run for a specific duration
model.run(duration="1 month, 2 weeks")

# Run until a specific date
target_date = datetime.datetime(2023, 6, 1, 0, 0, 0)
model.run(until_date=target_date)
```

#### `run_until`

Convenience method to run the simulation until a specific date.

```python
def run_until(self, end_date):
    """Run the model until a specific date is reached.
    
    Args:
        end_date (datetime.datetime): The date to run until
        
    Returns:
        BankCraftModel: The model instance
    """
```

### Dynamic Population Changes

The model supports dynamic changes to the population during simulation:

#### `add_person`

Adds a new person to the model.

```python
def add_person(self, initial_money=1000):
    """Add a new person to the model dynamically.
    
    Args:
        initial_money (int): Initial money for the person
        
    Returns:
        Person: The newly created person
    """
```

#### `remove_person`

Removes a person from the model.

```python
def remove_person(self, person=None):
    """Remove a person from the model dynamically.
    
    Args:
        person (Person, optional): The person to remove. If None, a random person is selected.
        
    Returns:
        bool: True if a person was removed, False otherwise
    """
```

#### `add_employer`

Adds a new employer to the model.

```python
def add_employer(self):
    """Add a new employer to the model dynamically.
    
    Returns:
        Employer: The newly created employer
    """
```

#### `remove_employer`

Removes an employer from the model.

```python
def remove_employer(self, employer=None):
    """Remove an employer from the model dynamically.
    
    Args:
        employer (Employer, optional): The employer to remove. If None, a random employer is selected.
        
    Returns:
        bool: True if an employer was removed, False otherwise
    """
```

#### Automatic Population Dynamics

The model can automatically handle population changes based on configured rates:

```python
# Configure rates
model.person_move_in_rate = 0.001   # 0.1% chance per step
model.person_move_out_rate = 0.001  # 0.1% chance per step
model.business_open_rate = 0.0005   # 0.05% chance per step
model.business_close_rate = 0.0005  # 0.05% chance per step

# Run with automatic population changes
model.run(steps=1000)
```

### Data Collection and Analysis

The model provides several methods for accessing and analyzing simulation data:

#### `get_transactions`

Returns a DataFrame of all transactions.

```python
def get_transactions(self):
    """Get transactions data as a DataFrame."""
```

#### `get_people`

Returns a DataFrame of people data with expanded columns for accounts and motivations.

```python
def get_people(self):
    """Get people data as a DataFrame with expanded columns for accounts and motivations."""
```

#### `get_agent_actions`

Returns a DataFrame of agent actions.

```python
def get_agent_actions(self, agent_id=None):
    """Get the action log for a specific agent or all agents.
    
    Args:
        agent_id (int, optional): The ID of the agent to get actions for. 
                                 If None, returns actions for all agents.
                                 
    Returns:
        pandas.DataFrame: A DataFrame containing the agent's actions
    """
```

#### `get_agent_diary`

Returns a formatted diary of an agent's actions.

```python
def get_agent_diary(self, agent_id):
    """Get a formatted diary of an agent's actions.
    
    Args:
        agent_id (int): The ID of the agent to get the diary for
        
    Returns:
        str: A formatted string containing the agent's diary
    """
```

#### `save_to_csv`

Saves the model data to CSV files.

```python
def save_to_csv(self, base_filename=""):
    """Save the model data to CSV files.
    
    Args:
        base_filename (str): Optional prefix for the CSV filenames. If empty,
                           files will be named 'agents.csv', 'transactions.csv', etc.
    """
```

## Example Usage

Here's a complete example of how to use the BankCraftModel and BankCraftModelBuilder:

```python
import datetime
from bankcraft import BankCraftModelBuilder
from bankcraft import Visualization

# Create a default model
model = BankCraftModelBuilder.build_default_model(
    num_people=50,
    initial_money=2000,
    num_banks=2,
    width=30,
    height=30
)

# Configure population dynamics
model.person_move_in_rate = 0.002   # 0.2% chance per step
model.person_move_out_rate = 0.001  # 0.1% chance per step
model.business_open_rate = 0.0005   # 0.05% chance per step
model.business_close_rate = 0.0005  # 0.05% chance per step

# Run for 1 month
model.run(duration="1 month")

# Add a specific person
new_person = model.add_person(initial_money=5000)

# Run until a specific date
target_date = model.current_time + datetime.timedelta(days=15)
model.run_until(target_date)

# Analyze results
transactions_df = model.get_transactions()
people_df = model.get_people()

# Get a specific agent's diary
agent_id = model.agents[0].unique_id
agent_diary = model.get_agent_diary(agent_id)
print(agent_diary)

# Save results
model.save_to_csv(base_filename="simulation_results")

# Visualize
vis = Visualization(model)
vis.grid_plot()
```

## Advanced Customization

For advanced scenarios, you can create a custom model and configure it manually:

```python
from bankcraft import BankCraftModelBuilder
from bankcraft.agent import Bank, Person, Employer, Business
import networkx as nx

# Create a minimal model
model = BankCraftModelBuilder.build_custom_model(width=20, height=20)

# Add banks
model._num_banks = 1
model.banks = [Bank(model) for _ in range(model._num_banks)]

# Add businesses
business_types = ["rent/mortgage", "utilities", "subscription", "membership", "net_providers"]
model.invoicer = {b_type: Business(model, b_type) for b_type in business_types}

# Add employers
model._num_employers = 2
model.employers = [Employer(model) for _ in range(model._num_employers)]
model._put_employers_in_model()

# Initialize social network
model._num_people = 10
model.social_grid = nx.complete_graph(model._num_people)
for (u, v) in model.social_grid.edges():
    model.social_grid.edges[u, v]['weight'] = 1 / (model._num_people - 1)

# Add people
model._put_people_in_model(initial_money=1500)

# Add merchants
model._num_merchant = 3
model._put_food_merchants_in_model()
model._put_clothes_merchants_in_model()

# Run the model
model.run(steps=100)
```
