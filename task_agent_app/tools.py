import os
import dotenv
import google.auth
import google.auth.transport.requests
import google.oauth2.id_token
#from google.adk.tools.mcp_toolset import MCPToolset
#from google.adk.tools.mcp_toolset import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams 

MAPS_MCP_URL = os.getenv("MAPS_MCP_URL")
if not MAPS_MCP_URL:
    raise ValueError("MAPS_MCP_URL not set")


BIGQUERY_MCP_URL = os.getenv("BIGQUERY_MCP_URL")
if not BIGQUERY_MCP_URL:
    raise ValueError("BIGQUERY_MCP_URL not set")


def get_maps_mcp_toolset():
    dotenv.load_dotenv()
    maps_api_key = os.getenv('MAPS_API_KEY')
    if not maps_api_key:
        raise ValueError("MAPS_API_KEY missing")
    
    tools = MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=MAPS_MCP_URL,
            headers={    
                "X-Goog-Api-Key": maps_api_key
            },
            timeout=30.0,          
            sse_read_timeout=300.0
        )
    )
    print("MCP Toolset configured for Streamable HTTP connection.")
    return tools


def get_bigquery_mcp_toolset():   
        
    credentials, project_id = google.auth.default(
            scopes=["https://www.googleapis.com/auth/bigquery"]
    )

    credentials.refresh(google.auth.transport.requests.Request())
    oauth_token = credentials.token
        
    HEADERS_WITH_OAUTH = {
        "Authorization": f"Bearer {oauth_token}",
        "x-goog-user-project": project_id
    }

    tools = MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=BIGQUERY_MCP_URL,
            headers=HEADERS_WITH_OAUTH
        )
    )
    print("MCP Toolset configured for Streamable HTTP connection.")
    return tools


