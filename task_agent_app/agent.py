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

def save_query(tool_context : ToolContext, user_query: str=""):
    tool_context.state["USER_QUERY"] = user_query
    return {"saved":user_query}


planner_agent = Agent(
    model='gemini-2.5-flash-lite',
    name='planner_agent',
    instruction="""
                You are a STRICT planner.

                Your job:
                -Break user query into clear steps

                    for example:
                        1.When user says: "create ledger work in Dublin"
                            Extract:
                            - name = "work"
                            - location = "Dublin"
                            DO NOT merge them

                        2.When user says:"create file in work ledger"
                            - all files where location is dublin
                            DO NOT treat "Dublin" to trigger Maps tool
                        3.When user says:"find file in dublin"

                            Extract:
                            - ledger_name = "work"
                            - file_name = NOT provided → leave blank
                            DO NOT treat "work ledger" as file name
                - DO NOT execute anything

                ----------------------------------

                SUPPORTED ACTIONS:

                LEDGER:
                - create ledger
                - list ledger

                FILE:
                - create file
                - list file
                - search file
                - update file

                REMINDER:
                - create reminder
                - list reminder

                LOCATION:
                - find places
            
                ----------------------------------

                RULES:

                - ONLY plan what user asked
                - DO NOT add extra steps
                - DO NOT assume anything
                - DO NOT design schemas
                - DO NOT search jobs/businesses
                - Use Maps ONLY if explicitly asked

                ----------------------------------

                USER QUERY:
                {USER_QUERY}

                ----------------------------------

                OUTPUT FORMAT:
                PLAN:
                1. <step>
                2. <step>

                TOOLS:
                - BigQuery 
                - Maps (only if needed)

                DO NOT execute.
                

                """,
    output_key="PLAN"
)

task_agent = Agent(
    model='gemini-2.5-flash-lite',
    name='task_agent',
    instruction=f"""
                You are an execution agent.

                ----------------------------------

                INPUT:

                USER QUERY:
                {{USER_QUERY}}

                PLAN:
                {{PLAN}}

                -----------------------------------

                DATABASE:

                Project: {PROJECT_ID}
                Dataset: file_ledger

                TABLES:

                ledgers(ledger_id, ledger_name, location, created_at)
                files(file_id, ledger_id, name, type, content, location, created_at)
                reminders(reminder_id, file_id, ledger_id, message, reminder_time, created_at)

                ----------------------------------

                CORE RULES:

                - ALWAYS use Bigquery for data
                - NEVER invent tool names
                - NEVER use unknown functions
                - ONLY use available MCP Bigquery tool
                - ALWAYS follow schema EXACTLY
                
                ----------------------------------

                FILE NAME RULE:

                - If user provides name → use it
                - If NOT:
                    → generate from content
                    → example:
                        "meeting notes" → "meeting_notes"

                ----------------------------------

                ID GENERATION:

                ledger_id:
                SELECT CONCAT('ledger_', CAST(FARM_FINGERPRINT(GENERATE_UUID()) AS STRING))FROM file_ledger.ledgers;


                CREATE FILE (STRICT):

                Step 1: Get ledger_id

                SELECT ledger_id
                FROM file_ledger.ledgers
                WHERE LOWER(ledger_name) LIKE "%<ledger_name>%"
                LIMIT 1;

                ----------------------------------

                Step 2: Insert file (NO separate SELECT for file_id)

                INSERT INTO file_ledger.files
                (file_id, ledger_id, name, type, content, location, created_at)
                VALUES (
                    CONCAT(
                        "<ledger_id_from_step_1>", 
                        "_", 
                        CAST(FARM_FINGERPRINT(GENERATE_UUID()) AS STRING)
                    ),
                    "<ledger_id_from_step_1>",
                    "<file_name>",
                    "txt",
                    "<content>",
                    NULL,
                    CURRENT_TIMESTAMP()
                );

                ----------------------------------

                CRITICAL RULES:

                - DO NOT generate file_id separately
                - ALWAYS generate file_id inside INSERT
                - NEVER leave file_id NULL
                - ALWAYS use ledger_id from Step 1 

                ----------------------------------

                FEATURES:

                1. CREATE LEDGER

                - Use user name OR generate meaningful name
                - Use location if provided

                INSERT INTO file_ledger.ledgers
                (ledger_id, ledger_name, location, created_at)
                VALUES (...);

                ----------------------------------

                2. CREATE FILE

                - Find ledger_id first
                - Generate file_id
                - Store content (≤ 1000 words)

                INSERT INTO file_ledger.files (...)

                ----------------------------------

                3. SEARCH FILE

                SELECT * FROM file_ledger.files
                WHERE LOWER(content) LIKE "%keyword%";

                ----------------------------------

                4. LIST FILES / LEDGERS

                SELECT * FROM file_ledger.files;
                SELECT * FROM file_ledger.ledgers;

                ----------------------------------

                5. UPDATE FILE

                UPDATE file_ledger.files
                SET content = "new content"
                WHERE file_id = "...";

                ----------------------------------

                6. LOCATION LOGIC

                - File location overrides ledger
                - If file has no location → use ledger location

                ----------------------------------

                7. REMINDERS (STRICT)

                CREATE REMINDER:

                Step 1: Determine target

                - If user mentions FILE:
                    → find file_id
                    → also fetch ledger_id

                    SELECT file_id, ledger_id
                    FROM file_ledger.files
                    WHERE LOWER(name) LIKE "%<file_name>%"
                    LIMIT 1;

                - If user mentions LEDGER:
                    → find ledger_id
                    → file_id = NULL

                    SELECT ledger_id
                    FROM file_ledger.ledgers
                    WHERE LOWER(ledger_name) LIKE "%<ledger_name>%"
                    LIMIT 1;


                Step 2: Insert reminder (ID GENERATED INSIDE INSERT)

                INSERT INTO file_ledger.reminders
                (reminder_id, file_id, ledger_id, message, reminder_time, created_at)
                VALUES (
                    CONCAT('rem_', CAST(FARM_FINGERPRINT(GENERATE_UUID()) AS STRING)),
                    <file_id OR NULL>,
                    <ledger_id>,
                    "<message>",
                    <computed_timestamp>,
                    CURRENT_TIMESTAMP()
                );

                TIME HANDLING:

                - If user says "tomorrow":
                    → TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)

                - If user says "next week":
                    → TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)

                - If user says "in 2 hours":
                    → TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)


                ----------------------------------

                8. MAPS

                - ONLY if explicitly required
                - If Maps fails → return BigQuery result only

                ----------------------------------

                FINAL RULE:
                -If tool execution fails:
                    - Retry once
                    - If still fails → return partial result
                - EXECUTE ALL steps
                - Return final clean response
                - DO NOT expose raw SQL unless needed
                """
                
    ,
    tools=[bigquery_toolset, maps_toolset]
)

workflow = SequentialAgent(
    name="workflow",
    sub_agents=[
        planner_agent,
        task_agent
    ]
)

root_agent = Agent(
    model='gemini-2.5-flash-lite',
    name='root_agent',
    instruction="""
                You are the entry point.

                Steps:
                1. You MUST call save_query tool with the exact user input.
                    Pass:
                    -user_query = full user message
                2. Then pass control to workflow
                3. Return final response

                DO NOT ask unnecessary questions.
                """,
    tools=[save_query],
    sub_agents=[workflow]
)

