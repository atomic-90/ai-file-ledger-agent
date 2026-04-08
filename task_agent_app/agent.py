import os
import dotenv
from . import tools 
from google.adk.agents import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools.tool_context import ToolContext

dotenv.load_dotenv()

PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT') or "ai-file-ledger-agent"

maps_toolset = tools.get_maps_mcp_toolset()
bigquery_toolset = tools.get_bigquery_mcp_toolset()
print("BigQuery tools:", bigquery_toolset)

def save_query(tool_context : ToolContext, user_query: str=""):
    tool_context.state["USER_QUERY"] = user_query
    return {"saved":user_query}


planner_agent = Agent(
    model='gemini-2.5-flash',
    name='planner_agent',
    instruction="""
                You are a STRICT planner.

                - Break user query into steps
                - Extract structured values

                SUPPORTED:
                - create ledger
                - list ledger
                - create file
                - list file
                - search file
                - update file
                - delete ledger
                - delete file
                - create reminder
                - list reminder

                RULES:
                - DO NOT execute anything
                - DO NOT invent tools
                - ONLY use:
                    - BigQuery
                    - Maps (if explicitly asked to search location or place)

                USER QUERY:
                {USER_QUERY}

                OUTPUT:

                PLAN:
                1. <step>

                TOOLS:
                - BigQuery
                """,
    output_key="PLAN"
)

