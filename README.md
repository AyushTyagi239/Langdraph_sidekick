# Sidekick – Self-Verifying AI Agent

Sidekick is a **goal-driven AI agent** designed to operate like a personal co-worker rather than a one-shot chatbot.  
It understands user tasks, uses external tools to execute them, and evaluates its own output against **explicit success criteria**, retrying automatically until the task is correctly completed or clarification is required.

Unlike traditional chatbots that answer once and rely on the user to fix mistakes, Sidekick introduces **self-verification, retry loops, and controlled termination**, making it suitable for **production-grade workflows**.

---

## Badges

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Agentic AI](https://img.shields.io/badge/Agentic-AI-purple)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-orange)

---

## Demo & Visuals

### 📸 Recommended Screenshots
- Sidekick UI (task + success criteria input)
- Agent workflow / architecture diagram
- Mobile push notification on task completion

_Add screenshots in a `/screenshots` folder and reference them here._

---

## Why Sidekick?

### Problem
Most AI systems generate a response once and stop, regardless of correctness or completeness.

### Solution
Sidekick introduces an **agent loop** where:

- A **Worker LLM** executes the task  
- **Tools** are used when necessary  
- An **Evaluator LLM** checks the output against success criteria  
- The agent **retries automatically** if needed  

This makes **“done” a measurable state**, not an assumption.

---

## Features

- Goal-driven AI agent architecture  
- Explicit success criteria for task completion  
- Automatic retry and self-correction  
- Human-in-the-loop clarification when tasks are ambiguous  
- Tool-aware decision making  
- Push notifications on task completion  

---

## Supported Tools

The agent can dynamically choose and use the following tools:

- 🧭 **Browser Automation** – Playwright (real Chromium browser)  
- 🔎 **Web Search** – Google Serper API  
- 📚 **Knowledge Lookup** – Wikipedia  
- 🧮 **Python Execution** – Python REPL  
- 📂 **File Management** – Read/write files in a sandboxed environment  
- 🔔 **Push Notifications** – Pushover integration  

---

## Getting Started

### Prerequisites

- Python **3.10+**
- Node.js (optional, for Playwright dependencies)
- Git
- API keys for:
  - OpenAI-compatible LLM provider
  - Google Serper API
  - Pushover (optional)

---

### Installation

```bash
git clone https://github.com/your-username/sidekick.git
cd sidekick
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt



Environment Variables

Create a .env file:

OPENAI_API_KEY=your_key_here
SERPER_API_KEY=your_key_here
PUSHOVER_TOKEN=your_token_here
PUSHOVER_USER=your_user_key_here

Usage
Run the Application
python app.py


This launches a Gradio UI where you can:

Enter a task

Define success criteria

Observe agent execution, retries, and evaluation

Example Task
Task
Research a current technical topic and summarize it.

Success Criteria
The response must be accurate, well-structured, and explicitly confirm whether the criteria is satisfied.

Agent Behavior

Uses web search and/or browser automation

Generates a structured summary

Evaluates output against success criteria

Retries if incomplete

Sends a push notification upon completion

Architecture Overview
User
 ↓
Worker LLM (Task Execution)
 ↓
Tool Router → External Tools
 ↓
Evaluator LLM (Quality Check)
 ↓
Retry Loop OR Completion


This architecture is implemented using LangGraph for deterministic control flow and state management.

Project Status & Roadmap
Current Features

 Tool-using agent

 Success-criteria-based evaluation

 Automatic retry loop

 Push notification support

 Gradio UI

Planned Enhancements

 Persistent task history

 Multi-agent collaboration

 Fine-grained evaluation metrics

 Dockerized deployment

Contributing

Contributions are welcome.
You can:

Open an issue for bugs or feature requests

Submit a pull request with improvements

Suggest new tool integrations or evaluation strategies

License

This project is licensed under the MIT License.
You are free to use, modify, and distribute this project with attribution.

Author & Contact

Ayush Tyagi
B.Tech Computer Science
AI Engineering | Agentic AI | Full-Stack Development

LinkedIn: https://www.linkedin.com/in/ayush-tyagi-0a3694267

Email: tyagiayush239@gmail.com
