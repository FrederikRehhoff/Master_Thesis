""" Generate a world """
from typing import Tuple
import networkx as nx
import random as rnd
import logging

from .map import Map


class SimpleMapGenerator(object):

    """ Auto generate simple maps (no obstacles or similar) """

    def __init__(self, map_size: Tuple[int, int],
                 seed=rnd.seed()):
        """ Create a generator

        :nodes: number of nodes (x * y)
        :seed: The seed for the random generator

        """
        assert map_size[0] > 0 and map_size[1] > 0, "The number of nodes must be a positive integer"

        self._map_size = map_size
        self._seed = seed
        self.reset()

    def reset(self) -> None:
        """ Reset the generator to beginning

        """
        rnd.seed(self._seed)

    def generate(self, objs=None, agents=None, idle_stations=None, idle_edges=None) -> Map:
        if idle_edges is None:
            idle_edges = []
        if agents is None:
            agents = []
        if objs is None:
            objs = []
        if idle_stations is None:
            idle_stations = []
        """ Generate a world
        :returns: TODO

        """
        logging.info("Generating world")

        # edge_count = int(1 + (3 * self._map_size[0] * self._map_size[1] + 1) / 2)
        #
        # logging.info(f'''Map generator settings: Seed: {self._seed} Number nodes: {self._map_size}'''
        #              f''' Edge count: {edge_count} ''')

        logging.info("Generating regular lattice")
        my_map: nx.Graph = nx.Graph()
        for x in range(0, self._map_size[0]):
            for y in range(0, self._map_size[1]):
                my_map.add_node((x, y))
                my_map.nodes[(x, y)]["agent"] = None
                my_map.nodes[(x, y)]["color"] = "white"
                my_map.nodes[(x, y)]["label"] = None
#               logging.info(f"Adding {x} and {y}")
                if x > 0:
                    my_map.add_edge((x - 1, y), (x, y))
                if y > 0:
                    my_map.add_edge((x, y - 1), (x, y))
                if x < self._map_size[0]-1:
                    my_map.add_edge((x + 1, y), (x, y))
                if y < self._map_size[1]-1:
                    my_map.add_edge((x, y + 1), (x, y))

        logging.info("Initializing objects")

        for obj in objs:
            if my_map.nodes[obj[1]]["agent"] is None:
                my_map.remove_node(obj[1])
                my_map.add_node(obj[1])
                my_map.nodes[obj[1]]["object"] = True
                my_map.nodes[obj[1]]["agent"] = None
            if obj[1][0] > 0:
                my_map.add_edge((obj[1][0] - 1, obj[1][1]), (obj[1][0], obj[1][1]))
            if obj[1][1] > 0:
                my_map.add_edge((obj[1][0], obj[1][1] - 1), (obj[1][0], obj[1][1]))
            if obj[1][0] < self._map_size[0]-1:
                my_map.add_edge((obj[1][0] + 1, obj[1][1]), (obj[1][0], obj[1][1]))
            if obj[1][1] < self._map_size[1]-1:
                my_map.add_edge((obj[1][0], obj[1][1] + 1), (obj[1][0], obj[1][1]))

        logging.info("Initializing idle stations")

        for station in idle_stations:
            # my_map.remove_node(station[0])
            my_map.add_node(station[0])
            my_map.nodes[station[0]]["idle station"] = True
            my_map.nodes[station[0]]["agent"] = None
            my_map.nodes[station[0]]["color"] = "green"
            my_map.nodes[station[0]]["label"] = "free"
        for edge in idle_edges:
            my_map.add_edge(*edge)


        logging.info("Initializing agents")

        for agent in agents:
            if my_map.nodes[agent.position]["agent"] is None:
                # my_map.remove_node(agent.position)
                # my_map.add_node(agent.position)
                my_map.nodes[agent.position]["agent"] = True
            # if agent.position[0] > 0:
            #     my_map.add_edge((agent.position[0] - 1, agent.position[1]), (agent.position[0], agent.position[1]))
            # if agent.position[1] > 0:
            #     my_map.add_edge((agent.position[0], agent.position[1] - 1), (agent.position[0], agent.position[1]))
            # if agent.position[0] < self._map_size[0]-1:
            #     my_map.add_edge((agent.position[0] + 1, agent.position[1]), (agent.position[0], agent.position[1]))
            # if agent.position[1] < self._map_size[1]-1:
            #     my_map.add_edge((agent.position[0], agent.position[1] + 1), (agent.position[0], agent.position[1]))

        logging.info("World generated")

        # print(f"nodes: {my_map.nodes()}\nedges: {my_map.edges()}")

        return Map(my_map, self._map_size)
