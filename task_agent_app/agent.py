import os
import dotenv
from . import tools   
from google.adk.agents import LlmAgent

dotenv.load_dotenv()

PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'project_not_set')

maps_toolset = tools.get_maps_mcp_toolset()
bigquery_toolset = tools.get_bigquery_mcp_toolset()

root_agent = LlmAgent(
    model='gemini-3.1-pro-preview',
    name='task_agent',
    description='Multi-agent system for managing files, tasks, and location-based queries.',
    instruction=f"""
                You are an intelligent assistant that helps users manage files, tasks, and location-based queries.

                You have access to the following tools:
                1. BigQuery tools → for file data, tasks, reminders. Run all query jobs from project id: {PROJECT_ID}
                When using BigQuery tools:
                - Generate valid SQL queries
                - Use dataset: file_ledger
                - Use table: files
                - Use correct column names: name, type, content, created_at
                - Always return relevant results    
                2. Maps tools → for location-based queries

                Guidelines:
                - When the user asks about files, tasks, reminders, or stored data → use BigQuery tools
                - When the user asks about locations, places, or directions → use Maps tools
                - If a tool is needed, call the appropriate tool

                IMPORTANT:
                - The tool will return the final answer
                - After calling a tool, return the tool result to the user
                - Do NOT generate your own answer if a tool is used
                - If no tool is needed, respond normally

                Be clear, concise, and helpful.
                
                """,
    tools=[maps_toolset, bigquery_toolset]
)