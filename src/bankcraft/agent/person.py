import random

import numpy as np
import pandas as pd

from bankcraft.agent.general_agent import GeneralAgent
from bankcraft.agent.merchant import Food, Clothes
from bankcraft.config import time_units, hunger_rate, fatigue_rate, social_rate, consumerism_rate, work_rate, motivation_threshold
from bankcraft.config import small_meal_avg_cost, medium_meal_avg_cost, large_meal_avg_cost
from bankcraft.motivation.motivation import Motivation
from bankcraft.motivation.motivation_state import NeutralState


class Person(GeneralAgent):
    def __init__(self, model,
                 initial_money):
        super().__init__(model)
        self.type = 'person'

        self._has_subscription = random.randint(0, 1)
        self._subscription_amount = self._has_subscription * random.randrange(0, 100)
        self._has_membership = random.randint(0, 1)
        self._membership_amount = self._has_membership * random.randrange(0, 100)

        self.motivation = Motivation(NeutralState, self)

        self.bank_accounts = self.assign_bank_account(model, initial_money)

        self.schedule_txn = pd.DataFrame()

        self.spending_prob = random.random()
        self.spending_amount = random.randrange(0, 100)

        self.target_location = None

        self._home = None
        self._work = None
        self._social_node = None
        self._social_network_weights = None
        self._friends = []

    @property
    def home(self):
        return self._home

    @home.setter
    def home(self, value):
        self._home = value

    @property
    def work(self):
        return self._work

    @work.setter
    def work(self, value):
        self._work = value

    @property
    def social_node(self):
        return self._social_node

    @social_node.setter
    def social_node(self, value):
        self._social_node = value

    @property
    def friends(self):
        return self._friends

    @friends.setter
    def friends(self, value):
        self._friends = value
        # highest value is the best friend
        self._partner = max(value, key=value.get)

    def assign_salary_info(self, employer, salary):
        self.salary = salary
        self.employer = employer
        self.work = employer.location
        self.housing_cost = self.salary * random.uniform(0.3, 0.4)
        self._housing_cost_frequency = random.choice([time_units['biweekly']])
        self._housing_cost_per_pay = self.housing_cost / time_units.convert(1, 'year', 'biweekly')
        self._set_schedule_txn()

    def _set_schedule_txn(self):
        #  include insurance, car lease, loan, tuition (limited time -> keep track of them in a counter)
        #  if the account balance is not enough they must be paid in future including the interest
        txn_list = [['scheduled_expenses', 'Amount', 'pay_date', 'Receiver'],
                    ['Rent/Mortgage', self._housing_cost_per_pay, self._housing_cost_frequency,
                     self.model.invoicer["rent/mortgage"]],
                    ['Utilities', np.random.normal(loc=200, scale=50), time_units['week'], self.model.invoicer["utilities"]],
                    ['Memberships', self._membership_amount, time_units['month'], self.model.invoicer["membership"]],
                    ['Subscriptions', self._subscription_amount, time_units['month'], self.model.invoicer["subscription"]],
                    ['Providers', random.randrange(10, 300), time_units['month'], self.model.invoicer["net_providers"]]
                    ]
        self.schedule_txn = pd.DataFrame(txn_list[1:], columns=txn_list[0])

    def pay_schedule_txn(self):
        for index, row in self.schedule_txn.iterrows():
            if self.model.steps % row['pay_date'] == 0:
                self.pay(receiver=row['Receiver'], amount=row['Amount'], txn_type='online',
                         description=row['scheduled_expenses'])

    def unscheduled_txn(self):
        if random.random() < 0.1:
            weight = self._social_network_weights
            recipient = random.choices(list(weight.keys()), weights=list(weight.values()), k=1)[0]
            self.adjust_social_network(recipient)
            amount = random.randrange(0, 100)
            if random.random() >= self.spending_prob:
                self.pay(amount=amount,
                         receiver=recipient,
                         txn_type='online',
                         description='social')

    def buy(self, motivation):
        # if there is a merchant agent in this location
        if self.model.grid.is_cell_empty(self.pos):
            return
        agents = self.model.grid.get_cell_list_contents([self.pos])
        # if the agent is a merchant

        for agent in agents:
            if motivation == 'small_meal' and isinstance(agent, Food):
                price = small_meal_avg_cost * random.uniform(0.5, 1.5)
                self.pay(agent, price, 'ACH', description='hunger')

            elif motivation == 'medium_meal' and isinstance(agent, Food):
                price = medium_meal_avg_cost * random.uniform(0.5, 1.5)
                self.pay(agent, price, 'ACH', description='hunger')

            elif motivation == 'large_meal' and isinstance(agent, Food):
                price = large_meal_avg_cost * random.uniform(0.7, 2.5)
                self.pay(agent, price, 'ACH', description='hunger')

            elif motivation == 'consumerism' and isinstance(agent, Clothes):
                if self.wealth > 0:
                    price = self.wealth * random.uniform(0.8, 0.95)
                    self.pay(price, agent, 'ACH', motivation)
                    return price
        return 0

    def set_social_network_weights(self):
        """Set weights for social connections with other people."""
        weight = {}
        for agent in self.model.agents:
            if isinstance(agent, Person) and agent != self:
                try:
                    weight[agent] = self.model.social_grid.edges[
                        self.social_node, agent.social_node
                    ]['weight']
                except KeyError:
                    # If edge doesn't exist in the graph, set weight to 0
                    weight[agent] = 0
        self._social_network_weights = weight

    def adjust_social_network(self, other_agent):
        self._social_network_weights[other_agent] += 0.1
        # have weights to be between 0 and 1
        self._social_network_weights[other_agent] = min(
            self._social_network_weights[other_agent], 1
        )

    def decision_maker(self):
        """
        This can adjust rates of motivation based on time of day, day of week, etc.
        and also decide whether to buy something or not
        """

        # check time, one hour to work increase work motivation
        if self.model.current_time.weekday() < 5 and self.model.current_time.hour == 8:
            self.motivation.update_state_value('WorkState', 100)

        if self.pos == self.home and self.motivation.state_values()['FatigueState'] > 0:
            if self.model.current_time.hour >= 22 or self.model.current_time.hour <= 6:
                self.motivation.update_state_value('FatigueState', -fatigue_rate * 6)
            else:
                self.motivation.update_state_value('FatigueState', -fatigue_rate * 3)

        elif self.pos == self.work:
            if self.model.current_time.weekday() < 5 and \
                    (9 <= self.model.current_time.hour <= 11 or 13 <= self.model.current_time.hour <= 16):
                self.motivation.update_state_value('WorkState', -0.4)
            elif (self.model.current_time.weekday() < 5 and self.model.current_time.hour > 17) or \
                    (self.model.current_time.weekday() >= 5):
                self.motivation.reset_one_motivation('WorkState')

        if self.target_location != self.pos:
            return
        elif self.motivation.present_state() == 'HungerState':
            hunger_value = self.motivation.state_values()['HungerState']
            if hunger_value < 2 * motivation_threshold:
                meal = random.choices(['small_meal', 'medium_meal', 'large_meal'], weights=[0.5, 0.25, 0.25], k=1)[0]
            else:
                meal = random.choices(['medium_meal', 'large_meal'], weights=[0.5, 0.5], k=1)[0]
            self.buy(meal)
            if meal == 'small_meal':
                value = hunger_value * 0.5
            else:
                value = hunger_value * random.uniform(0.8, 1)

            self.motivation.update_state_value('HungerState', -value)

        elif self.motivation.present_state() == 'ConsumerismState':
            self.buy('consumerism')
            self.motivation.reset_one_motivation('ConsumerismState')

        elif self.motivation.present_state() == 'SocialState':
            value = self.motivation.state_values()['SocialState']
            reduction_rate = np.random.beta(a=9, b=2, size=1)[0]
            self.motivation.update_state_value('SocialState', -value * reduction_rate)

    def update_people_records(self):
        agent_data = {
            "Step": self.model.steps,
            "AgentID": self.unique_id,
            "date_time": self.model.current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "location": self.pos,
            "account_balance": self.get_all_bank_accounts(),
            "motivations": self.motivation.state_values(),
        }
        self.model.datacollector.add_table_row("people", agent_data, ignore_missing=True)

    def step(self):
        self.move()
        self.pay_schedule_txn()
        # self.unscheduled_txn()
        self.motivation.step()
        self.decision_maker()
        self.update_people_records()

    @classmethod
    def create_agents(cls, model, n, initial_money):
        """Create multiple Person agents at once."""
        return [cls(model, initial_money) for _ in range(n)]
