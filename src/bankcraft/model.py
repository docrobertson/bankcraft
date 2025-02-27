import datetime
import random

import networkx as nx
import numpy as np
import pandas as pd
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid

from bankcraft.agent.bank import Bank
from bankcraft.agent.business import Business
from bankcraft.agent.employer import Employer
from bankcraft.agent.merchant import Food, Clothes
from bankcraft.agent.person import Person
from bankcraft.config import workplace_radius


class BankCraftModelBuilder:
    """Builder class for creating and configuring BankCraftModel instances.
    
    This class follows the builder pattern to separate model construction from model execution,
    making it easier to create different types of models with different configurations.
    
    Two main methods are provided:
    - build_default_model: Creates a fully configured model with all necessary components
    - build_custom_model: Creates a minimal model for custom configuration
    """
    
    @staticmethod
    def build_default_model(num_people=6, initial_money=1000,
                           num_banks=1, width=15, height=15):
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
        model = BankCraftModel(width, height)
        
        # Initialize banks
        model._num_banks = num_banks
        model.banks = [Bank(model) for _ in range(num_banks)]
        
        # Initialize businesses
        business_types = ["rent/mortgage", "utilities", "subscription", "membership", "net_providers"]
        model.invoicer = {b_type: Business(model, b_type) for b_type in business_types}
        
        # Calculate number of merchants and employers based on grid size
        model._num_merchant = width * height // 100
        model._num_employers = 5 * width * height // 100
        
        # Initialize employers
        model.employers = [Employer(model) for _ in range(model._num_employers)]
        model._put_employers_in_model()
        
        # Initialize social network
        model._num_people = num_people
        model.social_grid = nx.complete_graph(num_people)
        for (u, v) in model.social_grid.edges():
            model.social_grid.edges[u, v]['weight'] = 1 / (num_people - 1)
        
        # Initialize people, merchants, and set up social connections
        model._put_people_in_model(initial_money)
        model._put_clothes_merchants_in_model()
        model._put_food_merchants_in_model()
        model._set_best_friends()
        
        return model
    
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
        model = BankCraftModel(width, height)
        
        # Add custom initialization logic here
        # This method can be expanded based on specific customization needs
        
        return model


