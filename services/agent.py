from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from config import settings
from services.tools import calculator


@tool
def calculate(a: float, b: float, operation: str):
    """Calculate addition, subtraction, multiplication, or division."""
    return calculator(a, b, operation)


llm = ChatOpenAI(
    model="gpt-5-mini",
    api_key=settings.openai_api_key,
    timeout = 30
)

agent = create_agent(
    llm,
    tools=[calculate]
)


def ask_agent(question: str):
    result = agent.invoke({
        "messages": [
            ("user", question)
        ]
    })

    return result["messages"][-1].content


if __name__ == "__main__":
    answer = ask_agent(
        "I have 3 hours available. How many minutes is that? Use the calculator."
    )

    print(answer)    