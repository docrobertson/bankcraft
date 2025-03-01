from bankcraft.model import BankCraftModel, BankCraftModelBuilder
from bankcraft.agent import Employer
from bankcraft.agent import Bank
from bankcraft.agent import Person
from bankcraft.agent.merchant import Clothes, Food
from bankcraft.agent import Business
import pytest
import datetime
import networkx as nx

initial_money = 500

@pytest.fixture
def model():
    """Create a model instance for testing."""
    return BankCraftModelBuilder.build_model(num_people=6, initial_money=initial_money)

@pytest.fixture
def empty_model():
    """Create an empty model instance for testing specific initialization methods."""
    return BankCraftModel(width=15, height=15)

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

def test_people_are_on_grid(empty_model):
    """Test that people are placed on the grid correctly."""
    # First we need to set up employers
    empty_model._num_people = 6
    empty_model._num_employers = 3
    empty_model.employers = [Employer(empty_model) for _ in range(empty_model._num_employers)]
    empty_model._put_employers_in_model()
    
    # Initialize businesses
    business_types = ["rent/mortgage", "utilities", "subscription", "membership", "net_providers"]
    empty_model.invoicer = {b_type: Business(empty_model, b_type) for b_type in business_types}
    
    # Initialize social network
    empty_model.social_grid = nx.complete_graph(empty_model._num_people)
    for (u, v) in empty_model.social_grid.edges():
        empty_model.social_grid.edges[u, v]['weight'] = 1 / (empty_model._num_people - 1)
    
    # Now we can add people
    empty_model._put_people_in_model(initial_money)
    people = [agent for agent in empty_model.agents if isinstance(agent, Person)]
    assert all(agent in empty_model.get_all_agents_on_grid() for agent in people)

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
    model.step()
    assert model.current_time == current_time + model._one_step_time

def test_model_run_multiple_steps():
    """Test that the model can run for multiple steps."""
    model = BankCraftModelBuilder.build_model(
        num_people=10, initial_money=1000, width=20, height=20
    )
    initial_time = model.current_time
    num_steps = 5
    
    model.run(steps=num_steps)
    
    # Check that the correct number of steps were executed
    assert model.current_time == initial_time + (model._one_step_time * num_steps)
    
    # Check that data was collected
    people_data = model.get_people()
    assert not people_data.empty
    
    # Verify that transactions were recorded
    transactions_data = model.get_transactions()
    # Note: There might not be transactions in the first few steps, so we don't assert on this

def test_model_run_with_duration():
    """Test that the model can run for a specified duration."""
    model = BankCraftModelBuilder.build_model(
        num_people=5, initial_money=1000, width=10, height=10
    )
    initial_time = model.current_time
    
    # Run for 2 hours (12 steps)
    model.run(duration="2 hours")
    
    # Check that the correct number of steps were executed
    from bankcraft.config import time_units
    expected_steps = time_units.time_str_to_steps("2 hours")
    assert model.current_time == initial_time + (model._one_step_time * expected_steps)

def test_model_run_until_date():
    """Test that the model can run until a specified date."""
    model = BankCraftModelBuilder.build_model(
        num_people=5, initial_money=1000, width=10, height=10
    )
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
    model = BankCraftModelBuilder.build_model(
        num_people=5, initial_money=1000, width=10, height=10
    )
    
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
    initial_time = model.current_time
    model.run(until_date=past_date)
    assert model.current_time == initial_time  # No steps should have been executed

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
    model = BankCraftModelBuilder.build_model(
        num_people=10, initial_money=1000, width=20, height=20
    )
    
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

# Tests for the refactored model

def test_model_builder_default():
    """Test that the model builder creates a default model with expected parameters."""
    model = BankCraftModelBuilder.build_model(
        num_people=8, initial_money=1500, num_banks=2, width=25, height=25
    )
    
    # Check that the model has the expected parameters
    assert model.grid.width == 25
    assert model.grid.height == 25
    assert model._num_people == 8
    assert model._num_banks == 2
    
    # Check that the model has the expected agents
    people = [agent for agent in model.agents if isinstance(agent, Person)]
    banks = [agent for agent in model.agents if isinstance(agent, Bank)]
    
    assert len(people) == 8
    assert len(banks) == 2
    
    # Check that people have bank accounts with the expected balance
    for person in people:
        assert hasattr(person, 'bank_accounts')
        # Check if at least one account has the initial balance
        has_account_with_balance = False
        for bank_accounts in person.bank_accounts:
            for account in bank_accounts:
                if account.balance == 1500:
                    has_account_with_balance = True
                    break
            if has_account_with_balance:
                break
        assert has_account_with_balance, f"Person {person.unique_id} has no account with balance 1500"

def test_model_builder_custom():
    """Test that the model builder can create a custom model."""
    model = BankCraftModelBuilder.build_model(width=30, height=30)
    
    # Check that the model has the expected dimensions
    assert model.grid.width == 30
    assert model.grid.height == 30
    
    # Check that the model is a minimal model (no agents yet)
    assert len([agent for agent in model.agents if isinstance(agent, Person)]) == 0
    assert len([agent for agent in model.agents if isinstance(agent, Bank)]) == 0

def test_population_dynamics():
    """Test that the model can handle dynamic population changes."""
    model = BankCraftModelBuilder.build_model(
        num_people=10, initial_money=1000, width=20, height=20
    )

    # Set high rates to ensure changes happen
    model.person_move_in_rate = 1.0  # 100% chance
    model.person_move_out_rate = 0.0  # 0% chance

    # Count initial active population
    initial_active_people = len([agent for agent in model.agents if isinstance(agent, Person) and agent.active])

    # Run one step with population dynamics
    model.handle_population_dynamics()

    # Check that a person was added
    current_active_people = len([agent for agent in model.agents if isinstance(agent, Person) and agent.active])
    assert current_active_people > initial_active_people

    # Now test removal
    model.person_move_in_rate = 0.0  # 0% chance
    model.person_move_out_rate = 1.0  # 100% chance

    # Run one step with population dynamics
    model.handle_population_dynamics()

    # Check that a person was marked as inactive
    new_active_people = len([agent for agent in model.agents if isinstance(agent, Person) and agent.active])
    assert new_active_people < current_active_people