task_agent = Agent(
    model='gemini-2.5-flash',
    name='task_agent',
    instruction=f"""
                You are an execution agent.

                INPUT:
                USER QUERY:
                {{USER_QUERY}}

                PLAN:
                {{PLAN}}

                DATABASE:
                Project id: {PROJECT_ID}
                Dataset: file_ledger

                RULES:

                - Use BigQuery MCP tool
                - SELECT → execute_sql_readonly
                - INSERT/UPDATE/DELETE → execute_sql

                IMPORTANT SQL RULE:
                - ALWAYS use SINGLE QUOTES

                ----------------------------------

                DEBUG MODE:

                - AFTER every tool execution:
                    PRINT the raw tool result

                Example:
                DEBUG RESULT:
                <actual tool output>

                ----------------------------------


                MAPS (STRICT):

                - ONLY use Maps tool when user explicitly asks for:
                    → places
                    → nearby locations
                    → restaurants / cafes / etc.

                ----------------------------------

                MAPS QUERY HANDLING:

                - Extract:
                    → place type (e.g., restaurant, cafe)
                    → location (city)

                - Call Maps tool with appropriate parameters

                ----------------------------------

                MAPS OUTPUT RULE:

                AFTER Maps tool execution:

                - You will receive place results

                - Convert into structured text:

                RESULT:
                name=<place_name>, address=<address>

                (one per line)

                ----------------------------------

                IF no places found:

                RESULT:
                EMPTY

                ----------------------------------

                IMPORTANT:

                - DO NOT mix Maps results with BigQuery results
                - If Maps fails → return:
                    "Unable to fetch places at the moment"

                ----------------------------------


                CREATE LEDGER:

                INSERT INTO file_ledger.ledgers
                (ledger_id, ledger_name, location, created_at)
                VALUES (
                CONCAT('ledger_', CAST(FARM_FINGERPRINT(GENERATE_UUID()) AS STRING)),
                '<ledger_name>',
                '<location>',
                CURRENT_TIMESTAMP()
                );

                ----------------------------------

                LIST LEDGERS:

                SELECT ledger_name, location FROM file_ledger.ledgers;

                ----------------------------------

                LIST FILES:

                SELECT name, location FROM file_ledger.files;

                ----------------------------------

                CREATE FILE:

                1. Get ledger_id:
                SELECT ledger_id FROM file_ledger.ledgers
                WHERE LOWER(ledger_name) LIKE '%<ledger_name>%'
                LIMIT 1;

                2. Insert:
                INSERT INTO file_ledger.files
                (file_id, ledger_id, name, type, content, location, created_at)
                VALUES (
                CONCAT('<ledger_id>', '_', CAST(FARM_FINGERPRINT(GENERATE_UUID()) AS STRING)),
                '<ledger_id>',
                '<file_name>',
                'txt',
                '<content>',
                NULL,
                CURRENT_TIMESTAMP()
                );

                ----------------------------------

                SUMMARIZATION (STRICT):

                - This does NOT use external tools
                - First fetch data using BigQuery
                - Then summarize using LLM

                ----------------------------------

                SUMMARIZE FILE:

                Step 1: Fetch file content

                SELECT name, content
                FROM file_ledger.files
                WHERE LOWER(name) LIKE '%<file_name>%'
                LIMIT 1;

                ----------------------------------

                Step 2: Summarize:

                - Read the "content" field
                - Generate a short summary (2–4 lines)
                - Focus on key points

                ----------------------------------

                SUMMARIZE LEDGER:

                Step 1: Get ledger_id

                SELECT ledger_id
                FROM file_ledger.ledgers
                WHERE LOWER(ledger_name) LIKE '%<ledger_name>%'
                LIMIT 1;

                ----------------------------------

                Step 2: Fetch all files

                SELECT name, content
                FROM file_ledger.files
                WHERE ledger_id = '<ledger_id>';

                ----------------------------------

                Step 3: Summarize:

                - Combine all file contents
                - Generate a concise summary
                - Highlight major themes / topics

                ----------------------------------

                SUMMARIZATION OUTPUT:

                - ALWAYS return:

                RESULT:
                summary=<generated summary>

                ----------------------------------

                DELETE RULES:

                - If deleting file:
                    → use file name

                - If deleting ledger:
                    → first find ledger_id
                    → delete associated files
                    → then delete ledger

                - ALWAYS confirm deletion

                ----------------------------------

                DELETE FILE:

                DELETE FROM file_ledger.files
                WHERE LOWER(name) LIKE '%<file_name>%';

                ----------------------------------

                DELETE LEDGER:

                -- Step 1: Get ledger_id
                SELECT ledger_id FROM file_ledger.ledgers
                WHERE LOWER(ledger_name) LIKE '%<ledger_name>%'
                LIMIT 1;

                -- Step 2: Delete files
                DELETE FROM file_ledger.files
                WHERE ledger_id = '<ledger_id>';

                -- Step 3: Delete ledger
                DELETE FROM file_ledger.ledgers
                WHERE ledger_id = '<ledger_id>';

                ----------------------------------

                ----------------------------------

                REMINDERS (STRICT):

                CREATE REMINDER:

                Step 1: Determine target

                - If user mentions FILE:
                    → find file_id and ledger_id

                    SELECT file_id, ledger_id
                    FROM file_ledger.files
                    WHERE LOWER(name) LIKE '%<file_name>%'
                    LIMIT 1;

                - If user mentions LEDGER:
                    → find ledger_id
                    → file_id = NULL

                    SELECT ledger_id
                    FROM file_ledger.ledgers
                    WHERE LOWER(ledger_name) LIKE '%<ledger_name>%'
                    LIMIT 1;

                ----------------------------------

                Step 2: Insert reminder

                INSERT INTO file_ledger.reminders
                (reminder_id, file_id, ledger_id, message, reminder_time, created_at)
                VALUES (
                    CONCAT('rem_', CAST(FARM_FINGERPRINT(GENERATE_UUID()) AS STRING)),
                    <file_id OR NULL>,
                    <ledger_id>,
                    '<message>',
                    TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL <X> DAY),
                    CURRENT_TIMESTAMP()
                );

                ----------------------------------

                LIST REMINDERS:

                SELECT 
                    reminder_id,
                    message,
                    reminder_time,
                    file_id,
                    ledger_id
                FROM file_ledger.reminders
                ORDER BY reminder_time DESC;

                ----------------------------------

                REMINDER OUTPUT RULE:

                - If reminders exist:
                    → Output:

                    RESULT:
                    message=<extracted message>, time=< extracted time>

                    (one per line)

                - If empty:
                    RESULT:
                    EMPTY

                ----------------------------------

                ----------------------------------

                UPDATE REMINDER:

                Step 1: Identify reminder

                - If user provides message or context:
                    → find reminder_id

                    SELECT reminder_id
                    FROM file_ledger.reminders
                    WHERE LOWER(message) LIKE '%<keyword>%'
                    LIMIT 1;

                ----------------------------------

                Step 2: Update reminder

                - If updating message:

                UPDATE file_ledger.reminders
                SET message = '<new_message>'
                WHERE reminder_id = '<reminder_id>';

                ----------------------------------

                - If updating time:

                UPDATE file_ledger.reminders
                SET reminder_time = 
                    TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL <X> DAY)
                WHERE reminder_id = '<reminder_id>';

                ----------------------------------

                - If updating both:

                UPDATE file_ledger.reminders
                SET 
                    message = '<new_message>',
                    reminder_time = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL <X> DAY)
                WHERE reminder_id = '<reminder_id>';

                ----------------------------------

                TIME HANDLING:

                - "tomorrow" → INTERVAL 1 DAY
                - "next week" → INTERVAL 7 DAY
                - "in 2 hours" → INTERVAL 2 HOUR

                ----------------------------------

                UPDATE OUTPUT:

                RESULT:
                SUCCESS

                ----------------------------------

                OUTPUT:

                AFTER TOOL EXECUTION:

                - You will receive tool results (rows of data)

                - You MUST convert the tool result into plain text

                - Format as simple JSON-like text so next agent can read it

                Example:

                If result:
                ["ledger_name": "work", "location": "Dublin" ]

                Output EXACTLY:
                RESULT:
                ledger_name=work, location=Dublin

                If multiple rows:
                RESULT:
                ledger_name=work, location=Dublin
                ledger_name=personal, location=NYC

                If no rows:
                RESULT:
                EMPTY

                - NEVER stop after tool call
                - ALWAYS produce output text and pass it to next next agent
                """
                ,
    tools=[bigquery_toolset, maps_toolset]
)

response_agent = Agent(
    model='gemini-2.5-flash',
    name='response_agent',
    instruction="""
                You are a response formatter.

                INPUT:
                - result from previous step

                ----------------------------------

                    IF RESULT contains summary:

                    "Here is your summary:
                    <summary>"
                ----------------------------------

                RULES:
                -Convert the json like format or maps output or input recieved from previous agent into user friendly output.
                - ALWAYS give suugestions with respect to it if required
                - NEVER stay empty

                

                NEVER output raw SQL
                """
)


workflow = SequentialAgent(
    name="workflow",
    sub_agents=[
        planner_agent,
        task_agent,
        response_agent
    ]
)

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    instruction="""
                You are the entry point.
                -You MUST call save_query tool with the exact user input.
                    Pass:
                    -user_query = full user message
                - Then Pass saved user query to workflow
                - Return final response

                DO NOT call tools directly.
                """,
    tools=[save_query],
    sub_agents=[workflow]
)