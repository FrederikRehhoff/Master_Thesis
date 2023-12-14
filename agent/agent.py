import logging

import networkx as nx
from typing import Tuple
import random

from map import Map


class Agent(object):
    def __init__(self, name, position, color, property, inventory):
        self._name = name
        self._position = position
        self._initial_position = position
        self._color = color
        self._goal = None
        self._station = None
        self._status = "idle"
        self._path = []
        self._path_history = []
        self._property = property
        self._inventory = []

    def setGoal(self, my_map, goal):
        """ Sets the Goal for the robot and finds the shortest path """
        self._goal = goal
        self.set_status(my_map, "active")
        self._path = nx.shortest_path(my_map.graph, source=self._position, target=self._goal)
        self._path.pop(0)
        # print(self._path)

    def direction(self) -> Tuple[int, int]:
        """ Finds the next node the agent needs to move to """
        if self._path:
            x, y = self._path[0][0] - self._position[0], self._path[0][1] - self._position[1]
            return x, y
        else:
            return 0, 0

    def next_move(self, my_map):
        new_position = (self._position[0] + self.direction()[0], self._position[1] + self.direction()[1])
        if my_map.occupied(new_position):
            if self._position != self._goal:
                new_position = random.choice(my_map.get_neighbour_nodes(self))
                my_map.move_agent(self, new_position)
                self._path = nx.shortest_path(my_map.graph, source=self._position, target=self._goal)
                self._path.pop(0)
        else:
            self._path_history.append(self._position)
            my_map.move_agent(self, new_position)
            self._path = nx.shortest_path(my_map.graph, source=self._position, target=self._goal)
            self._path.pop(0)

    def move(self, my_map, idle_stations=None):
        if idle_stations is None:
            idle_stations = []

        if self._status == "active":
            self.next_move(my_map)

        elif self._status == "idle":
            self.move_to_station(my_map, idle_stations)

        print(f"agent: {self._name}, pos: {self._position}, station: {self._station}, Status: {self._status}")

    def move_to_station(self, my_map, idle_stations=None):
        if idle_stations is None:
            idle_stations = []

        # checks if the agent have reach the station
        if self._position == self._station:
            self._path = []
            self._status = "charging"

        # if the agent have not been assigned a goal, it will go to the nearest free station.
        if self._station is None:
            shortest_path_length = self.dist_func(idle_stations[0][0])
            shortest_path = None
            shortest_station = None
            for station in idle_stations:
                if my_map.graph.nodes[station[0]]["label"] == "free":
                    temp_dist = self.dist_func(station[0])
                    if temp_dist <= shortest_path_length:
                        shortest_path_length = temp_dist
                        shortest_station = station[0]

            self._station = shortest_station
            self._goal = self._station
            self._path = shortest_path
            my_map.graph.nodes[shortest_station]["label"] = "reserved"

        if self._station:
            self._path = nx.shortest_path(my_map.graph, source=self._position, target=self._goal)
            self._path.pop(0)
            # print(f"path: {self._path}")
            self.next_move(my_map)

    def grip_object(self, obj, quantity=1):
        if self._property == "gripper":
            self._inventory.append(obj[0])
            obj[3] -= quantity
        else:
            print("agent is not equipped with a gripper")

    def set_status(self, my_map, status="idle"):
        if status in ["idle", "active", "charging"]:
            old_status = self._status
            self._status = status
            if self._status == "idle":
                self._goal = None
            elif self._status == "active":
                if self._position != self._station and self._station is not None:
                    my_map.graph.nodes[self._station]["label"] = "free"
                self._station = None
            print(f"AGENT: {self._name}\nSTATUS CHANGE: {old_status} -> {self._status}")

    def dist_func(self, target_pos):
        x_dist = abs(target_pos[0] - self._position[0])
        y_dist = abs(target_pos[1] - self._position[1])
        total_dist = x_dist + y_dist
        return total_dist

    @property
    def inventory(self) -> list:
        """ An agents inventory """
        return self._inventory

    @property
    def initial_position(self) -> Tuple[int, int]:
        """ The initial position of the agent """
        return self._initial_position

    @property
    def position(self) -> Tuple[int, int]:
        """ The position of the agent """
        return self._position

    @position.setter
    def position(self, new_position: Tuple[int, int]):
        """ Set the new position

        :new_position: The new node id

        """
        self._position = new_position

    @property
    def name(self) -> str:
        """ The name of the agent """
        return self._name

    @name.setter
    def name(self, new_name: str):
        """ Sets a new name for the agent

        :new_name: The new name for the agent

        """
        self._name = new_name

    @property
    def color(self) -> str:
        """ The color of the agent """
        return self._color

    @color.setter
    def color(self, new_color: str):
        """ Sets a new color for the agent

        :new_goal: The new color for the agent

        """
        self._color = new_color

    @property
    def goal(self) -> Tuple[int, int]:
        """ The goal of the agent """
        return self._goal

    @goal.setter
    def goal(self, new_goal: Tuple[int, int]):
        """ Set the new goal

        :new_goal: The new goal node id

        """
        self._goal = new_goal

    @property
    def path(self) -> list:
        """ The path of the agent """
        return self._path

    @path.setter
    def path(self, new_path: Tuple[int, int]):
        """ Set the new path

        :new_path: The new path for the agent

        """
        self._path = new_path
