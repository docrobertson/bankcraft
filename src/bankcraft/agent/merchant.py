from bankcraft.agent.general_agent import GeneralAgent


class Merchant(GeneralAgent):
    def __init__(self, model,
                 price,
                 initial_money):
        super().__init__(model)
        self.price = price
        self.bank_accounts = self.assign_bank_account(model, initial_money)
        self.type = 'merchant'
        self._location = None

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        self._location = value


class Food(Merchant):
    def __init__(self, model,
                 price,
                 initial_money):
        super().__init__(model, price, initial_money)
        self._location = None

    @classmethod
    def create_agents(cls, model, n, price, initial_money):
        """Create multiple Food merchant agents at once."""
        return [cls(model, price, initial_money) for _ in range(n)]


class Clothes(Merchant):
    def __init__(self, model,
                 price,
                 initial_money):
        super().__init__(model, price, initial_money)
        self._location = None

    @classmethod
    def create_agents(cls, model, n, price, initial_money):
        """Create multiple Clothes merchant agents at once."""
        return [cls(model, price, initial_money) for _ in range(n)]

