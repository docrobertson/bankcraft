class Transaction:
    def __init__(self, sender, recipient, amount,
                 txn_counter, txn_type):
        self.sender = sender
        self.recipient = recipient
        self.transaction_id = f'{txn_counter}-self.sender.unique_id'
        self.sender_account = sender.bank_accounts[0][0]
        self.recipient_account = recipient.bank_accounts[0][0]
        self.amount = amount
        # self.date_of_transaction = date
        self._txn_type = txn_type

    def do_transaction(self):
        self.sender_account.balance -= self.amount
        self.sender.txn_counter += 1
        if self.recipient_account is not None:
            self.recipient_account.balance += self.amount

    def txn_type_is_defined(self):
        return str(self._txn_type).lower() in {"cash", "wire", "online", "ach", "cheque"}

    def txn_is_authorized(self):
        return self.amount > 0
