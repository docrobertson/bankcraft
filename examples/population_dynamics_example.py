"""
Example demonstrating the unified person management and inactive status tracking.

This example shows how to:
1. Create a model with initial population
2. Add new people during runtime
3. Mark people as inactive (leaving the community)
4. Track and analyze both active and inactive people
"""

import pandas as pd
from bankcraft.model import BankCraftModelBuilder

# Create a model with a small initial population
model = BankCraftModelBuilder.build_default_model(
    num_people=5,
    initial_money=1000,
    width=10,
    height=10
)

print(f"Initial population: {len([a for a in model.agents if hasattr(a, 'active') and a.active])} active people")

# Run the model for a few steps
model.run(steps=10)

# Add a new person
new_person = model.add_person(initial_money=2000)
print(f"Added new person with ID {new_person.unique_id}")

# Run a few more steps
model.run(steps=10)

# Mark a person as inactive (leaving)
person_to_remove = [a for a in model.agents if hasattr(a, 'active') and a.active][0]
print(f"Person {person_to_remove.unique_id} is leaving the community")
model.remove_person(person_to_remove)

# Run a few more steps
model.run(steps=10)

# Get data for all people, including inactive ones
people_data = model.get_people()

# Analyze active vs inactive people
active_people = people_data[people_data['active'] == True]
inactive_people = people_data[people_data['active'] == False]

print("\nSummary:")
print(f"Total people tracked: {len(people_data['AgentID'].unique())}")
print(f"Currently active: {len(active_people['AgentID'].unique())}")
print(f"Inactive (left community): {len(inactive_people['AgentID'].unique())}")

# Get the diary for the person who left
print(f"\nDiary for person who left (ID: {person_to_remove.unique_id}):")
print(model.get_agent_diary(person_to_remove.unique_id))

# Demonstrate that we can still access data for inactive people
print("\nLast recorded data for inactive people:")
for agent_id in inactive_people['AgentID'].unique():
    last_record = inactive_people[inactive_people['AgentID'] == agent_id].iloc[-1]
    print(f"Person {agent_id}: Last active at step {last_record['Step']}, "
          f"with {last_record.get('account_0', 'unknown')} in primary account") 