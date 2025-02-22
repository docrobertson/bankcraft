import datetime
import pytest
from mesa.datacollection import DataCollector
import pandas as pd

from bankcraft.agent.bank import Bank
from bankcraft.agent.general_agent import GeneralAgent
from bankcraft.bankcraftmodel import BankCraftModel

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
def banks(model):
    """Create banks for testing."""
    model.banks = [Bank(model) for _ in range(num_banks)]
    return model.banks

@pytest.fixture
def agent(model):
    """Create a general agent for testing."""
    return GeneralAgent(model)

@pytest.fixture
def other_agent(model):
    """Create another general agent for testing."""
    return GeneralAgent(model)

def test_bank_account_is_none_before_assigning(agent):
    assert agent.bank_accounts is None

def test_bank_account_is_not_none_after_assigning(agent, model):
    agent.bank_accounts = agent.assign_bank_account(model, account_initial_balance)
    assert agent.bank_accounts is not None

def test_wealth_updates_after_assigning_bank_account(agent, model):
    agent_default_wealth = agent.wealth
    agent.bank_accounts = agent.assign_bank_account(model, account_initial_balance)
    assert (agent_default_wealth == 0 and agent.wealth == num_banks*account_initial_balance)

def test_pay_changes_wealth(agent, other_agent, model, banks):
    agent.bank_accounts = agent.assign_bank_account(model, account_initial_balance)
    other_agent.bank_accounts = other_agent.assign_bank_account(model, account_initial_balance)
    agent.pay(other_agent, txn_amount, "cash", "gift")
    assert (agent.wealth == num_banks * account_initial_balance - txn_amount and
            other_agent.wealth == num_banks * account_initial_balance + txn_amount)

def test_undefined_tnx_type_does_not_change_wealth(agent, other_agent, model, banks):
    agent.bank_accounts = agent.assign_bank_account(model, account_initial_balance)
    agents_initial_wealth = agent.wealth
    other_agent.bank_accounts = other_agent.assign_bank_account(model, account_initial_balance)
    other_agent_initial_wealth = other_agent.wealth
    agent.pay(other_agent, txn_amount, "e-transfer", "gift")
    assert agents_initial_wealth == agent.wealth and other_agent_initial_wealth == other_agent.wealth

def test_updating_txn_records(agent, other_agent, model):
    agent.update_records(other_agent, txn_amount, "cheque", "chequing", "debt")
    model.datacollector.collect(model)
    expected_txn_data = {
        "sender": agent.unique_id,
        "receiver": other_agent.unique_id,
        "amount": txn_amount,
        "step": 0,
        "date_time": model.current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "txn_id": f"{str(agent.unique_id)}_{str(agent.txn_counter)}",
        "txn_type": "cheque",
        "sender_account_type": "chequing",
        "description": "debt",
    }
    model_txn_data = model.datacollector.get_table_dataframe("transactions").iloc[0]
    pd.testing.assert_series_equal(pd.Series(expected_txn_data, name=0), model_txn_data)