class BankCraftModel(Model):
    """Agent-based model for simulating financial transactions and behaviors.
    
    This is the core simulation engine of BankCraft. It manages all agents, 
    handles their interactions, and collects data about the simulation.
    
    Note: For creating model instances, use the BankCraftModelBuilder class
    rather than instantiating this class directly.
    
    Key features:
    - Spatial grid for agent placement and movement
    - Time-based simulation with configurable step size
    - Dynamic population changes (people moving in/out, businesses opening/closing)
    - Comprehensive data collection and analysis tools
    - Multiple ways to run the simulation (steps, duration, until date)
    """
    
    def __init__(self, width=15, height=15):
        """Initialize a bare BankCraftModel instance.
        
        Note: This constructor creates a minimal model. Use BankCraftModelBuilder
        to create a fully configured model.
        
        Args:
            width (int): Width of the grid
            height (int): Height of the grid
        """
        super().__init__()
        
        # Initialize basic properties
        self.grid = MultiGrid(width, height, torus=False)
        self._start_time = datetime.datetime(2023, 1, 1, 0, 0, 0)
        self._one_step_time = datetime.timedelta(minutes=10)
        self.current_time = self._start_time
        
        # Initialize empty collections
        self.banks = []
        self.employers = []
        self.invoicer = {}
        self._num_people = 0
        self._num_merchant = 0
        self._num_employers = 0
        self._num_banks = 0
        
        # Population dynamics parameters
        self.person_move_in_rate = 0.001  # 0.1% chance per step
        self.person_move_out_rate = 0.001  # 0.1% chance per step
        self.business_open_rate = 0.0005   # 0.05% chance per step
        self.business_close_rate = 0.0005  # 0.05% chance per step
        
        # Set up data collection
        self.setup_datacollector()

    def setup_datacollector(self):
        """Set up the data collector for the model."""
        self.datacollector = DataCollector(
            agent_reporters={'date_time': lambda a: a.model.current_time.strftime("%Y-%m-%d %H:%M:%S"),
                             'location': lambda a: a.pos,
                             'agent_type': lambda a: a.type,
                             'agent_home': lambda a: a.home if isinstance(a, Person) else a.location,
                             'agent_work': lambda a: a.work if isinstance(a, Person) else a.location,
                             },
            tables={"transactions": ["sender", "receiver", "amount", "step", "date_time",
                                     "txn_id", "txn_type", "sender_account_type", "description"],
                    "people": ['Step', 'AgentID', "date_time", "wealth", "location", "account_balance", "motivations"],
                    "agent_actions": ["agent_id", "agent_type", "step", "date_time", "action", "details", "location"]}
        )

    def _place_randomly_on_grid(self, agent):
        """Place an agent randomly on the grid.
        
        Args:
            agent: The agent to place
            
        Returns:
            tuple: The (x, y) coordinates where the agent was placed
        """
        x = self.random.randrange(self.grid.width)
        y = self.random.randrange(self.grid.height)
        self.grid.place_agent(agent, (x, y))
        return x, y

    def _put_employers_in_model(self):
        """Place employers on the grid and set their locations."""
        for employer in self.employers:
            location = self._place_randomly_on_grid(employer)
            employer.location = location

    def _put_people_in_model(self, initial_money):
        """Create people, place them on grid, and assign employers.
        
        This method is kept for backward compatibility.
        It uses the new add_people method internally.
        """
        return self.add_people(self._num_people, initial_money)

    def _assign_employer(self, person):
        """Assign an employer to a person based on distance."""
        # Check that all employers have locations
        if any(employer.location is None for employer in self.employers):
            raise ValueError("All employers must be placed on grid before assigning to people")
        
        closest_employer = min(self.employers, key=lambda x: self.get_distance(person.home, x.location))
        if self.get_distance(person.home, closest_employer.location) > workplace_radius:
            valid_employers = [employer for employer in self.employers]
        else:
            valid_employers = [employer for employer in self.employers
                         if self.get_distance(person.home, employer.location) <= workplace_radius]
        
        total_distance = sum([self.get_distance(person.home, employer.location) for employer in valid_employers])
        if total_distance == 0:
            return closest_employer
        
        employer_probabilities = [self.get_distance(person.home, employer.location) / total_distance 
                                for employer in valid_employers]
        employer = self.random.choices(valid_employers, employer_probabilities)[0]
        return employer

    def _put_food_merchants_in_model(self):
        """Create and place food merchants on the grid."""
        merchants = Food.create_agents(model=self, n=self._num_merchant, price=10, initial_money=1000)
        for merchant in merchants:
            merchant.location = self._place_randomly_on_grid(merchant)

    def _put_clothes_merchants_in_model(self):
        """Create and place clothes merchants on the grid."""
        merchants = Clothes.create_agents(model=self, n=self._num_merchant // 2, price=10, initial_money=1000)
        for merchant in merchants:
            merchant.location = self._place_randomly_on_grid(merchant)

    def _set_best_friends(self):
        """Assign friends to each person agent."""
        person_agents = [agent for agent in self.agents if isinstance(agent, Person)]

        for person in person_agents:
            number_of_friends = self.random.randint(1, len(person_agents) - 1)
            friends = self.random.sample(person_agents, number_of_friends)
            friendship_weights = [self.random.random() for _ in range(number_of_friends)]
            friends = dict(zip(friends, friendship_weights))
            person.friends = friends

    def add_person(self, initial_money=1000, social_node=None):
        """Add a new person to the model.
        
        This unified method is used for both initial setup and dynamic population changes.
        
        Args:
            initial_money (int): Initial money for the person
            social_node (int, optional): Social node ID for the person. If None, one will be assigned.
            
        Returns:
            Person: The newly created person
        """
        # Create a new person
        person = Person(self, initial_money)
        
        # Assign home and place on grid
        person.home = self._place_randomly_on_grid(person)
        
        # Assign employer if employers exist
        if self.employers:
            employer = self._assign_employer(person)
            employer.add_employee(person)
            person.work = employer.location
        
        # Assign social node if provided, otherwise use the unique_id
        person.social_node = social_node if social_node is not None else person.unique_id
        
        # Update social network
        person_agents = [agent for agent in self.agents if isinstance(agent, Person) and agent.active]
        if person_agents:
            # Assign friends
            number_of_friends = self.random.randint(1, min(5, len(person_agents)))
            friends = self.random.sample(person_agents, number_of_friends)
            friendship_weights = [self.random.random() for _ in range(number_of_friends)]
            friends = dict(zip(friends, friendship_weights))
            person.friends = friends
            
            # Add this person as a friend to some existing people
            for potential_friend in person_agents:
                if self.random.random() < 0.2:  # 20% chance to become friends
                    if person not in potential_friend.friends:
                        potential_friend.friends[person] = self.random.random()
        
        # Log the action
        person.log_action("created", "New person moved into the community")
        
        return person

    def add_people(self, num_people, initial_money=1000):
        """Add multiple people to the model at once.
        
        Args:
            num_people (int): Number of people to add
            initial_money (int): Initial money for each person
            
        Returns:
            list: The newly created people
        """
        # First make sure employers are placed
        if not self.employers or any(employer.location is None for employer in self.employers):
            self._put_employers_in_model()
            
        people = []
        for i in range(num_people):
            person = self.add_person(initial_money, social_node=i)
            people.append(person)
            
        # Set social network weights after all people are added
        for person in self.agents:
            if isinstance(person, Person) and person.active:
                person.set_social_network_weights()
                
        return people

    def remove_person(self, person=None):
        """Mark a person as inactive in the model.
        
        Instead of removing the person from the model, this method marks them as inactive
        so their information is still available for analysis.
        
        Args:
            person (Person, optional): The person to mark as inactive. If None, a random active person is selected.
            
        Returns:
            bool: True if a person was marked as inactive, False otherwise
        """
        active_person_agents = [agent for agent in self.agents if isinstance(agent, Person) and agent.active]
        if not active_person_agents:
            return False
        
        # Select a random person if none specified
        if person is None:
            person = self.random.choice(active_person_agents)
        elif not person.active:
            # Person is already inactive
            return False
        
        # Remove from employer
        for employer in self.employers:
            employee = employer.find_employee(person)
            if employee:
                employer.remove_employee(person)
                break
        
        # Remove from friends' lists but keep record of the relationship
        for other_person in active_person_agents:
            if person in other_person.friends:
                # We could keep the friendship but mark it as inactive
                # For simplicity, we'll remove it for now
                del other_person.friends[person]
        
        # Log the action
        person.log_action("left", "Person moved out of the community")
        
        # Mark as inactive instead of removing
        person.active = False
        
        # Remove from grid but keep in model
        self.grid.remove_agent(person)
        
        return True

    def add_employer(self):
        """Add a new employer to the model dynamically.
        
        Returns:
            Employer: The newly created employer
        """
        employer = Employer(self)
        self.employers.append(employer)
        employer.location = self._place_randomly_on_grid(employer)
        employer.log_action("created", "New business opened")
        return employer

    def remove_employer(self, employer=None):
        """Remove an employer from the model dynamically.
        
        Args:
            employer (Employer, optional): The employer to remove. If None, a random employer is selected.
            
        Returns:
            bool: True if an employer was removed, False otherwise
        """
        if not self.employers:
            return False
        
        # Select a random employer if none specified
        if employer is None:
            employer = self.random.choice(self.employers)
        
        # Reassign employees to other employers
        for employee in employer.employees.copy():
            person = employee['person']
            employer.remove_employee(person)
            
            if len(self.employers) > 1:
                # Find a new employer (excluding the one being removed)
                new_employers = [e for e in self.employers if e != employer]
                new_employer = self.random.choice(new_employers)
                new_employer.add_employee(person)
                person.work = new_employer.location
                person.log_action("employment_change", f"Reassigned to employer {new_employer.unique_id}")
        
        # Log the action before removal
        employer.log_action("removed", "Business closed")
        
        # Remove from model
        self.employers.remove(employer)
        employer.remove_from_model()
        
        return True

    def handle_population_dynamics(self):
        """Handle dynamic population changes based on configured rates."""
        # Handle person move-ins
        if self.random.random() < self.person_move_in_rate:
            self.add_person()
        
        # Handle person move-outs
        if self.random.random() < self.person_move_out_rate:
            # Only consider active people for moving out
            active_person_agents = [agent for agent in self.agents if isinstance(agent, Person) and agent.active]
            if active_person_agents:
                self.remove_person()
        
        # Handle business openings
        if self.random.random() < self.business_open_rate:
            self.add_employer()
        
        # Handle business closings
        if self.random.random() < self.business_close_rate and len(self.employers) > 1:
            self.remove_employer()

    def step(self):
        """Execute one step of the model."""
        # Handle dynamic population changes
        self.handle_population_dynamics()
        
        # Use Mesa's built-in AgentSet functionality for random activation
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)
        self.current_time += self._one_step_time

    def run(self, steps=None, duration=None, until_date=None):
        """Run the model for a specified number of steps, duration, or until a specific date.
        
        Args:
            steps (int, optional): Number of steps to run. Defaults to None.
            duration (str, optional): Duration to run as a string (e.g., "2 days, 4 hours"). Defaults to None.
            until_date (datetime.datetime, optional): Date to run until. Defaults to None.
            
        Returns:
            BankCraftModel: The model instance
            
        Raises:
            ValueError: If no run criteria are provided or if multiple criteria are provided
        """
        # Validate input parameters
        if sum(param is not None for param in [steps, duration, until_date]) != 1:
            raise ValueError("Exactly one of steps, duration, or until_date must be provided")
        
        # Calculate number of steps to run
        if steps is not None:
            steps_to_run = steps
        elif duration is not None:
            from bankcraft.config import time_units
            steps_to_run = time_units.time_str_to_steps(duration)
        elif until_date is not None:
            # Calculate time difference and convert to steps
            time_diff = until_date - self.current_time
            minutes_diff = time_diff.total_seconds() / 60
            steps_to_run = int(minutes_diff / self._one_step_time.total_seconds() * 60)
            
            # Ensure we don't run negative steps
            if steps_to_run <= 0:
                return self
        
        # Run the model for the calculated number of steps
        for _ in range(steps_to_run):
            self.step()
            
            # If running until a date, check if we've reached or passed it
            if until_date is not None and self.current_time >= until_date:
                break
        
        return self

    def run_until(self, end_date):
        """Run the model until a specific date is reached.
        
        Args:
            end_date (datetime.datetime): The date to run until
            
        Returns:
            BankCraftModel: The model instance
        """
        return self.run(until_date=end_date)

    def save_to_csv(self, base_filename=""):
        """
        Save the model data to CSV files.
        
        Args:
            base_filename (str): Optional prefix for the CSV filenames. If empty,
                               files will be named 'agents.csv', 'transactions.csv', etc.
        """
        prefix = f"{base_filename}_" if base_filename else ""
        self.datacollector.get_agent_vars_dataframe().to_csv(f"{prefix}agents.csv")
        self.get_transactions().to_csv(f"{prefix}transactions.csv")
        self.get_people().to_csv(f"{prefix}people.csv")

    def get_transactions(self):
        """Get transactions data as a DataFrame."""
        return self.datacollector.get_table_dataframe("transactions")

    def get_agents(self):
        """Get agent data as a DataFrame."""
        return self.datacollector.get_agent_vars_dataframe()

    def get_people(self):
        """Get people data as a DataFrame with expanded columns for accounts and motivations."""
        people = self.datacollector.get_table_dataframe("people")
        if people.empty:
            return people

        # Expand motivations into separate columns
        if 'motivations' in people.columns:
            people = pd.concat([people.drop(['motivations'], axis=1), 
                              people['motivations'].apply(pd.Series)], axis=1)

        # Expand account balances into separate columns
        if 'account_balance' in people.columns and not people['account_balance'].empty:
            new_column_names = {i: f'account_{i}' for i in range(len(people["account_balance"]) + 1)}
            accounts = people["account_balance"].apply(pd.Series)
            accounts.columns = [new_column_names.get(col, col) for col in accounts.columns]
            people = pd.concat([people.drop(['account_balance'], axis=1), accounts], axis=1)
            
        # Add active status information
        # This requires looking up the current active status of each agent
        agent_id_to_active = {}
        for agent in self.agents:
            if isinstance(agent, Person):
                agent_id_to_active[agent.unique_id] = agent.active
                
        if agent_id_to_active:
            people['active'] = people['AgentID'].map(agent_id_to_active).fillna(False)
            
        return people

    def get_agent_actions(self, agent_id=None):
        """Get the action log for a specific agent or all agents.
        
        Args:
            agent_id (int, optional): The ID of the agent to get actions for. 
                                     If None, returns actions for all agents.
                                     
        Returns:
            pandas.DataFrame: A DataFrame containing the agent's actions
        """
        actions = self.datacollector.get_table_dataframe("agent_actions")
        if actions.empty:
            return actions
            
        if agent_id is not None:
            actions = actions[actions["agent_id"] == agent_id]
            
        # Sort by step and date_time
        actions = actions.sort_values(by=["step", "date_time"])
        
        return actions
        
    def get_agent_diary(self, agent_id):
        """Get a formatted diary of an agent's actions.
        
        Args:
            agent_id (int): The ID of the agent to get the diary for
            
        Returns:
            str: A formatted string containing the agent's diary
        """
        actions = self.get_agent_actions(agent_id)
        if actions.empty:
            return f"No actions recorded for agent {agent_id}"
            
        # Get agent type
        agent_type = actions.iloc[0]["agent_type"]
        
        diary = f"Diary for {agent_type} (ID: {agent_id}):\n"
        diary += "=" * 80 + "\n\n"
        
        current_step = None
        current_date = None
        
        for _, row in actions.iterrows():
            step = row["step"]
            date_time = row["date_time"]
            action = row["action"]
            details = row["details"]
            location = row["location"]
            
            # Add headers for new steps/dates
            if current_step != step:
                current_step = step
                diary += f"\nStep {step}:\n"
                diary += "-" * 40 + "\n"
            
            if current_date != date_time:
                current_date = date_time
                diary += f"Time: {date_time}\n"
            
            # Add the action entry
            diary += f"  • {action}: {details}"
            if location:
                diary += f" (at location {location})"
            diary += "\n"
        
        return diary

    def get_all_agents_on_grid(self):
        """Get all agents on the grid.
        
        Returns:
            list: A list of all agents on the grid
        """
        all_agents = []
        for cell in self.grid.coord_iter():
            cell_content, pos = cell
            all_agents.extend(cell_content)
        return all_agents

    @staticmethod
    def get_distance(pos_1, pos_2):
        """Calculate the Euclidean distance between two positions.
        
        Args:
            pos_1 (tuple): First position (x, y)
            pos_2 (tuple): Second position (x, y)
            
        Returns:
            float: The distance between the positions
        """
        x1, y1 = pos_1
        x2, y2 = pos_2
        return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
