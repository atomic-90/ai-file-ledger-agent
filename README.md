# ai-file-ledger-agent

Multi agent AI system that helps users manage, search, and understand their files using natural language

# Features

•Store the file metadata and content
•Retrieve files by name, date, type
•Summarize fil content using AI
•Set reminders for file review
•Multi-agent architecture (Coordinator + File + Reminder agents + Location agents(in future))
•Deployed on google cloud Run

# Architecture

User -> Root Agent -> File Agent -> BigQuery
|
Reminder Agent
|
Response Formatter

# Tech Stack

•Python
•Google ADK (Agent Development Kit)
•Big Query
•Cloud Run
•GitHub

# Project Structure

task_agent_app/
├── agent.py
├── tools.py
├── **init**.py
├── requirements.txt
└── .env

data/
└── sample_files.csv
