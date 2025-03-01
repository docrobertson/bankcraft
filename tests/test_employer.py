import pytest
import datetime
from mesa.datacollection import DataCollector
from bankcraft.model import BankCraftModelBuilder
from bankcraft.agent import Person
from bankcraft.agent import Employer
from bankcraft.agent import Bank
from bankcraft.agent import Business
from bankcraft.config import time_units

num_banks = 1

@pytest.fixture
def model():
    """Create a model instance for testing."""
    model = BankCraftModelBuilder.build_model()
    model.datacollector = DataCollector(
        tables={
            "transactions": ["sender", "receiver", "amount", "step", "date_time",
                           "txn_id", "txn_type", "sender_account_type", "description"],
            "agent_actions": ["agent_id", "agent_type", "step", "date_time", "action", "details", "location"]
        }
    )
    model.current_time = datetime.datetime(2023, 1, 1, 0, 0, 0)
    return model

@pytest.fixture
def employer(model, banks, invoicer):
    """Create a single employer for testing."""
    employer = Employer(model)
    model.employers = [employer]
    return employer

@pytest.fixture
def person(model):
    """Create a person for testing."""
    return Person(model, 500)

@pytest.fixture
def banks(model):
    """Create banks for testing."""
    model.banks = [Bank(model) for _ in range(num_banks)]
    return model.banks

@pytest.fixture
def invoicer(model):
    """Create business invoicers for testing."""
    business_types = ["rent/mortgage", "utilities", "subscription", "membership", "net_providers"]
    model.invoicer = {b_type: Business(model, b_type) for b_type in business_types}
    return model.invoicer

def test_add_employee(employer, person):
    initial_num_employees = len(employer.employees)
    employer.add_employee(person)
    assert len(employer.employees) == initial_num_employees + 1

def test_remove_employee(employer, model, person):
    employer.add_employee(person)
    second_person = Person(model, 500)
    third_person = Person(model, 500)
    employer.add_employee(second_person)
    employer.add_employee(third_person)
    initial_num_employees = len(employer.employees)
    employer.remove_employee(second_person)
    final_num_employees = len(employer.employees)
    assert initial_num_employees == 3 and final_num_employees == 2

def test_pay_period_is_biweekly_or_month(employer):
    """Test that the pay period is either biweekly or monthly."""
    assert employer.pay_period == time_units['biweekly'] or employer.pay_period == time_units['month']

def test_15biweekly_is_7months_pay_date(employer):
    """Test that 15 biweekly periods is approximately 7 months."""
    step = time_units.convert(15, 'biweekly', 'month')
    assert pytest.approx(step, 0.1) == 7.0

def test_pay_salary_changes_the_employees_wealth(employer, person, model):
    employer.add_employee(person)
    person.bank_accounts = person.assign_bank_account(model, 10)
    employees_initial_wealth = person.wealth
    # Set the model steps to trigger a pay date
    model.steps = employer.pay_period  # This ensures we're at a pay date
    employer.step()  # This will trigger pay_salary() since we're at a pay date
    assert person.wealth > employees_initial_wealth

