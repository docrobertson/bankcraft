from bankcraft.model import BankCraftModel
from bankcraft.agent import Employer
from bankcraft.agent import Bank
from bankcraft.agent import Person
from bankcraft.agent.merchant import Clothes, Food
from bankcraft.agent import Business
import pytest

initial_money = 500

@pytest.fixture
def model():
    """Create a model instance for testing."""
    model = BankCraftModel()
    return model

def test_model_has_employers(model):
    employers = [agent for agent in model.agents if isinstance(agent, Employer)]
    assert len(employers) == model._num_employers

def test_model_has_people(model):
    people = [agent for agent in model.agents if isinstance(agent, Person)]
    assert len(people) == model._num_people

def test_model_has_food_merchants(model):
    merchants = [agent for agent in model.agents if isinstance(agent, Food)]
    assert len(merchants) == model._num_merchant

def test_model_has_clothes_merchants(model):
    merchants = [agent for agent in model.agents if isinstance(agent, Clothes)]
    assert len(merchants) == model._num_merchant//2

def test_people_are_on_grid(model):
    model._put_people_in_model(initial_money)
    people = [agent for agent in model.agents if isinstance(agent, Person)]
    assert all(agent in model.get_all_agents_on_grid() for agent in people)

def test_banks_are_in_agents_but_not_on_grid(model):
    """Test that banks exist in model.agents but are not placed on the grid."""
    banks_in_agents = [agent for agent in model.agents if isinstance(agent, Bank)]
    banks_on_grid = [agent for agent in model.get_all_agents_on_grid() if isinstance(agent, Bank)]
    assert len(banks_in_agents) == model._num_banks and len(banks_on_grid) == 0

def test_businesses_are_in_agents_but_not_on_grid(model):
    """Test that businesses exist in model.agents but are not placed on the grid."""
    businesses_in_agents = [agent for agent in model.agents if isinstance(agent, Business)]
    businesses_on_grid = [agent for agent in model.get_all_agents_on_grid() if isinstance(agent, Business)]
    assert len(businesses_in_agents) == len(model.invoicer) and len(businesses_on_grid) == 0

def test_can_step_model(model):
    """Test that the model can execute a single step."""
    current_time = model.current_time
    initial_steps = model.steps
    model.step()
    assert model.current_time == current_time + model._one_step_time
    assert model.steps == initial_steps + 1

def test_model_run_multiple_steps():
    """Test that the model can run for multiple steps."""
    model = BankCraftModel(num_people=10, initial_money=1000, num_banks=1, width=20, height=20)
    initial_time = model.current_time
    initial_steps = model.steps
    num_steps = 5
    
    model.run(steps=num_steps)
    
    # Check that the correct number of steps were executed
    assert model.steps == initial_steps + num_steps
    assert model.current_time == initial_time + (model._one_step_time * num_steps)
    
    # Check that data was collected
    people_data = model.datacollector.get_table_dataframe("people")
    assert not people_data.empty
    
    # Verify that transactions were recorded
    transactions_data = model.datacollector.get_table_dataframe("transactions")
    # Note: There might not be transactions in the first few steps, so we don't assert on this

def test_model_run_with_duration():
    """Test that the model can run for a specified duration."""
    model = BankCraftModel(num_people=5, initial_money=1000, num_banks=1, width=10, height=10)
    initial_time = model.current_time
    initial_steps = model.steps
    
    # Run for 2 hours (12 steps)
    model.run(duration="2 hours")
    
    # Check that the correct number of steps were executed
    from bankcraft.config import time_units
    expected_steps = time_units.time_str_to_steps("2 hours")
    assert model.steps == initial_steps + expected_steps
    assert model.current_time == initial_time + (model._one_step_time * expected_steps)

