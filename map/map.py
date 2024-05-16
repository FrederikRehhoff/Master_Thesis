from typing import Tuple
import networkx as nx
import logging
import matplotlib.pyplot as plt


class Map(object):

    """ The world representation """

    def __init__(self, graph, map_size: Tuple[int, int]):
        logging.debug("Initializing the world")
        self._graph = graph
        self._map_size = map_size

    @property
    def size_xy(self) -> Tuple[int, int]:
        return self._map_size

    @property
    def size_x(self) -> int:
        return self._map_size[0]

    @property
    def size_y(self) -> int:
        return self._map_size[1]

    @property
    def graph(self) -> nx.Graph:
        """ The graph of the world """
        return self._graph

    def connected(self, node: int) -> list:
        """ Get the corrected nodes to node

        :node: The node id
        :returns: list of node

        """
        return list(nx.neighbors(self._graph, node))

    def occupied(self, position: Tuple[int, int]):
        """
        Check if a node is occupied
        :position: node position
        """
        # if position[0] < 0 or position[0] >= self.size_x or position[1] < 0 or position[1] >= self.size_y:
        #     return True

        # Check if the node exists in the graph
        if position not in self._graph.nodes:
            return True  # If the node doesn't exist, consider it occupied

        return "agent" not in self._graph.nodes[position] or self._graph.nodes[position]["agent"] is not None

    def get_neighbour_nodes(self, agent):
        neighbour_nodes = []
        checkx = [0, 0, 1, -1]
        checky = [1, -1, 0, 0]

        for i in range(0, 4):
            if 0 <= agent.position[0] + checkx[i] <= self.size_x \
                    and 0 <= agent.position[1] + checky[i] <= self.size_y:  # check if the node is inside map

                if not self.occupied((agent.position[0] + checkx[i],
                                            agent.position[1] + checky[i])):  # check if the node is occupied
                    neighbour_nodes.append((agent.position[0] + checkx[i], agent.position[1] + checky[i]))

        return neighbour_nodes

    def move_agent(self, agent, new_position: Tuple[int, int]):
        assert self._graph.nodes[agent.position]["label"] == agent.name, \
            f"Error, {agent.name} is not currently located at {agent.position}"
        assert self._graph.nodes[new_position]["agent"] is None, \
            f"Error, location is not free {new_position}"

        self._graph.nodes[agent.position]["agent"] = None
        self._graph.nodes[agent.position]["label"] = None
        self._graph.nodes[agent.position]["color"] = "white"
        del self._graph.nodes[agent.position]["inventory"]
        self._graph.nodes[new_position]["agent"] = agent
        agent.position = new_position
        # print(f"{agent.name} pos: {agent.position}")

    def move_all(self, agents=None, idle_stations=None):
        if agents is None:
            agents = []
        if idle_stations is None:
            idle_stations = []

        for agent in agents:
            agent.move(self, idle_stations)

    def showMap(self, step, objs=None, agents=None, idle_stations=None):
        if agents is None:
            agents = []
        if objs is None:
            objs = []
        if idle_stations is None:
            idle_stations = []

        colors = []
        labels = {}

        # Clear the current axes
        plt.cla()

        for obj in objs:
            self._graph.nodes[obj[1]]["label"] = obj[0] + " x " + str(obj[3])
            self._graph.nodes[obj[1]]["color"] = obj[2]

        for station in idle_stations:
            if self._graph.nodes[station[0]]["label"] == "free":
                self._graph.nodes[station[0]]["label"] = station[2]
                self._graph.nodes[station[0]]["color"] = station[1]
            elif self._graph.nodes[station[0]]["label"] is None:
                self._graph.nodes[station[0]]["label"] = station[2]
                self._graph.nodes[station[0]]["color"] = station[1]
            else:
                self._graph.nodes[station[0]]["label"] = "reserved"
                self._graph.nodes[station[0]]["color"] = "red"

        for agent in agents:
            self._graph.nodes[agent.position]["label"] = agent.name
            self._graph.nodes[agent.position]["color"] = agent.color
            self._graph.nodes[agent.position]["inventory"] = agent.inventory

        for i in self._graph.nodes:
            node = self._graph.nodes[i]
            # print(node)
            colors.append(node["color"])

        for node in nx.nodes(self._graph):
            # print(self._graph.nodes[node])
            if self._graph.nodes[node]["label"] is not None:
                labels[node] = self._graph.nodes[node]["label"]

        pos = {n: (n[0] * 10, n[1] * 10) for n in nx.nodes(self._graph)}
        nodes_graph = nx.draw_networkx_nodes(self._graph, pos=pos, node_color=colors,
                                             node_size=800, node_shape="s", linewidths=1.0)
        nodes_edges = nx.draw_networkx_edges(self._graph, pos=pos)

        nx.draw_networkx_labels(self._graph, pos, labels, font_size=11, font_color="black",)
        nodes_graph.set_edgecolor('black')

        plt.title(f"Step {step}")
        plt.draw()
        plt.show(block=False)
        plt.pause(1)
        # plt.waitforbuttonpress()

    # def showMap(self, step, objs=None, agents=None, idle_stations=None):
    #     if agents is None:
    #         agents = []
    #     if objs is None:
    #         objs = []
    #     if idle_stations is None:
    #         idle_stations = []
    #
    #     colors = []
    #     labels = {}
    #
    #     # Clear the current axes
    #     plt.cla()
    #
    #     # Reset all nodes' labels and colors
    #     for node in self._graph.nodes:
    #         self._graph.nodes[node]["label"] = None
    #         self._graph.nodes[node]["color"] = "white"
    #
    #     for obj in objs:
    #         self._graph.nodes[obj[1]]["label"] = obj[0] + " x " + str(obj[3])
    #         self._graph.nodes[obj[1]]["color"] = obj[2]
    #
    #     for station in idle_stations:
    #         if self._graph.nodes[station[0]]["label"] == "free":
    #             self._graph.nodes[station[0]]["label"] = station[2]
    #             self._graph.nodes[station[0]]["color"] = station[1]
    #         elif self._graph.nodes[station[0]]["label"] is None:
    #             self._graph.nodes[station[0]]["label"] = station[2]
    #             self._graph.nodes[station[0]]["color"] = station[1]
    #         else:
    #             self._graph.nodes[station[0]]["label"] = "reserved"
    #             self._graph.nodes[station[0]]["color"] = "red"
    #
    #     for agent in agents:
    #         self._graph.nodes[agent.position]["label"] = agent.name
    #         self._graph.nodes[agent.position]["color"] = agent.color
    #         self._graph.nodes[agent.position]["inventory"] = agent.inventory
    #
    #     for i in self._graph.nodes:
    #         node = self._graph.nodes[i]
    #         colors.append(node["color"])
    #
    #     for node in nx.nodes(self._graph):
    #         if self._graph.nodes[node]["label"] is not None:
    #             labels[node] = self._graph.nodes[node]["label"]
    #
    #     pos = {n: (n[0] * 10, n[1] * 10) for n in nx.nodes(self._graph)}
    #     nodes_graph = nx.draw_networkx_nodes(self._graph, pos=pos, node_color=colors,
    #                                          node_size=800, node_shape="s", linewidths=1.0)
    #     nodes_edges = nx.draw_networkx_edges(self._graph, pos=pos)
    #
    #     nx.draw_networkx_labels(self._graph, pos, labels, font_size=11, font_color="black")
    #     nodes_graph.set_edgecolor('black')
    #
    #     plt.title(f"Step {step}")
    #     plt.draw()
    #     plt.show(block=False)
    #     plt.pause(1)
    #     # plt.waitforbuttonpress()
