from google.adk.tools.tool_context import ToolContext
from google.cloud import bigquery

def get_file_by_name (tool_context : ToolContext, file_name : str):
    print("TOOL EXECUTED")
    client = bigquery.Client()
    query = f"""
        SELECT name, type,content,created_at
        FROM `{tool_context.env['PROJECT_ID']}.file_ledger.files`
        WHERE LOWER(name) = LOWER('{file_name}')
        LIMIT 1
    """
    query_job = client.query(query)
    try:
        results = query_job.result()
    except Exception as e:
        return f"Error executing query: {e}"
    
    for row in results:
        return f"""
            File: {row.name}
            Type: {row.type}
            Content: {row.content}
            Created: {row.created_at}
        """
    
    return f"No file found with name '{file_name}'."

def list_files(tool_context : ToolContext):
    print("DEBUG : list_files tool called")
    try:
        client = bigquery.Client()
        query = f"""
            SELECT name, type,created_at
            FROM `{tool_context.env['PROJECT_ID']}.file_ledger.files`
            ORDER BY created_at DESC
            LIMIT 10
        """
        query_job = client.query(query)
        try:
            results = query_job.result()
        except Exception as e:
            return f"Error executing query: {e}"
        
        files = []
        for row in results:
            files.append(f"-{row.name} ({row.type}) - {row.created_at}")

        if not files:
            return "No files found."
        
        return "\n".join(files)
    except Exception as e:
        return f"ERROR in list_files: {str(e)}"
    

def summarize_file_content(tool_context : ToolContext, file_name : str):
    print("DEBUG : summarize_file_content tool called")
    try:
        client = bigquery.Client()
        query = f"""
            SELECT content
            FROM `{tool_context.env['PROJECT_ID']}.file_ledger.files`
            WHERE LOWER(name) = LOWER('{file_name}')
            LIMIT 1
        """
        query_job = client.query(query)
        try:
            results = query_job.result()
        except Exception as e:
            return f"Error executing query: {e}"
        
        for row in results:
            content = row.content

            summary = content[:200] + "..." if len(content) > 200 else content
            return f"Summary of '{file_name}':\n{summary}"
        
        return f"No file found with name '{file_name}'."
    except Exception as e:
        return f"ERROR in summarize_file_content: {str(e)}"
    
def delete_file_by_name(tool_context : ToolContext, file_name : str):
    print("DEBUG : delete_file_by_name tool called")
    try:
        client = bigquery.Client()
        query = f"""
            DELETE FROM `{tool_context.env['PROJECT_ID']}.file_ledger.files`
            WHERE LOWER(name) = LOWER('{file_name}')
        """
        query_job = client.query(query)
        try:
            query_job.result()
            return f"File '{file_name}' deleted successfully."
        except Exception as e:
            return f"Error executing delete query: {e}"
    except Exception as e:
        return f"ERROR in delete_file_by_name: {str(e)}"
    
