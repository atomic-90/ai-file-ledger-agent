# ai-file-ledger-agent

Multi agent AI system that helps users manage, search, and understand their files using natural language

# Features

•Store the file metadata and content <br />
•Retrieve files by name, date, type <br />
•Summarize fil content using AI <br />
•Set reminders for file review <br />
•Multi-agent architecture (Coordinator + File + Reminder agents + Location agents(in future)) <br />
•Deployed on google cloud Run

# Architecture

User -> Root Agent -> File Agent -> BigQuery<br />
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;|<br />
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Reminder Agent<br />
&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;|<br />
&emsp;&emsp;&emsp;&emsp;&emsp;&ensp;&emsp;&emsp;&emsp;&emsp;Response Formatter<br />

# Tech Stack

> •Python <br />
> •Google ADK (Agent Development Kit)<br />
> •Big Query<br />
> •Cloud Run<br />
> •GitHub

# Project Structure

```text
ai-file-ledger-agent/
├── data/                       # Pre-generated CSV files for BigQuery
│   ├── sample_files.csv
├── task_agent_app/             # AI Agent Application (ADK)
│   ├── agent.py                # Agent definition
│   ├── tools.py                # Custom tools for the agent
│   ├── **init**.py
│   ├── requirements.txt
│   └── .env
├── setup/                       # Infrastructure setup scripts
│   ├── setup_bigquery.sh        # Script to provision BigQuery dataset and tables
│   └── setup_env.sh             # Script to set up environment variables
├── cleanup/                     # Infrastructure clean up environment
│   ├── cleanup_env.sh           # Script to remove resources in environment
└── README.md
```
