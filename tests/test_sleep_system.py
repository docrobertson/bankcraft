import datetime
import pytest
from bankcraft.model import BankCraftModelBuilder

def test_sleep_system():
    """Test the new sleep system over a 48-hour period."""
    # Create a model with 5 people
    model = BankCraftModelBuilder.build_default_model(num_people=5, initial_money=1000)
    
    # Run the model for 48 hours (288 steps)
    total_steps = 288
    
    # Track sleep events
    sleep_starts = 0
    sleep_interruptions = 0
    wake_ups = 0
    activity_changes = 0
    
    # Run the model step by step
    for step in range(total_steps):
        model.step()
        
        # Check the agent actions for this step
        actions = model.datacollector.get_table_dataframe("agent_actions")
        if not actions.empty:
            # Filter for the most recent step
            step_actions = actions[actions["step"] == model.steps - 1]
            
            # Count sleep-related events
            for _, action in step_actions.iterrows():
                if action["action"] == "sleep":
                    if "Went back to sleep" in action["details"]:
                        sleep_interruptions += 1
                    else:
                        sleep_starts += 1
                elif action["action"] == "wake":
                    wake_ups += 1
                elif action["action"] == "activity_change":
                    activity_changes += 1
    
    # Get people data
    people_data = model.get_people()
    
    # Verify sleep system functionality
    assert sleep_starts > 0, "No sleep starts recorded"
    assert wake_ups > 0, "No wake ups recorded"
    assert activity_changes > 0, "No activity changes recorded"
    
    # Check that people have different activities
    activities = people_data["activity"].unique()
    assert len(activities) > 1, "Only one type of activity recorded"
    
    # Verify that the model started at the correct time
    assert model._start_time == datetime.datetime(2024, 5, 1, 8, 0, 0), "Model did not start at the correct time"
    
    # Get a sample person
    person_agents = [agent for agent in model.agents if agent.type == 'person']
    if person_agents:
        person = person_agents[0]
        
        # Verify person has activity tracking
        assert hasattr(person, '_current_activity'), "Person does not have _current_activity attribute"
        assert person._current_activity in ['none', 'sleeping', 'working', 'eating', 'shopping', 'socializing'], \
            f"Unexpected activity: {person._current_activity}"

def test_activity_tracking():
    """Test that activities are properly tracked and logged."""
    # Create a model with 1 person
    model = BankCraftModelBuilder.build_default_model(num_people=1, initial_money=1000)
    person = next(agent for agent in model.agents if agent.type == 'person')
    
    # Set initial activity
    person._current_activity = 'none'
    person._last_location = person.pos
    
    # Change activity and verify logging
    person._set_activity('working')
    
    # Get the most recent action
    actions = model.datacollector.get_table_dataframe("agent_actions")
    if not actions.empty:
        latest_action = actions.iloc[-1]
        assert latest_action["action"] == "activity_change", "Activity change not logged"
        assert "Changed activity from 'none' to 'working'" in latest_action["details"], "Activity change details incorrect"
    
    # Change location but not activity
    old_pos = person.pos
    new_pos = ((old_pos[0] + 1) % model.grid.width, (old_pos[1] + 1) % model.grid.height)
    model.grid.move_agent(person, new_pos)
    person._last_location = None  # Reset to force location change detection
    
    # Set same activity but at new location
    person._set_activity('working')
    
    # Verify location change is detected
    actions = model.datacollector.get_table_dataframe("agent_actions")
    if not actions.empty:
        latest_actions = actions.tail(2)
        location_change_logged = any("activity_change" in action["action"] for _, action in latest_actions.iterrows())
        assert location_change_logged, "Location change with same activity not detected"

def test_sleep_cycle():
    """Test the complete sleep cycle from starting sleep to waking up."""
    # Create a model with 1 person
    model = BankCraftModelBuilder.build_default_model(num_people=1, initial_money=1000)
    person = next(agent for agent in model.agents if agent.type == 'person')
    
    # Set up conditions for sleep
    # Move to home
    model.grid.move_agent(person, person.home)
    
    # Set time to evening
    evening_time = datetime.datetime(2024, 5, 1, 21, 0, 0)
    model.current_time = evening_time
    
    # Ensure fatigue is high enough
    person.motivation.update_state_value('SleepState', 30)
    
    # Trigger decision making
    person.decision_maker()
    
    # Verify sleep started
    assert person._current_activity == 'sleeping', "Person did not start sleeping"
    assert person._sleep_start_time is not None, "Sleep start time not set"
    assert person._planned_sleep_duration is not None, "Sleep duration not planned"
    assert person._wakeup_time is not None, "Wakeup time not set"
    
    # Fast forward to morning
    morning_time = datetime.datetime(2024, 5, 2, 7, 30, 0)
    model.current_time = morning_time
    model.steps = person._wakeup_time  # Ensure we've reached the wakeup time
    
    # Trigger decision making again
    person.decision_maker()
    
    # Verify person woke up
    assert person._current_activity != 'sleeping', "Person did not wake up"
    assert person._sleep_start_time is None, "Sleep start time not reset"
    assert person._planned_sleep_duration is None, "Sleep duration not reset"
    assert person._wakeup_time is None, "Wakeup time not reset" 