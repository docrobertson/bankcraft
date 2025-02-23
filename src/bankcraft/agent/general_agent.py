import itertools

import numpy as np
from mesa import Agent

from bankcraft.banking.bank_account import BankAccount
from bankcraft.banking.transaction import Transaction


class GeneralAgent(Agent):
    def __init__(self, model):
        Agent.__init__(self, model=model)
        self.bank_accounts = None
        self.txn_counter = 0

    def step(self):
        pass

    def assign_bank_account(self, model, initial_balance):
        account_types = ['chequing', 'saving', 'credit']
        bank_accounts = [[0] * len(account_types)] * len(model.banks)
        for (bank, bank_counter) in zip(model.banks, range(len(model.banks))):
            for (account_type, account_counter) in zip(account_types, range(len(account_types))):
                bank_accounts[bank_counter][account_counter] = BankAccount(self, bank, initial_balance, account_type)
        return bank_accounts

    def pay(self, receiver, amount, txn_type, description):
        transaction = Transaction(self,
                                  receiver,
                                  amount,
                                  self.txn_counter,
                                  txn_type)
        if transaction.txn_type_is_defined() and transaction.txn_is_authorized():
            transaction.do_transaction()
            self.update_records(receiver, amount, txn_type, "chequing", description)

    def update_records(self, other_agent, amount, txn_type, senders_account_type, description):
        transaction_data = {
            "sender": self.unique_id,
            "receiver": other_agent.unique_id,
            "amount": amount,
            "step": self.model.steps,
            "date_time": self.model.current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "txn_id": f"{str(self.unique_id)}_{str(self.txn_counter)}",
            "txn_type": txn_type,
            "sender_account_type": senders_account_type,
            "description": description,
        }
        self.model.datacollector.add_table_row("transactions", transaction_data, ignore_missing=True)

    def get_all_bank_accounts(self):
        bank_accounts = []
        for bank_account in itertools.chain(*self.bank_accounts):
            bank_accounts.append(bank_account.balance)
        return bank_accounts

    def move(self):
        if self.target_location is not None:
            self.move_to(self.target_location)
            # self.motivation.update_motivation('hunger', hunger_rate)

    def move_to(self, new_position):
        x, y = self.pos
        x_new, y_new = new_position
        x_distance = x_new - x
        y_distance = y_new - y
        if x_distance > 0:
            x += 1
        elif x_distance < 0:
            x -= 1

        if y_distance > 0:
            y += 1
        elif y_distance < 0:
            y -= 1

        self.model.grid.move_agent(self, (x, y))
        self.pos = (x, y)

    def distance_to(self, other_agent):
        x, y = self.pos
        x_other, y_other = other_agent.pos
        return np.sqrt((x - x_other) ** 2 + (y - y_other) ** 2)

    def get_nearest(self, agent_type):
        closest = float('inf')
        closest_agent = None
        for agent in self.model.get_all_agents_on_grid():
            if isinstance(agent, agent_type):
                distance = self.distance_to(agent)
                if distance < closest:
                    closest = distance
                    closest_agent = agent
        return closest_agent

    @property
    def wealth(self):
        _wealth = 0
        if self.bank_accounts is None:
            return _wealth
        for bank_account in itertools.chain(*self.bank_accounts):
            _wealth += bank_account.balance
        return _wealth

    def remove_from_model(self):
        """Remove agent from model properly."""
        self.remove()  # Use Mesa's built-in remove method
