import os
import subprocess
import time
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent / "payments_service" / ".env")

@pytest.fixture(scope="session")
def docker_compose_file():
    """Returns the absolute path to the docker-compose.yml file."""
    # Adjusted to point to the root of the project
    path = Path(__file__).parent.parent.parent.parent / "docker-compose.yml"
    return str(path.absolute())

def wait_for_service(check_command, timeout=30):
    """Wait for a service to become responsive."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            result = subprocess.run(check_command, capture_output=True, text=True)
            if result.returncode == 0:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

@pytest.fixture(scope="session")
def docker_services(docker_compose_file):
    """
    Manages the lifecycle of Docker services for the entire test session.
    """
    print("\n[Docker] Starting services...")
    try:
        # Using 'docker compose' as it's the modern standard, fallback to 'docker-compose' if needed
        cmd = ["docker", "compose"]
        try:
            subprocess.run(cmd + ["version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            cmd = ["docker-compose"]

        subprocess.run(cmd + ["-f", docker_compose_file, "up", "-d", "--build"], check=True)
        
        print("[Docker] Waiting for Postgres (db) to be ready...")
        if not wait_for_service(cmd + ["-f", docker_compose_file, "exec", "-T", "db", "pg_isready", "-U", "postgres"]):
            pytest.fail("Postgres service timed out")

        print("[Docker] Waiting for Redis (cache) to be ready...")
        if not wait_for_service(cmd + ["-f", docker_compose_file, "exec", "-T", "cache", "redis-cli", "ping"]):
            pytest.fail("Redis service timed out")

        print("[Docker] All services are up and healthy!")
        
        # Set environment variables for the tests
        os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/payments"
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"

    except subprocess.CalledProcessError as e:
        pytest.fail(f"Failed to manage Docker services: {e.stderr}")

    yield

    print("\n[Docker] Tearing down services...")
    subprocess.run(cmd + ["-f", docker_compose_file, "down", "-v"], check=False)
