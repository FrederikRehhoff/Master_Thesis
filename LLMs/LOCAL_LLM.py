from pydantic import BaseModel, Field
from typing import Optional

from langchain.llms import Ollama


class task_info(BaseModel):
    TASK: Optional[str] = Field(description="The task defined by the user")
    AGENT: Optional[str] = Field(description="The name of the agent that needs to solve the task")
    ACTION: Optional[str] = Field(description="the action the agent needs to do")
    SOLVABLE: Optional[bool] = Field(description="determines if the task given is solvable by the agents")


class local_llm(object):
    """TODO:
        1. Make an agent that uses the ReAct template, and make it able to run in steps
            Solution ideas:
                a. make a simple agent that outputs the result to the first subtask,
                and give it tools and memory so it solves the task iteratively in the code
                b. make it use function calling to lock it in a bool loop until the condition
                is meet i.e. 'Is agent at pos (yes or no)'"""
    def __init__(self, model="llama2"):
        self._model = Ollama(model=model)
        self._template = """
        You are a helpful assistant that dictate the actions of mobile agents. you will be assigned a task
        by the user, and you would then respond with the format:

        {format_instructions}

        The agents are mobile robots with different properties such as "gripper" or "broom", that makes them excellent
        at solving different tasks. The agents operate in a 2D grid world. each cell has a position (x, y)
        where x is the row index and y is the column index.

        These are the following actions the agent can make:
        move(x, y) which moves the robot to position (x, y)
        grab which makes the robot grab an object at it's current location

        Here are some examples of the task and response:

        task = R2D2 collect an apple located at (4, 4)
        response = TASK: collect an apple located at (4, 4) AGENT: R2D2 ACTION: move(4, 4) SOLVABLE: True

        task = move R2D2 to (2, 1)
        response = TASK: move agent to (2, 1) AGENT: R2D2 ACTION: move(2, 1) SOLVABLE: True

        task = C3P0 fetch an orange located at (0, 4)
        Response = TASK: fetch an orange located at (0, 4) AGENT: C3P0 ACTION: move(0, 4) SOLVABLE: True
        
        Task = R2D2 grab object
        Response = TASK: grab object AGENT: R2D2 ACTION: grab() SOLVABLE: True
        
        task = what is the capital of france?
        response = SOLVABLE: False
        
        You are to always respond in the format {format_instructions}.
        
        {task}.
        """

    def local_llm_test(self):
        print("work in progress")
