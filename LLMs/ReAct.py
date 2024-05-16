from langsmith import trace
from langchain_core.pydantic_v1 import BaseModel, Field
import operator
from .tools import control_tools, selection_tools, misc_tools
from typing import Any, Callable, List, Optional, TypedDict, Union, Tuple, Annotated

from langchain.agents import AgentExecutor, create_openai_tools_agent, create_tool_calling_agent
from langgraph.prebuilt import create_agent_executor
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
import functools

from langchain.chains.openai_functions import create_structured_output_runnable
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.openai_functions import create_openai_fn_runnable
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from langgraph.graph import END, StateGraph
import aioconsole



class PlanExecute(TypedDict):
    input: str
    plan: List[str]
    current_step: str
    # Used to route work. The supervisor calls a function
    # that will update this every time it makes a decision
    next: str
    # The reason behind the member choice
    reasoning: str
    past_steps: Annotated[List[Tuple], operator.add]
    response: List[str]
    robot_name: str
    tool_property: str
    item: str
    item_position: Tuple[int]


class Plan(BaseModel):
    """Plan to follow in future"""

    steps: List[str] = Field(
        description="different steps to follow, should be in sorted order"
    )
    current_step: str = Field(
        description="the first step to follow as per the steps variable"
    )


class Response(BaseModel):
    """Response to user."""
    robot_name: str = Field(
        description="The robot that solved the task i.e Robot22"
    )
    tool_property: str = Field(
        description="The tool property of {robot_name} i.e gripper"
    )
    item: str = Field(
        description="The item that is being manipulated i.e toolkit"
    )
    item_position: str = Field(
        description="The position of {item} i.e (11, 8)"
    )
    response: str


