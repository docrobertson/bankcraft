from bankcraft.banking.transaction import Transaction
from bankcraft.agent.general_agent import GeneralAgent
from bankcraft.agent.bank import Bank
from bankcraft.bankcraftmodel import BankCraftModel
import pytest
import datetime
from mesa.datacollection import DataCollector

account_initial_balance = 1500
num_banks = 1
txn_amount = 300

@pytest.fixture
def model():
    """Create a model instance for testing."""
    model = BankCraftModel()
    model.datacollector = DataCollector(
        tables={
            "transactions": ["sender", "receiver", "amount", "step", "date_time",
                           "txn_id", "txn_type", "sender_account_type", "description"]
        }
    )
    model.current_time = datetime.datetime(2023, 1, 1, 0, 0, 0)
    return model

@pytest.fixture
def agent(model):
    """Create a general agent for testing."""
    return GeneralAgent(model)

@pytest.fixture
def banks(model):
    """Create banks for testing."""
    model.banks = [Bank(model) for _ in range(num_banks)]
    return model.banks

def test_do_transaction_changes_senders_and_receivers_wealth(model, agent, banks):
    agent.bank_accounts = agent.assign_bank_account(model, account_initial_balance)
    agents_initial_wealth = agent.wealth
    
    another_agent = GeneralAgent(model)
    another_agent.bank_accounts = another_agent.assign_bank_account(model, account_initial_balance)
    another_agents_initial_wealth = another_agent.wealth
    
    transaction = Transaction(agent,
                            another_agent,
                            txn_amount,
                            agent.txn_counter,
                            txn_type='ACH')
    transaction.do_transaction()
    
    assert agents_initial_wealth == account_initial_balance and \
           agent.wealth == agents_initial_wealth - txn_amount and \
           agents_initial_wealth + another_agents_initial_wealth == agent.wealth + another_agent.wealth