def test_model_run_until_date():
    """Test that the model can run until a specified date."""
    import datetime
    
    model = BankCraftModel(num_people=5, initial_money=1000, num_banks=1, width=10, height=10)
    initial_time = model.current_time
    
    # Run until 3 hours in the future
    target_time = initial_time + datetime.timedelta(hours=3)
    model.run_until(target_time)
    
    # Check that we've reached the target time (or just passed it)
    assert model.current_time >= target_time
    # We should be at most one step past the target time
    assert model.current_time <= target_time + model._one_step_time

def test_model_run_with_invalid_params():
    """Test that the model raises an error when invalid parameters are provided."""
    import datetime
    import pytest
    
    model = BankCraftModel(num_people=5, initial_money=1000, num_banks=1, width=10, height=10)
    
    # Test with no parameters
    with pytest.raises(ValueError):
        model.run()
    
    # Test with multiple parameters
    with pytest.raises(ValueError):
        model.run(steps=5, duration="2 hours")
    
    # Test with invalid duration string
    with pytest.raises(ValueError):
        model.run(duration="invalid duration")
    
    # Test with past date
    past_date = model.current_time - datetime.timedelta(days=1)
    # This should not raise an error but should not run any steps
    initial_steps = model.steps
    model.run(until_date=past_date)
    assert model.steps == initial_steps  # No steps should have been executed

def test_time_str_to_steps_conversion():
    """Test the conversion from time strings to steps."""
    from bankcraft.config import time_units
    
    # Test simple cases
    assert time_units.time_str_to_steps("1 hour") == time_units['hour']
    assert time_units.time_str_to_steps("2 days") == 2 * time_units['day']
    
    # Test compound cases
    assert time_units.time_str_to_steps("1 day, 2 hours") == time_units['day'] + 2 * time_units['hour']
    assert time_units.time_str_to_steps("2 days, 3 hours, 30 minutes") == (
        2 * time_units['day'] + 3 * time_units['hour'] + 3  # 30 minutes = 3 steps
    )
    
    # Test empty string
    assert time_units.time_str_to_steps("") == 0

def test_all_agents_have_locations(model):
    """Test that all agents have a location property set after initialization."""
    for agent in model.agents:
        if isinstance(agent, (Bank, Business)):
            # These agents should have a location property but aren't on grid
            assert hasattr(agent, 'location')
        else:
            # All other agents should be on grid with pos attribute
            assert agent.pos is not None, f"Agent {agent.unique_id} of type {agent.type} has no position"
            assert isinstance(agent.pos, tuple), f"Agent {agent.unique_id} position is not a tuple"
            assert len(agent.pos) == 2, f"Agent {agent.unique_id} position is not 2D coordinates"

def test_model_initialization():
    """Test that the model properly initializes all components."""
    # Create model
    model = BankCraftModel(num_people=10, initial_money=1000, width=20, height=20)
    
    # Test that all expected agents are created and placed
    all_agents = model.get_all_agents_on_grid()
    
    # Count agent types
    person_count = sum(1 for agent in all_agents if agent.type == 'person')
    employer_count = sum(1 for agent in all_agents if agent.type == 'employer')
    merchant_count = sum(1 for agent in all_agents if agent.type == 'merchant')
    
    # Check counts match expected
    assert person_count == 10, "Expected 10 people"
    assert employer_count == model._num_employers, f"Expected {model._num_employers} employers"
    assert merchant_count == model._num_merchant * 1.5, f"Expected {model._num_merchant * 1.5} merchants (food + clothes)"
    
    # Check all agents have valid positions
    for agent in all_agents:
        assert agent.pos is not None, f"Agent {agent.unique_id} has no position"
        assert 0 <= agent.pos[0] < model.grid.width, f"Agent {agent.unique_id} x position out of bounds"
        assert 0 <= agent.pos[1] < model.grid.height, f"Agent {agent.unique_id} y position out of bounds"
    
    # Check people have necessary attributes
    people = [agent for agent in all_agents if agent.type == 'person']
    for person in people:
        assert person.home is not None, "Person has no home location"
        assert person.work is not None, "Person has no work location"
        assert person.friends is not None, "Person has no friends assigned"
        assert len(person.friends) > 0, "Person has empty friends list"

