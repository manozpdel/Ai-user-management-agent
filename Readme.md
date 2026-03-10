# AI User Management System

An AI-powered user management system built with LangGraph, FastAPI, PostgreSQL, and Streamlit. The system allows you to manage users through natural language conversation.

---

## Tech Stack

- **LangGraph** — AI agent framework with custom graph nodes and edges
- **FastAPI** — REST API backend
- **PostgreSQL** — Database (hosted on Supabase)
- **Streamlit** — Chat UI
- **Groq** — LLM provider (llama-3.3-70b-versatile)
- **Docker** — Containerization

---

## Features

- Create, read, update, and delete users through natural language
- Agent collects required fields one by one before creating a user
- Asks for confirmation before deleting a user
- Conversation memory saved to PostgreSQL — chat history persists across restarts
- Previous conversations listed in the sidebar and can be reloaded
- Full chat history saved per session

---

## Project Structure

```
├── main.py          # FastAPI app with /chat endpoint
├── agent.py         # LangGraph graph with nodes, edges, and memory
├── tools.py         # CRUD tools connected to the agent
├── database.py      # PostgreSQL connection and users table setup
├── app.py           # Streamlit chat UI
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/manozpdel/Ai-user-management-agent.git
cd your-repo-name
```

### 2. Set up environment variables

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://your-user:your-password@your-host:5432/postgres
GROQ_API_KEY=your_groq_api_key
```

- Get a free PostgreSQL database at [neon.tech](https://neon.tech) or [supabase.com](https://supabase.com)
- Get a free Groq API key at [console.groq.com](https://console.groq.com)

### 3. Run with Docker

```bash
docker-compose up --build
```

- Streamlit UI: [http://localhost:8501](http://localhost:8501)
- FastAPI docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Run without Docker (local development)

```bash
pip install -r requirements.txt

# Terminal 1 — start FastAPI
uvicorn main:app --reload

# Terminal 2 — start Streamlit
streamlit run app.py
```

---

## Agent Graph

The LangGraph agent uses a custom graph with two nodes connected by conditional edges:

![Agent Graph](Images/graph.png)

- **agent node** — LLM reads the conversation and decides whether to call a tool or reply directly
- **tools node** — executes the selected CRUD tool and returns the result back to the agent
- **tools_condition** — routes to tools node if a tool call is detected, otherwise ends

---

## Screenshots
### Our UI with Conversation Memory
![UI](Images/Add%20user.png)


### Agent collecting user details step by step
![Add User](Images/Add%20user.png)

### Updated User details
![Updated](Images/update.png)

### Delete confirmation
![Delete Confirmation](Images/delete%20user.png)

### Listing all users
![List Users](Images/list%20users.png)

---

