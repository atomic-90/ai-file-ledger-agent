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

•Python <br />
•Google ADK (Agent Development Kit)<br />
•Big Query<br />
•Cloud Run<br />
•GitHub

# Project Structure

task_agent_app/<br />
├── agent.py<br />
├── tools.py<br />
├── **init**.py<br />
├── requirements.txt<br />
└── .env<br />

data/<br />
└── sample_files.csv
