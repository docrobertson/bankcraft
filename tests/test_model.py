from bankcraft.bankcraftmodel import BankCraftModel
from bankcraft.agent.employer import Employer
from bankcraft.agent.bank import Bank
from bankcraft.agent.person import Person
from bankcraft.agent.merchant import Merchant
from bankcraft.agent.business import Business
import pytest
import datetime
import networkx as nx
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid

initial_money = 500

@pytest.fixture
def model():
    """Create a model instance for testing."""
    model = BankCraftModel()
    return model

def test_put_employers_in_model(model):
    model._put_employers_in_model()
    employers = [agent for agent in model.agents if isinstance(agent, Employer)]
    assert len(employers) == model._num_employers

def test_put_people_in_model(model):
    model._put_people_in_model(initial_money)
    people = [agent for agent in model.agents if isinstance(agent, Person)]
    assert len(people) == model._num_people

def test_put_food_merchant_in_model(model):
    model._put_food_merchants_in_model()
    merchants = [agent for agent in model.agents if isinstance(agent, Merchant)]
    assert len(merchants) == model._num_merchant

def test_put_clothes_merchant_in_model(model):
    model._put_clothes_merchants_in_model()
    merchants = [agent for agent in model.agents if isinstance(agent, Merchant)]
    assert len(merchants) == model._num_merchant//2

def test_put_food_and_clothes_merchant_in_model(model):
    model._put_food_merchants_in_model()
    model._put_clothes_merchants_in_model()
    merchants = [agent for agent in model.agents if isinstance(agent, Merchant)]
    assert len(merchants) == model._num_merchant + model._num_merchant//2

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

@pytest.fixture
def model():
    """Create a model instance for testing without initialization."""
    return BankCraftModel()

def test_put_people_in_model(model):
    model._put_people_in_model(initial_money)
    people = [agent for agent in model.agents if isinstance(agent, Person)]
    assert len(people) == model._num_people

