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
        # Check if receiver is a valid agent with bank_accounts
        if not hasattr(receiver, 'bank_accounts') or receiver.bank_accounts is None:
            self.log_action("payment_error", f"Cannot pay {amount} to invalid receiver (not an agent or no bank accounts)")
            return
            
        transaction = Transaction(self,
                                  receiver,
                                  amount,
                                  self.txn_counter,
                                  txn_type)
        if transaction.txn_type_is_defined() and transaction.txn_is_authorized():
            transaction.do_transaction()
            self.update_records(receiver, amount, txn_type, "chequing", description)
            self.log_action("payment", f"Paid {amount} to agent {receiver.unique_id} for {description}")

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
            old_pos = self.pos
            self.move_to(self.target_location)
            if old_pos != self.pos:
                # Determine destination type
                destination_type = "other"
                if hasattr(self, 'home') and self.target_location == self.home:
                    destination_type = "home"
                elif hasattr(self, 'work') and self.target_location == self.work:
                    destination_type = "work"
                else:
                    # Check if there's a merchant at the target location
                    cell_contents = self.model.grid.get_cell_list_contents([self.target_location])
                    for agent in cell_contents:
                        if agent.type in ['food', 'clothes']:
                            destination_type = "merchant"
                            break
                
                self.log_action("move", f"Moving to {destination_type} at {self.target_location}")

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

        old_pos = self.pos
        self.model.grid.move_agent(self, (x, y))
        self.pos = (x, y)
        
        # No longer logging position updates

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
        
    def log_action(self, action, details=""):
        """Log an action performed by the agent.
        
        Args:
            action (str): The name of the action performed
            details (str): Additional details about the action
        """
        action_data = {
            "agent_id": self.unique_id,
            "agent_type": getattr(self, "type", "unknown"),
            "step": self.model.steps,
            "date_time": self.model.current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "details": details,
            "location": getattr(self, "pos", None)
        }
        self.model.datacollector.add_table_row("agent_actions", action_data, ignore_missing=True)
