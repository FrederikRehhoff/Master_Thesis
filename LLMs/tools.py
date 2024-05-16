from agent.Robot_list import robots
from langchain_core.tools import tool
import config
from map import SimpleMapGenerator
from agent import Agent

from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List, Tuple, Annotated, TypedDict
import asyncio

# # define map size
# x = 10
# y = 10
# map_size = (x, y)
#
# corner_UR = (map_size[0] - 1, map_size[1] - 1)
# corner_UL = (0, map_size[1] - 1)
# corner_BL = (0, 0)
# corner_BR = (map_size[0] - 1, 0)
#
# # define agents:  ('name', placement: (x,y), 'color', Property, inventory)
# R1 = Agent("Robot1", (6, 6), "blue", "gripper", None, "idle")
# R2 = Agent("Robot2", (6, 9), "yellow", "mop", None, "idle")
#
# robots = [R1, R2]
#
# # define object in map:  ('name', placement: (x,y), 'color', number_on_location)
# obj1 = ["Apple", corner_UR, "red", 2]
# obj2 = ["Orange", corner_UL, "orange", 1]
# objs = [obj1, obj2]
#
# # define idle stations in map: (placement: (x,y), 'color', status: 'free')
# idle1 = [(corner_UR[0] + 1, corner_UR[1] + 0), "green", "free"]
# idle2 = [(corner_UR[0] + 0, corner_UR[1] + 1), "green", "free"]
# idle3 = [(corner_UL[0] + 0, corner_UL[1] + 1), "green", "free"]
# idle4 = [(corner_UL[0] - 1, corner_UL[1] + 0), "green", "free"]
# idle5 = [(corner_BR[0] + 1, corner_BR[1] + 0), "green", "free"]
# idle6 = [(corner_BR[0] + 0, corner_BR[1] - 1), "green", "free"]
# idle7 = [(corner_BL[0] + 0, corner_BL[1] - 1), "green", "free"]
# idle8 = [(corner_BL[0] - 1, corner_BL[1] + 0), "green", "free"]
# idle_stations = [idle1, idle2, idle3, idle4, idle5, idle6, idle7, idle8]
#
# # Define edges based on the corners and their respective idle stations
# idle_edges = [
#     (corner_UR, idle1[0]),
#     (corner_UR, idle2[0]),
#     (corner_UL, idle3[0]),
#     (corner_UL, idle4[0]),
#     (corner_BR, idle5[0]),
#     (corner_BR, idle6[0]),
#     (corner_BL, idle7[0]),
#     (corner_BL, idle8[0])
# ]
#
# # initialize map with given properties:  (width, heigth, object_list, agent_list)
# my_map = SimpleMapGenerator(map_size).generate(objs, robots, idle_stations, idle_edges)
#
#
# def update_map(robot_list=robots, idle_station_list=idle_stations):
#     my_map.move_all(robot_list, idle_station_list)
#
#
# def display_map(step, objects=objs, robot_list=robots, idle_station_list=idle_stations):
#     my_map.showMap(step, objects, robot_list, idle_station_list)


class desired_robot_tool_property(BaseModel):
    """Inputs to the tools."""

    desired_robot_tool_property: str = Field(
        description="The desired tool property which is required to solve the task given"
    )


def sort_by_tool(tool_name, robot_list=robots):
    usable_robots = []
    for robot in robot_list:
        if robot.tool_property == tool_name:
            usable_robots.append(robot)
    return usable_robots


def sort_by_availability(robot_list, target_pos):
    available_robots = []
    if robot_list:
        closest_robot = robot_list[0].name
        min_dist = dist_func(robot_list[0].position, target_pos)
        flag = True
        for robot in robot_list:
            if robot._status != "active":
                available_robots.append(robot.name)
                if flag:
                    flag = False
                    closest_robot = robot.name
                    min_dist = dist_func(robot.position, target_pos)

                if min_dist > dist_func(robot.position, target_pos):
                    closest_robot = robot.name
                    min_dist = dist_func(robot.position, target_pos)
        if available_robots:
            return f"out of available robot: {available_robots}, {closest_robot} is the best suited to solve the task."
    return "no robot with the specified tool to solve the task"


