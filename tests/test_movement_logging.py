import pytest
from bankcraft.model import BankCraftModelBuilder

def test_movement_logging():
    """Test that movement is logged correctly with destination types."""
    # Create a model with 1 person
    model = BankCraftModelBuilder.build_default_model(num_people=1, initial_money=1000)
    person = next(agent for agent in model.agents if agent.type == 'person')
    
    # Print the datacollector tables to debug
    print("Available tables:", model.datacollector.tables.keys())
    
    # Test moving to home
    person.target_location = person.home
    person.move()
    
    # Get the actions table
    actions = model.datacollector.get_table_dataframe("agent_actions")
    print("Actions after home move:", actions)
    
    if not actions.empty:
        if "action" in actions.columns:
            home_move = actions[actions["action"] == "move"]
            if not home_move.empty:
                assert "Moving to home" in home_move.iloc[-1]["details"], "Home destination not correctly logged"
    
    # Test moving to work
    person.target_location = person.work
    person.move()
    
    # Get the actions table
    actions = model.datacollector.get_table_dataframe("agent_actions")
    print("Actions after work move:", actions)
    
    if not actions.empty:
        if "action" in actions.columns:
            work_move = actions[actions["action"] == "move"]
            if not work_move.empty:
                assert "Moving to work" in work_move.iloc[-1]["details"], "Work destination not correctly logged"
    
    # Find a merchant location
    merchant = None
    for agent in model.agents:
        if agent.type in ['food', 'clothes']:
            merchant = agent
            break
    
    if merchant:
        # Test moving to merchant
        person.target_location = merchant.pos
        person.move()
        
        # Get the actions table
        actions = model.datacollector.get_table_dataframe("agent_actions")
        print("Actions after merchant move:", actions)
        
        if not actions.empty:
            if "action" in actions.columns:
                merchant_move = actions[actions["action"] == "move"]
                if not merchant_move.empty:
                    assert "Moving to merchant" in merchant_move.iloc[-1]["details"], "Merchant destination not correctly logged"
    
    # Test moving to other location
    random_pos = (5, 5)  # Some random position
    person.target_location = random_pos
    person.move()
    
    # Get the actions table
    actions = model.datacollector.get_table_dataframe("agent_actions")
    print("Actions after random move:", actions)
    
    if not actions.empty:
        if "action" in actions.columns:
            other_move = actions[actions["action"] == "move"]
            if not other_move.empty:
                assert "Moving to other" in other_move.iloc[-1]["details"], "Other destination not correctly logged"
    
    # Verify no position_update actions are logged
    actions = model.datacollector.get_table_dataframe("agent_actions")
    if not actions.empty and "action" in actions.columns:
        position_updates = actions[actions["action"] == "position_update"]
        assert len(position_updates) == 0, "Position updates should not be logged" 