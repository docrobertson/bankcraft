import random
from abc import ABC, abstractmethod

from bankcraft.agent.merchant import Clothes, Food


class MotivationState(ABC):

    def __init__(self, motivation):
        self.motivation = motivation
        self.__value = 1

    def __str__(self):
        return self.__class__.__name__

    @abstractmethod
    def set_motion(self) -> None:
        pass

    def get_value(self):
        return self.__value

    def update_value(self, amount):
        self.__value += amount


class HungerState(MotivationState):

    def set_motion(self) -> None:
        self.motivation.agent.target_location = self.motivation.agent.get_nearest(Food).pos


class FatigueState(MotivationState):

    def set_motion(self) -> None:
        self.motivation.agent.target_location = self.motivation.agent.home
        # self.update_value(-fatigue_rate)


class ConsumerismState(MotivationState):

    def set_motion(self) -> None:
        self.motivation.agent.target_location = self.motivation.agent.get_nearest(Clothes).pos


class SocialState(MotivationState):

    def set_motion(self) -> None:
        # self.motivation.agent.target_location = self.motivation.agent.best_friend.pos
        friends = self.motivation.agent.friends
        friend = random.choices(list(friends.keys()), weights=list(friends.values()), k=1)[0]
        self.motivation.agent.target_location = friend.pos


class WorkState(MotivationState):

    def set_motion(self) -> None:
        self.motivation.agent.target_location = self.motivation.agent.work


class NeutralState(MotivationState):

    def set_motion(self) -> None:
        print('no motion in Neutral state')
        return
