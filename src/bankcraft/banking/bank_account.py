
class BankAccount:
    def __init__(self, person_owner, bank, initial_balance, account_type):
        self.owner = person_owner
        self.bank = bank
        self.account_type = account_type
        self.balance = initial_balance if self.account_type == 'chequing' else 0
        self.bank_account_id = f"{person_owner.unique_id}-{bank.unique_id}"
