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

def test_can_run_model(model):
    model = BankCraftModel(num_people=100, initial_money=1000, num_banks=1, width=50, height=50)
    current_time = model.current_time
    model.step()
    assert model.current_time == current_time + model._one_step_time

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

