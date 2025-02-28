"""
Tests for the BankCraftModelBuilder class.
"""
import pytest
import datetime
import networkx as nx

from bankcraft.model import BankCraftModel, BankCraftModelBuilder
from bankcraft.agent import Person, Bank, Employer, Business
from bankcraft.agent.merchant import Food, Clothes

@pytest.fixture
def default_model():
    """Create a default model instance for testing."""
    return BankCraftModelBuilder.build_default_model(
        num_people=10, 
        initial_money=1000, 
        num_banks=2, 
        width=20, 
        height=20
    )

@pytest.fixture
def custom_model():
    """Create a custom model instance for testing."""
    return BankCraftModelBuilder.build_custom_model(width=30, height=30)

def test_build_default_model_dimensions():
    """Test that the default model has the expected dimensions."""
    model = BankCraftModelBuilder.build_default_model(width=25, height=30)
    assert model.grid.width == 25
    assert model.grid.height == 30

def test_build_default_model_agents():
    """Test that the default model has the expected agents."""
    model = BankCraftModelBuilder.build_default_model(
        num_people=15, 
        initial_money=2000, 
        num_banks=3
    )
    
    # Check agent counts
    people = [agent for agent in model.agents if isinstance(agent, Person)]
    banks = [agent for agent in model.agents if isinstance(agent, Bank)]
    employers = [agent for agent in model.agents if isinstance(agent, Employer)]
    food_merchants = [agent for agent in model.agents if isinstance(agent, Food)]
    clothes_merchants = [agent for agent in model.agents if isinstance(agent, Clothes)]
    
    assert len(people) == 15
    assert len(banks) == 3
    assert len(employers) == model._num_employers
    assert len(food_merchants) == model._num_merchant
    assert len(clothes_merchants) == model._num_merchant // 2

def test_build_default_model_initial_money():
    """Test that people in the default model have the expected initial money."""
    initial_money = 2500
    model = BankCraftModelBuilder.build_default_model(
        num_people=5, 
        initial_money=initial_money
    )
    
    people = [agent for agent in model.agents if isinstance(agent, Person)]
    
    # Check that each person has the expected wealth
    for person in people:
        assert person.wealth == initial_money

def test_build_custom_model_empty():
    """Test that the custom model starts empty."""
    model = BankCraftModelBuilder.build_custom_model()
    
    # Check that the model has no agents of these types
    assert len([agent for agent in model.agents if isinstance(agent, Person)]) == 0
    assert len([agent for agent in model.agents if isinstance(agent, Bank)]) == 0
    assert len([agent for agent in model.agents if isinstance(agent, Employer)]) == 0
    assert len([agent for agent in model.agents if isinstance(agent, Food)]) == 0
    assert len([agent for agent in model.agents if isinstance(agent, Clothes)]) == 0
    
    # Check that collections are initialized but empty
    assert model.banks == []
    assert model.employers == []
    assert model.invoicer == {}

def test_build_custom_model_dimensions():
    """Test that the custom model has the expected dimensions."""
    model = BankCraftModelBuilder.build_custom_model(width=40, height=50)
    assert model.grid.width == 40
    assert model.grid.height == 50

def test_default_model_social_network(default_model):
    """Test that the default model has a properly initialized social network."""
    # Check that the social grid is initialized
    assert hasattr(default_model, 'social_grid')
    assert isinstance(default_model.social_grid, nx.Graph)
    
    # Check that the social grid has the expected number of nodes
    assert default_model.social_grid.number_of_nodes() == default_model._num_people
    
    # Check that the social grid is a complete graph
    assert default_model.social_grid.number_of_edges() == (default_model._num_people * (default_model._num_people - 1)) // 2
    
    # Check that all edges have weights
    for u, v in default_model.social_grid.edges():
        assert 'weight' in default_model.social_grid.edges[u, v]

def test_default_model_time_initialization(default_model):
    """Test that the default model has properly initialized time settings."""
    assert default_model.current_time == datetime.datetime(2024, 5, 1, 8, 0, 0)
    assert default_model._one_step_time == datetime.timedelta(minutes=10)

def test_default_model_data_collection(default_model):
    """Test that the default model has properly initialized data collection."""
    assert hasattr(default_model, 'datacollector')
    
    # Run a step and check that data is collected
    default_model.step()
    
    # Check that agent data was collected
    agent_data = default_model.datacollector.get_agent_vars_dataframe()
    assert not agent_data.empty
    
    # Check that the expected tables exist
    assert "transactions" in default_model.datacollector.tables
    assert "people" in default_model.datacollector.tables
    assert "agent_actions" in default_model.datacollector.tables

def test_custom_model_can_be_populated():
    """Test that a custom model can be populated with agents."""
    model = BankCraftModelBuilder.build_custom_model()
    
    # Add banks
    model._num_banks = 2
    model.banks = [Bank(model) for _ in range(model._num_banks)]
    
    # Add businesses - make sure to include all required business types
    business_types = ["rent/mortgage", "utilities", "subscription", "membership", "net_providers"]
    model.invoicer = {b_type: Business(model, b_type) for b_type in business_types}
    
    # Add employers
    model._num_employers = 3
    model.employers = [Employer(model) for _ in range(model._num_employers)]
    model._put_employers_in_model()
    
    # Initialize social network
    model._num_people = 5
    model.social_grid = nx.complete_graph(model._num_people)
    for (u, v) in model.social_grid.edges():
        model.social_grid.edges[u, v]['weight'] = 1 / (model._num_people - 1)
    
    # Add people
    model._put_people_in_model(initial_money=1000)
    
    # Add merchants
    model._num_merchant = 2
    model._put_food_merchants_in_model()
    model._put_clothes_merchants_in_model()
    
    # Check that agents were added
    assert len([agent for agent in model.agents if isinstance(agent, Person)]) == 5
    assert len([agent for agent in model.agents if isinstance(agent, Employer)]) == 3
    assert len([agent for agent in model.agents if isinstance(agent, Food)]) == 2
    assert len([agent for agent in model.agents if isinstance(agent, Clothes)]) == 1
    
    # Check that all people have homes and work locations
    people = [agent for agent in model.agents if isinstance(agent, Person)]
    for person in people:
        assert person.home is not None
        assert person.work is not None 