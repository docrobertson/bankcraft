from __future__ import annotations

from bankcraft.motivation.motivation_state import *
from bankcraft.config import hunger_rate, fatigue_rate, consumerism_rate, social_rate, work_rate, motivation_threshold


class Motivation:

    def __init__(self, state, agent) -> None:
        self._state = state
        self.set_state(NeutralState)
        self.critical_motivation = None
        self.agent = agent
        self.states_rate = {
            'HungerState': (HungerState(self), hunger_rate),
            'FatigueState': (FatigueState(self), fatigue_rate),
            'ConsumerismState': (ConsumerismState(self), consumerism_rate),
            'SocialState': (SocialState(self), social_rate),
            'WorkState': (WorkState(self), work_rate)
        }

    def set_state(self, state: MotivationState):
        self._state = state
        self._state.motivation = self

    def set_motion(self):
        self._state.set_motion()

    def set_transaction(self):
        self._state.set_transaction()

    def __str__(self):
        return str(self._state)

    def get_critical_motivation(self):
        max_motivation, max_motivation_value = self.get_max_motivation()
        if max_motivation_value > motivation_threshold:
            return max_motivation

    def get_max_motivation(self):
        max_value = 0
        max_motivation = None
        for state_class, rate in self.states_rate.values():
            state = state_class
            value = state.get_value()
            if value > max_value:
                max_value = value
                max_motivation = state

        return max_motivation, max_value

    def reset_one_motivation(self, state):
        current_value = self.states_rate[state][0].get_value()
        self.states_rate[state][0].update_value(-current_value)

    def present_state(self):
        return str(self._state)

    def live(self):
        for state, rate in self.states_rate.values():
            state.update_value(rate)

    def state_values(self):
        return {str(state): state.get_value() for state, rate in self.states_rate.values()}

    def update_state_value(self, state, value):
        self.states_rate[state][0].update_value(value)

    def step(self):
        self.live()
        self.critical_motivation = self.get_critical_motivation()
        if self.critical_motivation is not None:
            self.set_state(self.critical_motivation)  # Set the critical motivation state
            self.critical_motivation.set_motion()
        else:
            self.set_state(NeutralState)
