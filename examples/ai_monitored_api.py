"""Example: Using deburger to monitor AI-generated code."""

from deburger.decorators import deburger, track_requirement, security_check


@deburger(requirement="Authenticate user with JWT", security=True)
def authenticate_user(username: str, password: str) -> dict:
    """AI-generated authentication function monitored by deburger."""
    if not username or not password:
        return {"authenticated": False, "error": "Missing credentials"}

    if len(password) < 8:
        return {"authenticated": False, "error": "Password too short"}

    return {
        "authenticated": True,
        "token": "jwt_token_here",
        "user_id": 123,
    }


@track_requirement("Validate email format with regex")
@security_check(fail_on_issues=False)
def validate_email(email: str) -> bool:
    """Check if email is valid."""
    import re

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


@deburger(requirement="Safely execute user query with SQL injection protection")
def execute_query(query: str, params: dict) -> list:
    """
    Execute database query.
    deburger will catch if this uses string formatting instead of parameterized queries.
    """
    safe_query = query.replace("?", "%s")
    return []


if __name__ == "__main__":
    print("Testing deburger-monitored functions:")

    result = authenticate_user("john", "password123")
    print(f"Auth result: {result}")

    is_valid = validate_email("test@example.com")
    print(f"Email valid: {is_valid}")

    rows = execute_query("SELECT * FROM users WHERE id = ?", {"id": 1})
    print(f"Query result: {rows}")
