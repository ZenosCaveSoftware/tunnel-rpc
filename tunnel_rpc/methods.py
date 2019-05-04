# -*- coding: utf-8 -*-
"""RPC Methods available for Tunnel RPC.

    Includes any helper methods needed to run @method annotated rpc calls.

    The current calls are:

        * run:  run arbitrary commands on a docker bash instance
                with persistent state between commands.

"""
import os
import re
import tarfile
from io import BytesIO
from fnmatch import fnmatch
from base64 import b64decode, b64encode
from collections import defaultdict
from docker import APIClient


__all__ = ["run"]


def create_container(api_client):
    """Creates a basic REPL bash container in Docker.

    Args:
        api_client (ApiClient): the client to be used for container creation.

    Returns:
        (str) the container's id.

    """
    return api_client.create_container(
        image="zenoscave/tunnel-runner:latest", stdin_open=True
    )


def eval_commands(api_client, container, commands, source_base64=None):
    """Evaluates commands in a docker container.

    Keeps stdin open and runs commands on same environment.

    Args:
        api_client (APIClient): API interaction client for a Docker host
        container (str): Container's ID used to run the commands
        commands (List[str]): Commands to run
        source_base64 (str): The base64 contents of a tar archive (optional)

    Returns:
        (str) The stdout/stderr combined output

    """
    if source_base64:
        tar_stream = b64decode(source_base64)
        api_client.put_archive(container, path="/app/src", data=tar_stream)

    api_client.start(container)

    socket = api_client.attach_socket(
        container, params={"stdin": 1, "stream": 1}
    )
    file_descriptor = socket.fileno()

    for cmd in commands + ["exit"]:
        cmd = cmd.replace("\n", " ; ")
        cmd += "\n"
        os.write(file_descriptor, cmd.encode("utf-8"))
    socket.close()

    api_client.wait(container)

    return api_client.logs(container, stdout=True, stderr=True).decode()


def parse_output(output):
    """Store all terminal lines associated with the program run commands.

    Args:
        output(str): Container with pre-run commands in terminal

    Returns:
        (list) The contents of the terminal

    """
    commands = []
    for command_text in output.replace("\r\n", "\n").split("---\n"):
        command = defaultdict(list)
        for line in command_text.split("\n"):
            match = re.match(r"^\[([^\]]*)\] (.*)$", line)
            if bool(match):
                key, value = match.groups()
                command[key].append(value)
        if any(command):
            commands.append(dict(command))
    return commands


def retrieve_archive_base64(api_client, container, distribution_config):
    """Retrieves any artifacts for distribution from a container after running

    Args:
        api_client (APIClient): API interaction client for a Docker host
        container (str): Container's ID used to run the commands
        distribution_config (dict): The specified distribution config

    Returns:
        (str) base64 encoded tarball stream containing distribution artifacts

    """
    base_path = distribution_config.get("base_path", "")
    artifacts = distribution_config.get("artifacts", [])

    def _is_artifact(member):
        return any(fnmatch(member.name, artifact) for artifact in artifacts)

    if not artifacts:
        return None

    strm, _ = api_client.get_archive(
        container, os.path.join("/app/src", base_path)
    )

    members = []

    for obj in strm:
        tar_stream = tarfile.TarFile(fileobj=BytesIO(obj))
        members += [
            member
            for member in tar_stream.getmembers()
            if _is_artifact(member)
        ]

    out_obj = BytesIO()
    with tarfile.TarFile(
            "output.tgz", "w", fileobj=out_obj
    ) as out_stream:
        for member in members:
            out_stream.addfile(member)
    return b64encode(out_obj.getvalue())


def run(request=None):
    """Runs commands in a docker container and parses the log output.

    Args:
        request (dict): requested commands to run

    Returns:
        (list) parsed outputs

    """
    api_client = APIClient()
    container = create_container(api_client)
    source_base64 = request.get("source", None)
    commands = request.get("commands", [])
    lines = eval_commands(api_client, container, commands, source_base64)
    results = parse_output(lines)

    distribution = request.get("dist", {})
    output_tarball = retrieve_archive_base64(
        api_client, container, distribution
    )

    api_client.remove_container(container)
    return {"results": results, "output": output_tarball}
