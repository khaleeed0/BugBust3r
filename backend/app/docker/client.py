"""
Docker client for managing containers
"""
import docker
from typing import Optional, Tuple
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class DockerClient:
    """Docker client wrapper for running security tools"""
    
    def __init__(self):
        try:
            # Try to connect to Docker daemon
            self.client = docker.from_env()
            self.client.ping()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None
    
    def run_container(
        self,
        image: str,
        command: str,
        volumes: Optional[dict] = None,
        environment: Optional[dict] = None,
        remove: bool = True,
        network_mode: Optional[str] = None,
        tmpfs: Optional[dict] = None
    ) -> Tuple[str, str, int]:
        """
        Run a Docker container and capture output
        
        Args:
            image: Docker image name
            command: Command to run in container
            volumes: Volume mounts (optional)
            environment: Environment variables (optional)
            remove: Remove container after execution (default: True)
            network_mode: Network mode (e.g., 'host')
            tmpfs: Tmpfs mounts (optional) - dict mapping paths to tmpfs options
        
        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        if self.client is None:
            raise RuntimeError("Docker client not initialized")
        
        try:
            logger.info(f"Running container: {image} with command: {command}")
            
            # Prepare container run arguments
            run_kwargs = {
                "image": image,
                "command": command,
                "volumes": volumes or {},
                "environment": environment or {},
                "remove": remove,
                "detach": False,
                "stdout": True,
                "stderr": True
            }
            
            # Add optional parameters
            if network_mode:
                run_kwargs["network_mode"] = network_mode
            if tmpfs:
                run_kwargs["tmpfs"] = tmpfs
            
            # Run container and capture output
            result = self.client.containers.run(**run_kwargs)
            
            # Parse output - containers.run returns bytes
            if isinstance(result, bytes):
                output = result.decode('utf-8', errors='ignore')
                stdout = output
                stderr = ""
                exit_code = 0
            elif isinstance(result, str):
                stdout = result
                stderr = ""
                exit_code = 0
            else:
                stdout = str(result)
                stderr = ""
                exit_code = 0
            
            logger.info(f"Container {image} completed with exit code: {exit_code}")
            return stdout, stderr, exit_code
            
        except docker.errors.ContainerError as e:
            logger.error(f"Container error: {e}, exit_status: {e.exit_status}")
            # Try to get container logs
            try:
                if hasattr(e, 'container') and e.container:
                    logs = e.container.logs(stdout=True, stderr=True).decode('utf-8', errors='ignore')
                    # Split logs into stdout and stderr (Docker combines them)
                    stdout = logs
                    stderr = str(e)
                else:
                    stdout = str(e)
                    stderr = str(e)
            except Exception as log_error:
                logger.warning(f"Could not retrieve container logs: {log_error}")
                stdout = str(e)
                stderr = str(e)
            return stdout, stderr, e.exit_status if hasattr(e, 'exit_status') else 1
        
        except docker.errors.ImageNotFound:
            logger.error(f"Image not found: {image}")
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error running container: {e}")
            raise
    
    def image_exists(self, image: str) -> bool:
        """Check if a Docker image exists"""
        if self.client is None:
            return False
        try:
            self.client.images.get(image)
            return True
        except docker.errors.ImageNotFound:
            return False
    
    def pull_image(self, image: str):
        """Pull a Docker image"""
        if self.client is None:
            raise RuntimeError("Docker client not initialized")
        logger.info(f"Pulling image: {image}")
        self.client.images.pull(image)


# Global Docker client instance
docker_client = DockerClient()

