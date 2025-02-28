import random

import numpy as np
import pandas as pd

from bankcraft.agent.general_agent import GeneralAgent
from bankcraft.agent.merchant import Food, Clothes
from bankcraft.config import time_units, fatigue_rate, motivation_threshold
from bankcraft.config import small_meal_avg_cost, medium_meal_avg_cost, large_meal_avg_cost
from bankcraft.motivation.motivation import Motivation
from bankcraft.motivation.motivation_state import NeutralState


class Person(GeneralAgent):
    def __init__(self, model,
                 initial_money):
        super().__init__(model)
        self.type = 'person'
        self.active = True  # Flag to indicate if the person is active in the model

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
        
        # Activity tracking
        self._current_activity = 'none'
        self._last_location = None
        self._sleep_start_time = None
        self._planned_sleep_duration = None  # in steps
        self._wakeup_time = None  # in steps
        self._sleep_interrupted = False

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
                self.log_action("pay_bill", f"Paid {row['scheduled_expenses']} bill of {row['Amount']} to {row['Receiver'].type}")

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
                self.log_action("social_payment", f"Sent {amount} to friend (ID: {recipient.unique_id})")

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
                self.log_action("buy_food", f"Bought small meal for {price}")
                self._set_activity('eating')

            elif motivation == 'medium_meal' and isinstance(agent, Food):
                price = medium_meal_avg_cost * random.uniform(0.5, 1.5)
                self.pay(agent, price, 'ACH', description='hunger')
                self.log_action("buy_food", f"Bought medium meal for {price}")
                self._set_activity('eating')

            elif motivation == 'large_meal' and isinstance(agent, Food):
                price = large_meal_avg_cost * random.uniform(0.7, 2.5)
                self.pay(agent, price, 'ACH', description='hunger')
                self.log_action("buy_food", f"Bought large meal for {price}")
                self._set_activity('eating')

            elif motivation == 'consumerism' and isinstance(agent, Clothes):
                if self.wealth > 0:
                    price = self.wealth * random.uniform(0.8, 0.95)
                    self.pay(price, agent, 'ACH', motivation)
                    self.log_action("buy_clothes", f"Bought clothes for {price}")
                    self._set_activity('shopping')
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

    def _set_activity(self, activity):
        """Set the current activity and log if it changed."""
        if self._current_activity != activity or self._last_location != self.pos:
            old_activity = self._current_activity
            self._current_activity = activity
            self._last_location = self.pos
            
            # Log the activity change
            if old_activity != activity:
                self.log_action("activity_change", f"Changed activity from '{old_activity}' to '{activity}' at {self.model.current_time.strftime('%H:%M')}")

    def _should_start_sleeping(self):
        """Determine if the person should start sleeping."""
        # Must be at home
        if self.pos != self.home:
            return False
            
        # Must be evening hours (9 PM to 11 PM)
        hour = self.model.current_time.hour
        if not (21 <= hour <= 23):
            return False
            
        # Must have some fatigue
        if self.motivation.state_values()['SleepState'] <= 0:
            return False
            
        # Already sleeping
        if self._current_activity == 'sleeping':
            return False
            
        return True
        
    def _should_wake_up(self):
        """Determine if the person should wake up."""
        # If not sleeping, can't wake up
        if self._current_activity != 'sleeping':
            return False
            
        # Check if it's morning (7 AM to 8 AM)
        hour = self.model.current_time.hour
        if 7 <= hour <= 8:
            return True
            
        # Check if planned sleep duration is over
        if self.model.steps >= self._wakeup_time:
            return True
            
        # Random chance of waking up during the night (very low probability)
        if random.random() < 0.01:  # 1% chance per step
            self._sleep_interrupted = True
            return True
            
        return False
        
    def _start_sleeping(self):
        """Start sleeping process."""
        self._set_activity('sleeping')
        self._sleep_start_time = self.model.steps
        
        # Determine sleep duration (6 to 10 hours)
        sleep_hours = random.uniform(6, 10)
        self._planned_sleep_duration = int(sleep_hours * 6)  # 6 steps per hour
        self._wakeup_time = self.model.steps + self._planned_sleep_duration
        
        # Log the sleep start
        self.log_action("sleep", f"Started sleeping at {self.model.current_time.strftime('%H:%M')}. " +
                        f"Planning to sleep for {sleep_hours:.1f} hours with current fatigue of {self.motivation.state_values()['SleepState']:.1f}")
        
    def _wake_up(self):
        """Wake up from sleep."""
        was_sleeping_for = self.model.steps - self._sleep_start_time
        hours_slept = was_sleeping_for / 6  # 6 steps per hour
        
        # Log the wake up
        if self._sleep_interrupted:
            self.log_action("wake", f"Woke up unexpectedly after {hours_slept:.1f} hours of sleep at {self.model.current_time.strftime('%H:%M')}")
            
            # Decide to go back to sleep for a shorter duration
            self._set_activity('none')
            self._sleep_interrupted = False
            
            # 80% chance to go back to sleep if woken up at night
            if self.model.current_time.hour < 6 and random.random() < 0.8:
                # Sleep for 1-3 more hours
                self._start_sleeping()
                self._planned_sleep_duration = int(random.uniform(1, 3) * 6)  # 6 steps per hour
                self._wakeup_time = self.model.steps + self._planned_sleep_duration
                self.log_action("sleep", f"Went back to sleep after waking up. Planning to sleep for {self._planned_sleep_duration/6:.1f} more hours")
        else:
            self.log_action("wake", f"Woke up naturally after {hours_slept:.1f} hours of sleep at {self.model.current_time.strftime('%H:%M')}")
            self._set_activity('none')
            self._sleep_start_time = None
            self._planned_sleep_duration = None
            self._wakeup_time = None

    def decision_maker(self):
        """
        This can adjust rates of motivation based on time of day, day of week, etc.
        and also decide whether to buy something or not
        """
        # Check if should start sleeping
        if self._should_start_sleeping():
            self._start_sleeping()
            return  # Skip other decisions when starting to sleep
            
        # Check if should wake up
        if self._should_wake_up():
            self._wake_up()
            
        # If sleeping, reduce fatigue and skip other decisions
        if self._current_activity == 'sleeping':
            # Calculate fatigue reduction (should reach ~0 after 8 hours)
            # 8 hours = 48 steps, so we need to reduce by ~fatigue/48 per step
            current_fatigue = self.motivation.state_values()['SleepState']
            
            # Calculate hourly reduction rate (fatigue / 8 hours)
            hourly_reduction = current_fatigue / 8
            
            # Convert to per-step reduction (divide by 6 steps per hour)
            per_step_reduction = hourly_reduction / 6
            
            # Ensure we don't reduce below zero
            reduction = min(current_fatigue, per_step_reduction)
            
            if reduction > 0:
                self.motivation.update_state_value('SleepState', -reduction)
            
            return  # Skip other decisions while sleeping

        # check time, one hour to work increase work motivation
        if self.model.current_time.weekday() < 5 and self.model.current_time.hour == 8:
            self.motivation.update_state_value('WorkState', 100)
            self.log_action("motivation_change", "Work motivation increased due to work hour")

        if self.pos == self.work:
            if self.model.current_time.weekday() < 5 and \
                    (9 <= self.model.current_time.hour <= 11 or 13 <= self.model.current_time.hour <= 16):
                self.motivation.update_state_value('WorkState', -0.4)
                
                # Set activity to working if not already
                if self._current_activity != 'working':
                    self._set_activity('working')
                    self.log_action("work", "Working during work hours")
            elif (self.model.current_time.weekday() < 5 and self.model.current_time.hour > 17) or \
                    (self.model.current_time.weekday() >= 5):
                self.motivation.reset_one_motivation('WorkState')
                
                # If was working, set to none
                if self._current_activity == 'working':
                    self._set_activity('none')
                    self.log_action("motivation_change", "Work motivation reset after work hours or weekend")

        if self.target_location != self.pos:
            return
        elif self.motivation.present_state() == 'HungerState':
            hunger_value = self.motivation.state_values()['HungerState']
            if hunger_value < 2 * motivation_threshold:
                meal = random.choices(['small_meal', 'medium_meal', 'large_meal'], weights=[0.5, 0.25, 0.25], k=1)[0]
                self.log_action("decision", f"Decided to buy a {meal} due to low hunger")
            else:
                meal = random.choices(['medium_meal', 'large_meal'], weights=[0.5, 0.5], k=1)[0]
                self.log_action("decision", f"Decided to buy a {meal} due to high hunger")
            self.buy(meal)
            if meal == 'small_meal':
                value = hunger_value * 0.5
            else:
                value = hunger_value * random.uniform(0.8, 1)

            self.motivation.update_state_value('HungerState', -value)
            self.log_action("motivation_change", f"Hunger reduced by {value} to {self.motivation.state_values()['HungerState']}")

        elif self.motivation.present_state() == 'ConsumerismState':
            self.log_action("decision", "Decided to go shopping due to consumerism motivation")
            self.buy('consumerism')
            self.motivation.reset_one_motivation('ConsumerismState')
            self.log_action("motivation_change", "Consumerism motivation reset after shopping")

        elif self.motivation.present_state() == 'SocialState':
            value = self.motivation.state_values()['SocialState']
            reduction_rate = np.random.beta(a=9, b=2, size=1)[0]
            self.motivation.update_state_value('SocialState', -value * reduction_rate)
            self._set_activity('socializing')
            self.log_action("social_interaction", f"Social interaction reduced social motivation by {value * reduction_rate}")
        
        # If no specific activity and not at target location, set to 'none'
        elif self._current_activity not in ['sleeping', 'working', 'eating', 'shopping', 'socializing']:
            self._set_activity('none')

    def update_people_records(self):
        agent_data = {
            "Step": self.model.steps,
            "AgentID": self.unique_id,
            "date_time": self.model.current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "location": self.pos,
            "account_balance": self.get_all_bank_accounts(),
            "motivations": self.motivation.state_values(),
            "active": self.active,
            "activity": self._current_activity
        }
        self.model.datacollector.add_table_row("people", agent_data, ignore_missing=True)

    def step(self):
        # Skip processing if the person is not active in the model
        if not self.active:
            return
            
        # Only move if not sleeping
        if self._current_activity != 'sleeping':
            self.move()
            
        self.pay_schedule_txn()
        # self.unscheduled_txn()
        
        # Only update motivations if not sleeping
        if self._current_activity != 'sleeping':
            self.motivation.step()
            
        self.decision_maker()
        self.update_people_records()

    @classmethod
    def create_agents(cls, model, n, initial_money):
        """Create multiple Person agents at once."""
        return [cls(model, initial_money) for _ in range(n)]
