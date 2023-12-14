from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate, SystemMessage, HumanMessagePromptTemplate
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from typing import Optional

from .API_keys import keys


class task_info(BaseModel):
    TASK: Optional[str] = Field(description="The task defined by the user")
    AGENT: Optional[str] = Field(description="The name of the agent that needs to solve the task")
    ACTION: Optional[str] = Field(description="the action the agent needs to do")
    SOLVABLE: Optional[bool] = Field(description="determines if the task given is solvable by the agents")


class OPENAI_llm(object):
    def __init__(self, API_key=keys.OPENAI_api_key, OPENAI_model="gpt-4-0613", temperature=0.7):
        self._chat_model = ChatOpenAI(openai_api_key=API_key, temperature=temperature, model=OPENAI_model)
        self._boot_template = """
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

    def llm_test(self):
        parser = PydanticOutputParser(pydantic_object=task_info)

        task = input("how can i help? \n\n> ")

        message = HumanMessagePromptTemplate.from_template(template=self._boot_template)
        chat_prompt = ChatPromptTemplate.from_messages(messages=[message])
        final_prompt = chat_prompt.format_prompt(
            task=task,
            format_instructions=parser.get_format_instructions()
        )
        response = self._chat_model(final_prompt.to_messages())
        # print(f"LLM response:\n {response}")
        data = parser.parse(response.content)
        # print(f"{data.SOLVABLE}")
        return data