def create_executor_agent(
    llm: ChatOpenAI,
    tools: list,
    system_prompt: str,
) -> str:
    """Create a function-calling agent and add it to the graph."""
    system_prompt += """\nWork autonomously according to your specialty, using the tools available to you.
    Do not ask for clarification.
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt,
            ),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            (
                "human",
                "{input}",
            ),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = create_agent_executor(agent, tools)
    return executor


def create_team_supervisor(llm: ChatOpenAI, system_prompt, members) -> str:
    """An LLM-based router."""
    options = members
    function_def = {
        "name": "route",
        "description": "Select the next role.",
        "parameters": {
            "title": "routeSchema",
            "type": "object",
            "properties": {
                "next": {
                    "title": "Next",
                    "anyOf": [
                        {"enum": options},
                    ],
                },
                "reasoning": {
                    "type": "string",
                    "description": "The reason behind the choice of member"
                }
            },
            "required": ["reasoning", "next"],
        },
    }
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                "{current_step}",
            ),
            (
                "system",
                "Given the conversation above, who should act next? Select one of: {options}, and remember to give reasoning behind the choice",
            ),
        ]
    ).partial(options=str(options), team_members=", ".join(members))
    return (
        prompt
        | llm.bind_functions(functions=[function_def], function_call="route")
        | JsonOutputFunctionsParser()
    )


class ReAct_model(object):
    def __init__(self,
                 controller_tools=control_tools,
                 selector_tools=selection_tools,
                 misc_agent_tools=misc_tools,
                 llm_agents="gpt-4-1106-preview",
                 llm_planner="gpt-4-1106-preview",
                 ):

        control_agent = create_executor_agent(
            ChatOpenAI(model=llm_agents),
            controller_tools,
            """
            You are an agent that control robots actions using the tools available to you.
            remember you are only able to grab/remove the items and not the robots tool property. this is the list of tool properties: [lawnmower, gripper, tow hook, saw, screwdriver, mop, spray nozzle, broom, front loader, vacuum].
             which are not to be grabed or removed.
            """
        )

        robot_selector_agent = create_executor_agent(
            ChatOpenAI(model=llm_agents),
            selector_tools,
            """
            You are a agent with the purpose to select the best suited robot for the task. A robot can have the following tool properties: [lawnmower, gripper, tow hook, saw, screwdriver, mop, spray nozzle, broom, front loader, vacuum].
            If a specified robot is already selected to solve the task, use select_known_robot_tool.
            Here is an example of that.
    
            EXAMPLE: 
            task = "Move robot_name to location (2, 11) and sort the recyclables."
            Robot = robot_name
            END EXAMPLE
    
            remember to select the most apropriate tool_property for the task i.e a gripper for a task where something needs to be picked up.
    
            here is a list of items, and what tool property can manipulating that item:
    
            toolkit = gripper
            liquid spill = mop
            large debris = gripper, front loader 
            dust = vacuum, broom
            grass = lawnmower
            small debris = broom, vacuum 
            vehicle = tow hook
            construction materials = gripper, front loader, tow hook
            tree branches = saw
            screws = screwdriver
    
            remember that each of the items in the list is a category of it's own
    
        """
        )

        misc_agent = create_executor_agent(
            ChatOpenAI(model=llm_agents),
            misc_agent_tools,
            """
            You are an agent that can answer general questions and messages that doesn't have anything to do with making a robot solve a complex task.
            """
        )

        supervisor_agent = create_team_supervisor(
            ChatOpenAI(model=llm_agents),
            """
            You are a supervisor tasked with routing the current_step to the following workers: Controller, Robot_selector, misc_agent.
            Given the following user request, respond with the worker to act next and the reason behind the choice.
            The selected worker will perform the current_step.
    
            Controller:
            Reponsible for controlling the robots with a set of tools. the tools are: [move_robot, wait, grab_or_remove_item, robot_status_change].
    
            tool functionality:
                - move_robot(robot_name, desired_position): Moves the selected robot to a given position.
                - grab_or_remove_item(robot_name, item_name): grabs the item on the robots location and adds it to the robots inventory.
                - robot_status_change(robot_name, status): changes the current status of the robot to one of the statuses: idle, active, charging. This should only be used to set the robots status to idle after the objective is complete.
                - wait(robot_name): This function is used to allow the robots time to move to the desired_position position. This function should always be called in the next step of the plan after move_robot.
                
            Robot_selector:
            Reponsible for selecting the correct robot using tools: [robot_selection_tool, select_known_robot_tool]
    
            tool functionality:
                - robot_selection_tool(desired_robot_tool_property, item_position): If no robot is specified in the objective, then this tools is to be used to determine the best suited robot to solve the objective.
                - select_known_robot_tool(robot_name, desired_robot_tool_property): If a robot is specified in the objective then this tool is to be used to determined if the robot is equipped with a tool property capable of solving the objective.
    
            misc_agent:
            Reponsible for anwsering more generic questions with tool: [agent_response_tool].
    
            """,
            ["Controller", "Robot_selector", "misc_agent"],
        )

        planner_prompt = ChatPromptTemplate.from_template(
            """For the given objective, come up with a simple step by step plan. \
            This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
            The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.
        
            When making the plan, keep in mind the executor agents capabilities:
        
            Controller:
            Reponsible for controlling the robots with a set of tools. the tools are: [move_robot, wait, grab_or_remove_item, robot_status_change].
        
            tool functionality:
                - move_robot(robot_name, desired_position): Moves the selected robot to a given position.
                - grab_or_remove_item(robot_name, item_name): grabs the item on the robots location and adds it to the robots inventory.
                - robot_status_change(robot_name, status): changes the current status of the robot to one of the statuses: idle, active, charging. This should only be used to set the robots status to idle after the objective is complete.
                - wait(robot_name): This function is used to allow the robots time to move to the desired_position position. This function should always be called in the next step of the plan after move_robot.  This function is only a check, and might need to be used multiple times after the move_robot function
                
            Robot_selector:
            Reponsible for selecting the correct robot using tools: [robot_selection_tool, select_known_robot_tool]
        
            tool functionality:
                - robot_selection_tool(desired_robot_tool_property, item_position): If no robot is specified in the objective, then this tools is to be used to determine the best suited robot to solve the objective.
                - select_known_robot_tool(robot_name, desired_robot_tool_property): If a robot is specified in the objective then this tool is to be used to determined if the robot is equipped with a tool property capable of solving the objective.
        
                Here is an example of a task with and without a specified robot.
        
                EXAMPLE WITH SPECIFIED ROBOT:
                 - Move Robot22 to location (6, 1) and remove the toolkit.
        
                EXAMPLE WITHOUT SPECIFIED ROBOT:
                 - Move to location (9, 4) and remove the construction materials.
        
            misc_agent:
            Reponsible for anwsering more generic questions with tool: [agent_response_tool].
        
            If there is a specified robot for the objective, then always make sure the robot is equipped with a tool property capable of solving the objective. remember to give a tool property example in the same step as the check.
        
            When designing a step by step plan for the objective, keep in mind the required input to the executor agents tools.
        
            A robot can have the following tool properties: [lawnmower, gripper, tow hook, saw, screwdriver, mop, spray nozzle, broom, front loader, vacuum].
        
            {objective}"""
        )
        planner = create_structured_output_runnable(
            Plan, ChatOpenAI(model=llm_planner), planner_prompt
        )

        replanner_prompt = ChatPromptTemplate.from_template(
            """For the given objective, come up with a simple step by step plan. \
            This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
            The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.
    
            When making the plan, keep in mind the executor agents capabilities:
    
            Controller:
            Reponsible for controlling the robots with a set of tools. the tools are: [move_robot, wait, grab_or_remove_item, robot_status_change].
    
            tool functionality:
                - move_robot(robot_name, desired_position): Moves the selected robot to a given position.
                - grab_or_remove_item(robot_name, item_name): grabs the item on the robots location and adds it to the robots inventory.
                - robot_status_change(robot_name, status): changes the current status of the robot to one of the statuses: idle, active, charging. This should only be used to set the robots status to idle after the objective is complete.
                - wait(robot_name): This function is used to allow the robots time to move to the desired_position position. This function should always be called in the next step of the plan after move_robot. This function is only a check, and might need to be used multiple times after the move_robot function
                
            Robot_selector:
            Reponsible for selecting the correct robot using tools: [robot_selection_tool, select_known_robot_tool]
    
            tool functionality:
                - robot_selection_tool(desired_robot_tool_property, item_position): If no robot is specified in the objective, then this tools is to be used to determine the best suited robot to solve the objective.
                - select_known_robot_tool(robot_name, desired_robot_tool_property): If a robot is specified in the objective then this tool is to be used to determined if the robot is equipped with a tool property capable of solving the objective.
    
                Here is an example of a task with and without a specified robot.
    
                EXAMPLE WITH SPECIFIED ROBOT:
                 - Move Robot22 to location (6, 1) and remove the toolkit.
    
                EXAMPLE WITHOUT SPECIFIED ROBOT:
                 - Move to location (9, 4) and remove the construction materials.
    
            misc_agent:
            Reponsible for anwsering more generic questions with tool: [agent_response_tool].
    
            If there is a specified robot for the objective, then always make sure the robot is equipped with a tool property capable of solving the objective. remember to give a tool property example in the same step as the check.
    
            When designing a step by step plan for the objective, keep in mind the required input to the executor agents tools.
    
            A robot can have the following tool properties: [lawnmower, gripper, tow hook, saw, screwdriver, mop, spray nozzle, broom, front loader, vacuum].
    
            Your objective was this:
            {input}
    
            Your original plan was this:
            {plan}
    
            You have currently done the follow steps:
            {past_steps}
    
            Update your plan accordingly. If no more steps are needed and you can return to the user, then respond to the user. Otherwise, fill out the plan. Only add steps to the plan that still NEED to be done. Do not return previously done steps as part of the plan.
            Remember to fill out the response to the user completely.
            """
        )

        replanner = create_openai_fn_runnable(
            [Plan, Response],
            ChatOpenAI(model=llm_planner),
            replanner_prompt,
        )

        self._control_agent = control_agent
        self._robot_selector_agent = robot_selector_agent
        self._misc_agent = misc_agent
        self._supervisor_agent = supervisor_agent
        self._planner = planner
        self._replanner = replanner

    async def controller_execute_step(self, state: PlanExecute):
        task = state["plan"][0]
        agent_response = await self._control_agent.ainvoke({"input": task, "chat_history": []})
        return {
            "past_steps": (task, agent_response["agent_outcome"].return_values["output"])
        }

    async def robot_selector_execute_step(self, state: PlanExecute):
        task = state["plan"][0]
        agent_response = await self._robot_selector_agent.ainvoke({"input": task, "chat_history": []})
        return {
            "past_steps": (task, agent_response["agent_outcome"].return_values["output"])
        }

    async def misc_execute_step(self, state: PlanExecute):
        task = state["plan"][0]
        agent_response = await self._misc_agent.ainvoke({"input": task, "chat_history": []})
        return {
            "past_steps": (task, agent_response["agent_outcome"].return_values["output"])
        }

    async def plan_step(self, state: PlanExecute):
        plan = await self._planner.ainvoke({"objective": state["input"]})
        return {"plan": plan.steps, "current_step": plan.current_step}

    async def replan_step(self, state: PlanExecute):
        output = await self._replanner.ainvoke(state)
        if isinstance(output, Response):
            # return {"response": output.response}
            return {"response": output.response, "robot_name": output.robot_name, "tool_property": output.tool_property,
                    "item": output.item, "item_position": output.item_position}
        else:
            return {"plan": output.steps, "current_step": output.current_step}

    def should_end(self, state: PlanExecute):
        if "response" in state and state["response"]:
            return True
        else:
            return False

    async def run(self):
        workflow = StateGraph(PlanExecute)

        # Add the plan node
        workflow.add_node("planner", self.plan_step)

        # Add supervisor node
        workflow.add_node("supervisor", self._supervisor_agent)

        # Add the execution step nodes
        workflow.add_node("Controller", self.controller_execute_step)
        workflow.add_node("Robot_selector", self.robot_selector_execute_step)
        workflow.add_node("misc_agent", self.misc_execute_step)

        # Add a replan node
        workflow.add_node("replanner", self.replan_step)

        # Define the starting node
        workflow.set_entry_point("planner")

        # From plan we go to supervisor
        workflow.add_edge("planner", "supervisor")

        # Supervisor select one of the executor nodes
        workflow.add_conditional_edges(
            "supervisor",
            lambda x: x["next"],
            {"Controller": "Controller", "Robot_selector": "Robot_selector", "misc_agent": "misc_agent"}
        )

        # The executor nodes return to the replanner
        workflow.add_edge("Controller", "replanner")
        workflow.add_edge("Robot_selector", "replanner")
        workflow.add_edge("misc_agent", "replanner")

        # If task not completed then replan and go to the supervisor
        workflow.add_conditional_edges(
            "replanner",
            # Next, we pass in the function that will determine which node is called next.
            self.should_end,
            {
                # If `tools`, then we call the tool node.
                True: END,
                False: "supervisor",
            },
        )

        # Finally, we compile it!
        # This compiles it into a LangChain Runnable,
        # meaning you can use it as you would any other runnable
        app = workflow.compile()

        task = await aioconsole.ainput("how can I help?\n\n> ")

        config = {"recursion_limit": 100}
        inputs = {"input": task}
        async for event in app.astream(inputs, config=config):
            for k, v in event.items():
                if k != "__end__":
                    print(f"{k}: {v}")

