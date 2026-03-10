import os
import psycopg
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.postgres import PostgresSaver

from tools import create_user, get_user, list_users, update_user, delete_user

load_dotenv()

TOOLS = [create_user, get_user, list_users, update_user, delete_user]

SYSTEM_PROMPT = """
You are a user management assistant. You help manage a database of people.

You have access to the following tools:
- create_user: Add a new user to the database
- get_user: Find a user by their ID or email
- list_users: Get a list of users with optional filters
- update_user: Update details of an existing user
- delete_user: Remove a user from the database

User Fields:
Required fields:
- name
- email
- phone_number
- location

Optional fields:
- age
- profession

Rules you must follow:
1. When a user asks to create a new user, collect all required details step by step. Required fields are: name, email, phone_number, location.
2. Age and profession are optional fields. After collecting all required fields, ask the user: "Age and profession are optional fields. Would you like to add them, or should I proceed with creating the user?"
3. If the user provides age or profession, include them when calling the create_user tool.
4. If the user does not want to provide them, proceed without them.
5. Before deleting a user, always ask for confirmation.
6. When retrieving a user, accept either user_id or email.
7. Be conversational and helpful.
"""

# Initialize LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
)

# Bind tools to the model
llm_with_tools = llm.bind_tools(TOOLS)


# Handle the main LLM response
def agent_node(state: MessagesState):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


tool_node = ToolNode(TOOLS)


# Build and configure the agent graph
def create_agent():
    graph = StateGraph(MessagesState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")

    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")

    conn = psycopg.connect(os.getenv("DATABASE_URL"), autocommit=True)
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()

    agent = graph.compile(checkpointer=checkpointer)
    return agent


agent = create_agent()


# Send user message to the agent and return response
def chat(message: str, thread_id: str) -> str:
    config = {"configurable": {"thread_id": thread_id}}

    response = agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
    )

    return response["messages"][-1].content