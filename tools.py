from langchain_core.tools import tool
from psycopg2.extras import RealDictCursor
from database import get_connection


@tool
def create_user(
    name: str,
    email: str,
    phone_number: str = None,
    location: str = None,
    age: int = None,
    profession: str = None,
) -> str:
    """Create a new user. Required: name and email."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Check if a user with the same email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return f"A user with email {email} already exists."

        # Insert new user into the database
        cursor.execute(
            """
            INSERT INTO users (name, email, phone_number, location, age, profession)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (name, email, phone_number, location, age, profession),
        )
        user = dict(cursor.fetchone())
        conn.commit()
        return f"User created successfully. Details: {user}"

    except Exception as e:
        conn.rollback()
        return f"Error creating user: {str(e)}"

    finally:
        cursor.close()
        conn.close()


@tool
def get_user(user_id: str = None, email: str = None) -> str:
    """Fetch a user by user_id or email. Must provide at least one."""
    if user_id in (None, "null", ""):
        user_id = None
    if email in (None, "null", ""):
        email = None
    if not user_id and not email:
        return "Please provide either a user_id or an email address."

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        if user_id:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        else:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))

        user = cursor.fetchone()
        if not user:
            return "No user found."

        return f"User found: {dict(user)}"

    except Exception as e:
        return f"Error fetching user: {str(e)}"

    finally:
        cursor.close()
        conn.close()


@tool
def list_users(location: str = None, profession: str = None) -> str:
    """List all users, optionally filtering by location or profession."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        query = "SELECT * FROM users WHERE 1=1"
        params = []

        if location:
            query += " AND location ILIKE %s"
            params.append(f"%{location}%")
        if profession:
            query += " AND profession ILIKE %s"
            params.append(f"%{profession}%")

        cursor.execute(query, params)
        users = cursor.fetchall()
        if not users:
            return "No users found."

        return f"Found {len(users)} user(s): {[dict(u) for u in users]}"

    except Exception as e:
        return f"Error listing users: {str(e)}"

    finally:
        cursor.close()
        conn.close()


@tool
def update_user(
    user_id: str,
    name: str = None,
    email: str = None,
    phone_number: str = None,
    location: str = None,
    age: int = None,
    profession: str = None,
) -> str:
    """Update an existing user. Only provide fields to change."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Ensure user exists
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            return f"No user found with ID {user_id}."

        # Build dynamic update query
        fields = []
        values = []

        if name:
            fields.append("name = %s")
            values.append(name)
        if email:
            fields.append("email = %s")
            values.append(email)
        if phone_number:
            fields.append("phone_number = %s")
            values.append(phone_number)
        if location:
            fields.append("location = %s")
            values.append(location)
        if age is not None:
            fields.append("age = %s")
            values.append(age)
        if profession:
            fields.append("profession = %s")
            values.append(profession)

        if not fields:
            return "No fields were provided to update."

        values.append(user_id)
        query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s RETURNING *"

        cursor.execute(query, values)
        updated = dict(cursor.fetchone())
        conn.commit()

        return f"User updated successfully. Updated details: {updated}"

    except Exception as e:
        conn.rollback()
        return f"Error updating user: {str(e)}"

    finally:
        cursor.close()
        conn.close()


@tool
def delete_user(user_id: str) -> str:
    """Delete a user by their user_id."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return f"No user found with ID {user_id}."

        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()

        return f"User {user['name']} ({user['email']}) has been deleted."

    except Exception as e:
        conn.rollback()
        return f"Error deleting user: {str(e)}"

    finally:
        cursor.close()
        conn.close()