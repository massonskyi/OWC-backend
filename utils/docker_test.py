import os
import docker
from docker.errors import NotFound
from fastapi import HTTPException
from typing import Optional # noqa: F401
client = docker.from_env()

def create_container(workspace_id: int, project_id: int, language: str):
    container_name = f"workspace_{workspace_id}_project_{project_id}"
    image_name = "mcr.microsoft.com/dotnet/sdk:latest" if language == "csharp" else f"{language}:latest"

    # Construct the absolute path for the volume
    volume_path = os.path.abspath(f"./{workspace_id}/project/{project_id}")

    # Ensure the directory exists
    if not os.path.exists(volume_path):
        os.makedirs(volume_path)

    try:
        container = client.containers.run(
            image_name,
            name=container_name,
            detach=True,
            tty=True,
            stdin_open=True,
            volumes={volume_path: {'bind': '/workspace', 'mode': 'rw'}}
        )
        return container.id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def stop_container(container_id: str):
    try:
        container = client.containers.get(container_id)
        container.stop()
    except NotFound:
        raise HTTPException(status_code=404, detail="Container not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def remove_container(container_id: str):
    try:
        container = client.containers.get(container_id)
        container.remove(force=True)
    except NotFound:
        raise HTTPException(status_code=404, detail="Container not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def execute_command_in_container(container_id: str, command: str):
    try:
        container = client.containers.get(container_id)
        exit_code, output = container.exec_run(command)
        if exit_code != 0:
            raise HTTPException(status_code=500, detail=f"Command failed with exit code {exit_code}: {output.decode('utf-8')}")
        return output.decode('utf-8')
    except NotFound:
        raise HTTPException(status_code=404, detail="Container not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def create_project_in_container(container_id: str, project_name: str, language: str):
    try:
        container = client.containers.get(container_id)
        if language == "csharp":
            command = f"dotnet new console -n {project_name} -o /workspace/{project_name}"
        elif language == "python":
            command = f"python -m venv /workspace/{project_name} && cd /workspace/{project_name} && pip install -r requirements.txt"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")

        exit_code, output = container.exec_run(command)
        if exit_code != 0:
            raise HTTPException(status_code=500, detail=f"Command failed with exit code {exit_code}: {output.decode('utf-8')}")
        return output.decode('utf-8')
    except NotFound:
        raise HTTPException(status_code=404, detail="Container not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Пример использования
if __name__ == "__main__":
    container_id = create_container(1, 1, "csharp")
    print(f"Created container with ID: {container_id}")

    output = execute_command_in_container(container_id, "ls -la")
    print(f"Command output: {output}")

    project_output = create_project_in_container(container_id, "MyProject", "csharp")
    print(f"Project creation output: {project_output}")

    stop_container(container_id)
    remove_container(container_id)
