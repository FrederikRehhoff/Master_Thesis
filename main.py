from map import Map
from map import SimpleMapGenerator
from agent import Agent
from LLMs import OPENAI_llm, keys


import logging
import keyboard


def dist_func(agent_pos, target_pos):
    x_dist = abs(target_pos[0] - agent_pos[0])
    y_dist = abs(target_pos[1] - agent_pos[1])
    total_dist = x_dist + y_dist
    return total_dist


def python_handler(llm_response, my_map, agents=None, objs=None):
    """TODO:
        1. Make the LLM bound to the map size
        2. Implement memory for the LLM"""
    if agents is None:
        agents = []
    if objs is None:
        objs = []

    if llm_response.SOLVABLE:
        print(f"TASK: {llm_response.TASK}, AGENT: {llm_response.AGENT}, ACTION: {llm_response.ACTION}, SOLVABLE: {llm_response.SOLVABLE}")
        action_value = llm_response.ACTION.split("(")[0].strip()
        agent_name = llm_response.AGENT
        if action_value == "move":
            coordinates_str = llm_response.ACTION.split("(")[1].split(")")[0]
            x, y = map(int, coordinates_str.split(","))
            coordinates = (x, y)
            for agent in agents:
                if agent.name == agent_name:
                    agent.setGoal(my_map, coordinates)

        if action_value == "grab":
            for agent in agents:
                if agent.name == agent_name:
                    for obj in objs:
                        if agent.position == obj[1]:
                            agent.grip_object(obj)
                            if obj[3] == 0:
                                objs.remove(obj)

        if action_value == "change_status":
            status = llm_response.ACTION.split("(")[1].split(")")[0]
            for agent in agents:
                if agent.name == agent_name:
                    agent.set_status(my_map, status)

    else:
        print("This request is not solvable for the agents operating in a 2D environment")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # define map size
    x = 10
    y = 10
    map_size = (x, y)

    corner_UR = (map_size[0] - 1, map_size[1] - 1)
    corner_UL = (0, map_size[1] - 1)
    corner_BL = (0, 0)
    corner_BR = (map_size[0] - 1, 0)

    # define agents:  ('name', placement: (x,y), 'color', Property, inventory)
    R1 = Agent("R2D2", (6, 6), "blue", "gripper", None)
    R2 = Agent("C3PO", (6, 9), "yellow", "gripper", None)
    agents = [R1, R2]

    # define object in map:  ('name', placement: (x,y), 'color', number_on_location)
    obj1 = ["Apple", corner_UR, "red", 2]
    obj2 = ["Orange", corner_UL, "orange", 1]
    objs = [obj1, obj2]

    # define idle stations in map: (placement: (x,y), 'color', status: 'free')
    idle1 = [(corner_UR[0] + 1, corner_UR[1] + 0), "green", "free"]
    idle2 = [(corner_UR[0] + 0, corner_UR[1] + 1), "green", "free"]
    idle3 = [(corner_UL[0] + 0, corner_UL[1] + 1), "green", "free"]
    idle4 = [(corner_UL[0] - 1, corner_UL[1] + 0), "green", "free"]
    idle5 = [(corner_BR[0] + 1, corner_BR[1] + 0), "green", "free"]
    idle6 = [(corner_BR[0] + 0, corner_BR[1] - 1), "green", "free"]
    idle7 = [(corner_BL[0] + 0, corner_BL[1] - 1), "green", "free"]
    idle8 = [(corner_BL[0] - 1, corner_BL[1] + 0), "green", "free"]
    idle_stations = [idle1, idle2, idle3, idle4, idle5, idle6, idle7, idle8]

    # Define edges based on the corners and their respective idle stations
    idle_edges = [
        (corner_UR, idle1[0]),
        (corner_UR, idle2[0]),
        (corner_UL, idle3[0]),
        (corner_UL, idle4[0]),
        (corner_BR, idle5[0]),
        (corner_BR, idle6[0]),
        (corner_BL, idle7[0]),
        (corner_BL, idle8[0])
    ]

    # initialize map with given properties:  (width, heigth, object_list, agent_list)
    my_map = SimpleMapGenerator(map_size).generate(objs, agents, idle_stations, idle_edges)

    # show environment
    step = 0
    my_map.showMap(step, objs, agents, idle_stations)

    openai_model="gpt-4-0613"
    llm = OPENAI_llm(API_key=keys.OPENAI_api_key, temperature=0.01, OPENAI_model=openai_model)
    # python_handler(llm_response=llm.llm_test(), my_map=my_map, agents=agents, objs=objs)

    R1.setGoal(my_map, R1.position)
    R2.setGoal(my_map, R2.position)
    while True:
        step += 1
        if step == 2:
            python_handler(llm_response=llm.llm_test("R2D2 move to (4, 4)"), my_map=my_map, agents=agents, objs=objs)
        #     R1.setGoal(my_map, (4, 4))
        if step == 8:
            python_handler(llm_response=llm.llm_test("C3PO move to (6, 6)"), my_map=my_map, agents=agents, objs=objs)
        #     R2.setGoal(my_map, (6, 6))
        if keyboard.is_pressed('esc'):
            break
        elif keyboard.is_pressed("enter"):
            python_handler(llm_response=llm.llm_test(), my_map=my_map, agents=agents, objs=objs)

        my_map.move_all(agents, idle_stations)
        # print(f"distance from {R1.name} to {R1.goal}: {dist_func(R1.position, R1.goal)}")

        # # makes the robot go back to initial position
        # for agent in agents:
        #     if agent.position == agent.goal:
        #         agent.setGoal(my_map, agent.initial_position)
        my_map.showMap(step, objs, agents, idle_stations)



