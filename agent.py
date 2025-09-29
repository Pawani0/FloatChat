from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.memory import ConversationBufferMemory
from Tools.sql_tools import generate_postgresql_query, fire_sql
from Tools.plotting_tools import plot_profile, plot_ts_diagram, plot_trajectory
import dotenv
import os

# Load environment variables from .env file
dotenv.load_dotenv()
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)


# ---------------- Tool Wrappers ----------------
tools = [
    Tool(name="SQLGenerator", func=generate_postgresql_query,
         description="Generate SQL query string from natural language user query. just pass base user query in natural language that you got as an argument and it will returns SQL Query according to the db schema string. Do not give sql query to this function."),

    Tool(name="SQLExecutor", func=fire_sql,
         description="Execute SQL query string on Argo database and return results. It takes SQL Query string as argument and returns the fetched data in the form of dictionary."),

    Tool(name="Plot_Profile", func=plot_profile,
         description="""Fetches and plots the Temperature and Salinity data against Depth for a given profile ID.

    This tool should be used when a user asks to 'plot a profile', 'visualize profile data',
    or requests a Temperature/Salinity plot for a specific profile identifier.

Input format:
- a comma-separated string: "1900043, 1900089"

Output:
- File path(s) of saved profile plots."""),

    Tool(name="plot_ts_diagram", func=plot_ts_diagram,
         description="""
    Generates and saves a detailed Temperature-Salinity (T-S) diagram for a given profile ID.

    This plot shows the relationship between Conservative Temperature and Absolute Salinity.
    It includes contours of constant seawater density (isopycnals), and individual data points are colored by their depth.
    Use this tool specifically when a user asks for a "T-S diagram," "T-S plot," or to visualize water mass properties for a profile.

Input format:
- a comma-separated string: "1900043, 1900089"

Output:
- File path(s) of saved T-S diagram plots.
    """),

    Tool(name="plot_trajectory", func=plot_trajectory,
         description="""Use when the user asks to plot or map the trajectory of a float/platform.

Input format:
- a comma-separated string: "1900043, 1900089"

Output:
- File path(s) of saved trajectory plots.
""")
]

# ---------------- Agent ----------------
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="chat-conversational-react-description",
    memory=memory,
    max_iterations=150,
    handle_parsing_errors=True,
    verbose=True
)

# ---------------- Example Run ----------------
while True:
  user_query = input("Enter your query : ")
  if user_query.lower == "exit":
    break
  response = agent.run(user_query)
  print(response)