def dist_func(robot_pos, target_pos):
    x_dist = abs(target_pos["x"] - robot_pos[0])
    y_dist = abs(target_pos["y"] - robot_pos[1])
    total_dist = x_dist + y_dist
    return total_dist


def select_known_robot(robot_name, desired_tool, robot_list=robots):
    for robot in robot_list:
        if robot_name == robot.name:
            if robot._status != "active":
                if desired_tool == robot.tool_property:
                    return f"{robot_name} with the tool property: {robot.tool_property} has been selected to solve the task."
                return f"""{robot_name} is not equipped with the tool property initially selected for task completion. 
                Can {robot_name} with tool property: {robot.tool_property} still solve the task?
                If a list of items with assoicated tool properties is provided, remember to use that as reference.
                In your anwser please stat the initial selected tool and why {robot_name} can/can't solve the task with the tool property: {robot.tool_property}. in this step be strict and try to stay close to the list of items with assoicated tool properties
                """
            return f"{robot_name} is currently active and is not available to solve the task"
    return f"{robot_name} is not a valid robot"


def change_status(robot_name, robot_list=robots, status="idle"):
    my_map = config.my_map
    for robot in robot_list:
        if robot_name == robot.name:
            old_status = robot._status
            robot.set_status(my_map=my_map, status=status)
            return f"{robot.name} has changed status from {old_status} to {status}"


def set_goal(robot_name: str, position: Tuple, robot_list=robots):
    my_map = config.my_map
    for robot in robot_list:
        if robot_name == robot.name:
            robot.setGoal(my_map=my_map, goal=position)
            return robot.goal


def add_item_to_inventory(robot_name, item_name, robot_list=robots):
    objs = config.objs
    for robot in robot_list:
        if robot_name == robot.name:
            for obj in objs:
                if item_name == obj[0]:
                    robot.add_item_inventory(item_name)
                    obj[3] -= 1


def wait_for_goal(robot_name: str, robot_list=robots):
    for robot in robot_list:
        print(len(robot_list))
        if robot_name == robot.name:
            if robot.goal is None:
                return f"The specified robot {robot.name} does not have a goal."
            if robot.position != robot.goal:
                return f"{robot_name} is still underway and haven't reach location {robot.goal} yet"
            else:
                return f"{robot.name} have arrived at position {robot.goal}."
    return f"Robot with the name {robot_name} does not exist or is busy with something else."


@tool
def move_robot(robot_name: str, position: Tuple) -> str:
    """Moves the Specified robot to the desired position"""
    goal = set_goal(robot_name=robot_name, position=position)
    return f"{robot_name} is moving to the desired position {goal}"


@tool
def wait(robot_name: str):
    """This tool waits for the specified robot to reach its desired position"""
    return wait_for_goal(robot_name)


@tool
def grab_or_remove_item(robot_name: str, item_name: str) -> str:
    """makes the specified robot grab/remove the desired item"""
    add_item_to_inventory(robot_name=robot_name, item_name=item_name)
    return f"{robot_name} has grabed/removed the desired item {item_name}"


@tool
def robot_status_change(robot_name: str, status: str):
    """Changes the status of a robot"""
    return change_status(robot_name=robot_name, status=status)


@tool
def robot_selection_tool(desired_robot_tool_property, item_position) -> str:
    """Finds the most robots with the desired tool property. Remember that the item_position needs to be a dict of x and y coordinates"""
    sorted_robots = sort_by_tool(desired_robot_tool_property)
    return sort_by_availability(sorted_robots, item_position)


@tool
def select_known_robot_tool(robot_name: str, desired_robot_tool_property) -> str:
    """select the specified robot to solve the task. If the robot does not have the desired tool for the task, then it will ask if the robot still can solve the task.
    This tool does not alter the tools a robot has, but will try to use the selected robot although it might not have the desired tool.
    """
    return select_known_robot(robot_name=robot_name, desired_tool=desired_robot_tool_property)


@tool
def agent_response_tool(input: str, response: str) -> str:
    """this is a tool that returns the response to the input"""
    return response


control_tools = [move_robot, wait, grab_or_remove_item, robot_status_change]
selection_tools = [robot_selection_tool, select_known_robot_tool]
misc_tools = [agent_response_tool]