def test_business_dynamics():
    """Test that the model can handle dynamic business changes."""
    model = BankCraftModelBuilder.build_model(
        num_people=10, initial_money=1000, width=20, height=20
    )
    
    # Set high rates to ensure changes happen
    model.business_open_rate = 1.0  # 100% chance
    model.business_close_rate = 0.0  # 0% chance
    
    # Count initial businesses
    initial_employers = len(model.employers)
    
    # Run one step with business dynamics
    model.handle_population_dynamics()
    
    # Check that a business was added
    current_employers = len(model.employers)
    assert current_employers > initial_employers
    
    # Now test removal
    model.business_open_rate = 0.0  # 0% chance
    model.business_close_rate = 1.0  # 100% chance
    
    # Run one step with business dynamics
    model.handle_population_dynamics()
    
    # Check that a business was removed (if there are at least 2 employers)
    if initial_employers > 1:
        new_employers = len(model.employers)
        assert new_employers < current_employers

def test_get_agent_actions():
    """Test that the model can retrieve agent actions."""
    model = BankCraftModelBuilder.build_model(
        num_people=5, initial_money=1000, width=10, height=10
    )
    
    # Run a few steps to generate actions
    model.run(steps=3)
    
    # Get all actions
    all_actions = model.get_agent_actions()
    assert not all_actions.empty
    
    # Get actions for a specific agent
    agent_id = model.agents[0].unique_id
    agent_actions = model.get_agent_actions(agent_id)
    
    # Check that the actions are for the correct agent
    if not agent_actions.empty:
        assert all(action == agent_id for action in agent_actions["agent_id"])

def test_get_agent_diary():
    """Test that the model can generate an agent diary."""
    model = BankCraftModelBuilder.build_model(
        num_people=5, initial_money=1000, width=10, height=10
    )
    
    # Run a few steps to generate actions
    model.run(steps=3)
    
    # Get diary for a specific agent
    agent_id = model.agents[0].unique_id
    diary = model.get_agent_diary(agent_id)
    
    # Check that the diary is a string
    assert isinstance(diary, str)
    
    # Check that the diary contains the agent ID
    assert str(agent_id) in diary

# Additional tests for the refactored model

def test_model_builder_with_custom_parameters():
    """Test that the model builder can create a model with custom parameters."""
    # Create a model with custom parameters
    model = BankCraftModelBuilder.build_model(
        num_people=15,
        initial_money=2000,
        num_banks=3,
        width=30,
        height=30
    )
    
    # Check that the model has the expected parameters
    assert model.grid.width == 30
    assert model.grid.height == 30
    assert model._num_people == 15
    assert model._num_banks == 3
    
    # Check that the model has the expected agents
    people = [agent for agent in model.agents if isinstance(agent, Person)]
    banks = [agent for agent in model.agents if isinstance(agent, Bank)]
    
    assert len(people) == 15
    assert len(banks) == 3

def test_model_save_to_csv(tmp_path):
    """Test that the model can save data to CSV files."""
    model = BankCraftModelBuilder.build_model(
        num_people=5, initial_money=1000, width=10, height=10
    )
    
    # Run a few steps to generate data
    model.run(steps=3)
    
    # Save to CSV
    base_filename = str(tmp_path / "test_output")
    model.save_to_csv(base_filename)
    
    # Check that the files were created
    import os
    assert os.path.exists(f"{base_filename}_agents.csv")
    assert os.path.exists(f"{base_filename}_transactions.csv")
    assert os.path.exists(f"{base_filename}_people.csv")

def test_add_and_remove_person():
    """Test that the model can add and remove people dynamically."""
    model = BankCraftModelBuilder.build_model(
        num_people=5, initial_money=1000, width=10, height=10
    )

    # Count initial active population
    initial_active_people = len([agent for agent in model.agents if isinstance(agent, Person) and agent.active])

    # Add a new person
    new_person = model.add_person(initial_money=1500)

    # Check that the person was added
    current_active_people = len([agent for agent in model.agents if isinstance(agent, Person) and agent.active])
    assert current_active_people == initial_active_people + 1
    assert new_person in model.agents
    assert new_person.active is True
    assert new_person.home is not None

    # Remove the person
    result = model.remove_person(new_person)

    # Check that the person was marked as inactive
    assert result is True
    assert new_person in model.agents  # Person is still in the model
    assert new_person.active is False  # But is marked as inactive
    
    # Check that the number of active people decreased
    final_active_people = len([agent for agent in model.agents if isinstance(agent, Person) and agent.active])
    assert final_active_people == initial_active_people

def test_add_and_remove_employer():
    """Test that the model can add and remove employers dynamically."""
    model = BankCraftModelBuilder.build_model(
        num_people=5, initial_money=1000, width=10, height=10
    )
    
    # Count initial employers
    initial_employers = len(model.employers)
    
    # Add a new employer
    new_employer = model.add_employer()
    
    # Check that the employer was added
    assert len(model.employers) == initial_employers + 1
    assert new_employer in model.employers
    assert new_employer.location is not None
    
    # Remove the employer
    result = model.remove_employer(new_employer)
    
    # Check that the employer was removed
    assert result is True
    assert len(model.employers) == initial_employers
    assert new_employer not in model.employers

