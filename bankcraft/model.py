import datetime

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


class BankCraftModel(Model):
    def __init__(self, num_people=6, initial_money=1000,
                 num_banks=1, width=15, height=15):
        super().__init__()
        self._num_people = num_people
        self._num_merchant = width * height // 100
        self._num_employers = 5 * width * height // 100

        self._num_banks = num_banks
        self.banks = [Bank(self) for _ in range(self._num_banks)]

        business_types = ["rent/mortgage", "utilities", "subscription", "membership", "net_providers"]
        self.invoicer = {b_type: Business(self, b_type) for b_type in business_types}

        self.employers = [Employer(self) for _ in range(self._num_employers)]
        self.social_grid = nx.complete_graph(self._num_people)
        for (u, v) in self.social_grid.edges():
            self.social_grid.edges[u, v]['weight'] = 1 / (self._num_people - 1)

        self.grid = MultiGrid(width, height, torus=False)
        self._start_time = datetime.datetime(2023, 1, 1, 0, 0, 0)
        self._one_step_time = datetime.timedelta(minutes=10)
        self.current_time = self._start_time
        self.setup_datacollector()

        # Initialize all agents
        self._put_employers_in_model()
        self._put_people_in_model(initial_money)
        self._put_clothes_merchants_in_model()
        self._put_food_merchants_in_model()
        self._set_best_friends()

    def setup_datacollector(self):
        self.datacollector = DataCollector(
            agent_reporters={'date_time': lambda a: a.model.current_time.strftime("%Y-%m-%d %H:%M:%S"),
                             'location': lambda a: a.pos,
                             'agent_type': lambda a: a.type,
                             'agent_home': lambda a: a.home if isinstance(a, Person) else a.location,
                             'agent_work': lambda a: a.work if isinstance(a, Person) else a.location,
                             },
            tables={"transactions": ["sender", "receiver", "amount", "step", "date_time",
                                     "txn_id", "txn_type", "sender_account_type", "description"],
                    "people": ['Step', 'AgentID', "date_time", "wealth", "location", "account_balance", "motivations"]}

        )

    def _place_randomly_on_grid(self, agent):
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
        """Create people, place them on grid, and assign employers."""
        # First make sure employers are placed
        if not self.employers or any(employer.location is None for employer in self.employers):
            self._put_employers_in_model()
        
        people = Person.create_agents(model=self, n=self._num_people, initial_money=initial_money)
        for i, person in enumerate(people):
            person.home = self._place_randomly_on_grid(person)
            employer = self._assign_employer(person)
            employer.add_employee(person)
            person.work = employer.location
            person.social_node = i

        for person in self.agents:
            if isinstance(person, Person):
                person.set_social_network_weights()

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
        merchants = Food.create_agents(model=self, n=self._num_merchant, price=10, initial_money=1000)
        for merchant in merchants:
            merchant.location = self._place_randomly_on_grid(merchant)

    def _put_clothes_merchants_in_model(self):
        merchants = Clothes.create_agents(model=self, n=self._num_merchant // 2, price=10, initial_money=1000)
        for merchant in merchants:
            merchant.location = self._place_randomly_on_grid(merchant)

    def _set_best_friends(self):
        person_agents = [agent for agent in self.agents if isinstance(agent, Person)]

        for person in person_agents:
            number_of_friends = self.random.randint(1, len(person_agents) - 1)
            friends = self.random.sample(person_agents, number_of_friends)
            friendship_weights = [self.random.random() for _ in range(number_of_friends)]
            friends = dict(zip(friends, friendship_weights))
            person.friends = friends

    def step(self):
        """Execute one step of the model."""
        # Use Mesa's built-in AgentSet functionality for random activation
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)
        self.current_time += self._one_step_time

    def run(self, no_steps):
        """Run the model for a specified number of steps."""
        for i in range(no_steps):
            self.step()
        return self

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
            
        return people

    def get_all_agents_on_grid(self):
        all_agents = []
        for cell in self.grid.coord_iter():
            cell_content, pos = cell
            all_agents.extend(cell_content)
        return all_agents

    @staticmethod
    def get_distance(pos_1, pos_2):
        x1, y1 = pos_1
        x2, y2 = pos_2
        return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
