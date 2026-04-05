import os
import dotenv
from . import tools   
#from google.adk.agents import LlmAgent
from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools.tool_context import ToolContext

dotenv.load_dotenv()

PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'project_not_set')

maps_toolset = tools.get_maps_mcp_toolset()
bigquery_toolset = tools.get_bigquery_mcp_toolset()

def save_query(tool_context : ToolContext, user_query: str):
    tool_context.state["USER_QUERY"] = user_query
    return {"saved":user_query}


planner_agent = Agent(
    model='gemini-3.1-flash-lite',
    name='planner_agent',
    instruction="""
                You are a planner.

                USER QUERY:
                { USER_QUERY }

                Break it into steps.

                Rules:
                - Files / ledger / reminder → BigQuery
                - Location / places → Maps
                - Multi-step → separate clearly

                Output :

                PLAN:
                1. <step>
                2. <step>

                TOOLS:
                - BigQuery 
                - Maps

                DO NOT execute.

                """,
    output_key="PLAN"
)

task_agent = Agent(
    model='gemini-3.1-flash-lite',
    name='task_agent',
    instruction=f"""
                You are an execution agent.

                USER QUERY:
                {{USER_QUERY}}

                PLAN:
                {{PLAN}}

                ----------------------------------
                DATABASE:
                Project: {PROJECT_ID}
                Dataset: file_ledger

                TABLES:

                ledgers(ledger_id, name, location, created_at)
                files(file_id, ledger_id, name, type, content, location, created_at)
                reminders(reminder_id, file_id, ledger_id, reminder_text, remind_at, created_at)

                ----------------------------------

                ID RULES:

                - ledger_id → "ledger_1", "ledger_2"
                - file_id → "ledger_1_1", "ledger_1_2"
                - reminder_id → "rem_1", "rem_2"

                Generate using COUNT + 1.

                ----------------------------------

                CREATE LEDGER:

                1. Generate ID:
                SELECT CONCAT("ledger_", CAST(COUNT(*) + 1 AS STRING)) FROM file_ledger.ledgers;

                2. Decide name:
                - Use user input OR generate meaningful name

                3. Optional:
                - If user mentions location → store it

                4. Insert:
                INSERT INTO file_ledger.ledgers (ledger_id, name, location)
                VALUES ("ledger_X", "name", "location");

                ----------------------------------

                CREATE FILE:

                1. Find ledger_id:
                SELECT ledger_id FROM file_ledger.ledgers
                WHERE LOWER(name) LIKE "%keyword%";

                2. Generate file_id:
                SELECT CONCAT("ledger_X_", CAST(COUNT(*) + 1 AS STRING))
                FROM file_ledger.files
                WHERE ledger_id = "ledger_X";

                3. Decide:
                - file name (AI or user)
                - type (txt/pdf/docx)

                4. Content:
                - MUST be ≤ 1000 words
                - If longer → reject

                5. Optional:
                - If user gives location → store it

                6. Insert:
                INSERT INTO file_ledger.files
                (file_id, ledger_id, name, type, content, location)
                VALUES (...);

                ----------------------------------

                LOCATION LOGIC (VERY IMPORTANT):

                - Location can exist at:
                    ✔ Ledger level
                    ✔ File level

                - If file has no location:
                    → inherit from ledger

                - If user asks:
                    "files in Dublin"
                → query both:

                SELECT * FROM file_ledger.files
                WHERE location = "Dublin"
                OR ledger_id IN (
                SELECT ledger_id FROM file_ledger.ledgers WHERE location = "Dublin"
                );

                ----------------------------------

                SEARCH FILE:

                - By content:
                SELECT * FROM file_ledger.files
                WHERE LOWER(content) LIKE "%keyword%";

                ----------------------------------

                REMINDER:

                1. Generate ID:
                SELECT CONCAT("rem_", CAST(COUNT(*) + 1 AS STRING))
                FROM file_ledger.reminders;

                - If reminder is for a file:
                  → include file_id AND ledger_id

                - If reminder is for a ledger:
                  → include only ledger_id

                2. Insert:
                INSERT INTO file_ledger.reminders
                (reminder_id, file_id, ledger_id, reminder_text, remind_at)
                VALUES (...);

                ----------------------------------

                MAPS USAGE:

                - If user asks:
                  "nearest bakery"
                  "cafes near me"

                → Use Maps tool ONLY

                ----------------------------------

                RULES:

                - ALWAYS use BigQuery for data
                - ALWAYS execute ALL steps
                - NEVER hallucinate tools
                - NEVER say "filesystem"
                - ALWAYS return final result
                """
                
    ,
    tools=[maps_toolset, bigquery_toolset]
)

workflow = SequentialAgent(
    name="workflow",
    sub_agents=[
        planner_agent,
        task_agent
    ]
)

root_agent = Agent(
    model='gemini-3.1-flash-lite',
    name='root_agent',
    instruction="""
                You are the entry point.

                Steps:
                1. Save user query
                2. Pass it to workflow
                3. Ensure final result is returned
                Do NOT stop after planning.
                """,
    tools=[save_query],
    sub_agents=[workflow]
)

