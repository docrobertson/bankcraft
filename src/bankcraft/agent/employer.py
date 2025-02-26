import random

from bankcraft.agent.general_agent import GeneralAgent
from bankcraft.config import time_units


class Employer(GeneralAgent):
    def __init__(self, model):
        super().__init__(model)
        self.pay_period = random.choice([time_units['biweekly']])
        self._num_pays_per_year = time_units.convert(1, 'year', 'biweekly')

        self.employees = []
        self._initial_fund = 1000000
        self.bank_accounts = self.assign_bank_account(model, self._initial_fund)
        # These are for use of agent reporter and needs to be handled better in the future
        self.type = 'employer'
        self._location = None
        self._salary_list = [['0', '0.8', '18>', '100-200'],
                             ['1', '0.9', '18>', '54-120'],
                             ['2', '0.8', '18>', '66-96'],
                             ['3', '0.8', '18>', '49-63'],
                             ['4', '0.9', '18>', '30-60']]  # ['Group', 'wage_Gap_Rate', 'Age', 'Salary_Range']

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        self._location = value

    def is_pay_date(self, current_step):
        """
        Check if the current step is a pay date.
        
        Args:
            current_step: The current step in the simulation
            
        Returns:
            bool: True if it's a pay date, False otherwise
        """
        return current_step % self.pay_period == 0

    def step(self):
        if self.is_pay_date(self.model.steps):
            self.pay_salary()

    def add_employee(self, person):
        salary = self.assign_salary(person)
        salary_per_pay = salary / self._num_pays_per_year
        self.employees.append({'person': person, 'salary': salary, 'salary_per_pay': salary_per_pay})
        person.assign_salary_info(self, salary)

    def find_employee(self, person):
        for employee in self.employees:
            if employee['person'] == person:
                return employee
        return None

    def remove_employee(self, person):
        employee = self.find_employee(person)
        self.employees.remove(employee)

    def pay_salary(self):
        for employee in self.employees:
            person = employee['person']
            salary_per_pay = employee['salary_per_pay']
            self.pay(person, salary_per_pay, 'cheque', 'salary')

    def assign_salary(self, person):
        # Assign a random group since person doesn't have a group attribute
        group = random.randint(0, len(self._salary_list) - 1)
        salary_range = self._salary_list[group][3].split('-')
        min_salary = float(salary_range[0]) * 1000
        max_salary = float(salary_range[1]) * 1000
        salary = random.uniform(min_salary, max_salary)
        return salary
