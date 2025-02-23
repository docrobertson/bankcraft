from bankcraft.agent.general_agent import GeneralAgent


class Bank(GeneralAgent):
    def __init__(self, model):
        super().__init__(model)
        self.type = 'bank'
        self._location = None  # Add location attribute

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        self._location = value
