from map import Map
from map import SimpleMapGenerator
from agent import Agent, robots
from LLMs import keys, ReAct_model
from typing import Annotated, List, Tuple, Union

import logging
import keyboard
import asyncio
import threading
import aioconsole
import time
from concurrent.futures import ThreadPoolExecutor
import getpass
import os
import config


os.environ["OPENAI_API_KEY"] = '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'
os.environ["LANGCHAIN_API_KEY"] = 'ls__c0f826e0c4514d678c5fdec4a48e6b92'
os.environ["TAVILY_API_KEY"] = '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'


def _set_if_undefined(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass(f"Please provide your {var}")


_set_if_undefined("OPENAI_API_KEY")
_set_if_undefined("LANGCHAIN_API_KEY")
_set_if_undefined("TAVILY_API_KEY")

# Optional, add tracing in LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "ReAct"


if __name__ == '__main__':
    # logging.basicConfig(level=logging.INFO)
    # define map size
    x = 10
    y = 10
    map_size = (x, y)

    corner_UR = (map_size[0] - 1, map_size[1] - 1)
    corner_UL = (0, map_size[1] - 1)
    corner_BL = (0, 0)
    corner_BR = (map_size[0] - 1, 0)

    # define object in map:  ('name', placement: (x,y), 'color', number_on_location)
    obj1 = ["Apple", corner_UR, "red", 2]
    obj2 = ["liquid spill", (5, 4), "orange", 1]
    objs = [obj1, obj2]
    config.objs = objs

    "Move Robot2 to location (5, 4) and remove the liquid spill."

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
    my_map = SimpleMapGenerator(map_size).generate(objs, robots, idle_stations, idle_edges)
    config.my_map = my_map

    # show environment
    step = 0
    my_map.showMap(step, objs, robots, idle_stations)

    # initiate LLM
    llm = ReAct_model()

    async def main_loop():
        step = 0
        while True:
            step += 1
            for obj in objs:
                if obj[3] == 0:
                    objs.remove(obj)
            config.objs = objs

            # Update map
            my_map.move_all(robots, idle_stations)
            config.my_map = my_map

            # Display updated map
            my_map.showMap(step, objs, robots, idle_stations)

            await asyncio.sleep(0.1)  # Add a small delay to avoid maxing out CPU


    def handle_keyboard_input(loop):
        while True:
            if keyboard.is_pressed("esc"):
                print("ESC pressed, stopping the program.")
                loop.call_soon_threadsafe(loop.stop)
                break
            elif keyboard.is_pressed("page up"):
                print("ENTER pressed, running the model.")
                # Schedule the llm.run() coroutine to be run in the event loop
                asyncio.run_coroutine_threadsafe(llm.run(), loop)
            time.sleep(0.1)  # Use time.sleep for synchronous sleep in the thread


    # Get the current event loop
    loop = asyncio.get_event_loop()

    # Create a separate thread for handling keyboard inputs
    keyboard_thread = threading.Thread(target=handle_keyboard_input, args=(loop,))
    keyboard_thread.start()

    # Run the main loop in the event loop
    loop.run_until_complete(main_loop())

    # Without join, the program might exit here before the keyboard thread completes.
    keyboard_thread.join()

            # print(f"distance from {R1.name} to {R1.goal}: {dist_func(R1.position, R1.goal)}")

            # # makes the robot go back to initial position
            # for agent in agents:
            #     if agent.position == agent.goal:
            #         agent.setGoal(my_map, agent.initial_position)




