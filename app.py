import streamlit as st
import requests
import uuid
import os
from dotenv import load_dotenv
from psycopg2 import pool

load_dotenv()

FASTAPI_URL = "http://fastapi:8000/chat"

st.set_page_config(
    page_title="User Management Assistant",
    layout="centered",
)

st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            font-size: 0.8rem;
        }
        section[data-testid="stSidebar"] button p {
            font-size: 0.8rem;
        }
        section[data-testid="stSidebar"] .stAlert p {
            font-size: 0.8rem;
        }
    </style>
""", unsafe_allow_html=True)

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_name" not in st.session_state:
    st.session_state.session_name = None


@st.cache_resource
def init_db():
    """Create connection pool and tables once for the lifetime of the app."""
    connection_pool = pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        dsn=os.getenv("DATABASE_URL"),
    )

    conn = connection_pool.getconn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            thread_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            id SERIAL PRIMARY KEY,
            thread_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cursor.close()
    connection_pool.putconn(conn)

    return connection_pool


def get_conn():
    return init_db().getconn()


def put_conn(conn):
    init_db().putconn(conn)


def save_session(thread_id, name):
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_sessions (thread_id, name)
            VALUES (%s, %s)
            ON CONFLICT (thread_id) DO NOTHING
        """, (thread_id, name))
        conn.commit()
        cursor.close()
    except Exception as e:
        print("Save session error:", e)
    finally:
        put_conn(conn)


def save_message(thread_id, role, content):
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_messages (thread_id, role, content)
            VALUES (%s, %s, %s)
        """, (thread_id, role, content))
        conn.commit()
        cursor.close()
    except Exception as e:
        print("Save message error:", e)
    finally:
        put_conn(conn)


@st.cache_data(ttl=60)
def get_all_sessions():
    """Fetch sessions from DB, cached for 60 seconds to avoid re-fetching every render."""
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT thread_id, name FROM chat_sessions
            ORDER BY created_at DESC
            LIMIT 6
        """)
        rows = cursor.fetchall()
        cursor.close()
        return [{"thread_id": r[0], "name": r[1]} for r in rows]
    except Exception:
        return []
    finally:
        put_conn(conn)


def load_messages(thread_id):
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content FROM chat_messages
            WHERE thread_id = %s
            ORDER BY created_at ASC
        """, (thread_id,))
        rows = cursor.fetchall()
        cursor.close()
        return [{"role": r[0], "content": r[1]} for r in rows]
    except Exception:
        return []
    finally:
        put_conn(conn)


# Initialize DB once
init_db()

# Sidebar
with st.sidebar:
    if st.button("New Chat", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.session_name = None

    sessions = get_all_sessions()
    if sessions:
        st.caption("Previous chats")
        for session in sessions:
            is_active = session["thread_id"] == st.session_state.thread_id
            if is_active:
                st.button(
                    session["name"],
                    key=f"sess_{session['thread_id']}",
                    use_container_width=True,
                    type="primary",
                )
            else:
                if st.button(
                    session["name"],
                    key=f"sess_{session['thread_id']}",
                    use_container_width=True,
                ):
                    st.session_state.thread_id = session["thread_id"]
                    st.session_state.session_name = session["name"]
                    st.session_state.messages = load_messages(session["thread_id"])

    st.divider()
    st.caption("What can I do?")
    st.info("""
**Add a user**
Say "add a new user" and I will ask for their name, email, phone, and location one by one.

**Find a user**
Say "find user with email john@example.com" or provide a user ID.

**List users**
Say "show all users" or filter by saying "show all users from Kathmandu" or "show all engineers".

**Update a user**
Say "update user" and provide the user ID along with the fields you want to change.

**Delete a user**
Say "delete user" and provide the user ID. I will ask for confirmation before deleting.
    """)

# Main area
st.title("User Management Assistant")
st.caption("Talk to the AI to create, search, update or delete users.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("Type a message...")

if user_input and user_input.strip():
    message = user_input.strip()

    if st.session_state.session_name is None:
        name = message[:35]
        st.session_state.session_name = name
        save_session(st.session_state.thread_id, name)
        get_all_sessions.clear()

    save_message(st.session_state.thread_id, "user", message)
    st.session_state.messages.append({"role": "user", "content": message})

    with st.spinner("Thinking..."):
        try:
            res = requests.post(
                FASTAPI_URL,
                json={
                    "message": message,
                    "thread_id": st.session_state.thread_id,
                },
                timeout=60,
            )
            res.raise_for_status()
            reply = res.json()["response"]
        except requests.exceptions.ConnectionError:
            reply = "Could not connect to the backend. Make sure the FastAPI server is running."
        except Exception as e:
            reply = f"Something went wrong: {str(e)}"

    save_message(st.session_state.thread_id, "assistant", reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()