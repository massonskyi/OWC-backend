import docker
from docker.errors import NotFound
from typing import Optional # noqa: F401

from fastapi import HTTPException

client = docker.from_env()

def create_container(workspace_id: int, project_id: int, language: str):
    container_name = f"workspace_{workspace_id}_project_{project_id}"
    try:
        container = client.containers.run(
            f"{language}:latest",
            name=container_name,
            detach=True,
            tty=True,
            stdin_open=True,
            volumes={f"/path/to/workspace/{workspace_id}/project/{project_id}": {'bind': '/workspace', 'mode': 'rw'}}
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
