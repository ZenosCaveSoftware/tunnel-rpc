# -*- coding: utf-8 -*-
"""Tests for Tunnel RPC methods.

"""
from json.decoder import JSONObject

from tunnel_rpc.methods import eval_commands, parse_output, run, archiver, create_container
from docker import APIClient


def test_eval_commands(
        docker_api_client, tunnel_container_factory, tarball64_factory
):
    """Tests the command evaluation method.

    eval_commands should return a string
    eval_commands logs should contain both stderr and stdout
    eval_commands should extract tarballs correctly for the container

    """
    ls_container = tunnel_container_factory()
    ls_logs = eval_commands(docker_api_client, ls_container, ["ls"])
    assert isinstance(ls_logs, str), "eval_commands should return a string"

    stdout_container = tunnel_container_factory()
    stdout_logs = eval_commands(
        docker_api_client, stdout_container, ["echo 43"]
    )
    assert "43" in stdout_logs, "eval_commands should contain stdout"

    stderr_container = tunnel_container_factory()
    stderr_logs = eval_commands(
        docker_api_client, stderr_container, ["echo 43 1>&2"]
    )
    assert "43" in stderr_logs, "eval_commands should contain stderr"

    tarball_base64 = tarball64_factory({"test_file.txt": "43"})
    tarball_container = tunnel_container_factory()
    tarball_logs = eval_commands(
        docker_api_client,
        tarball_container,
        ["ls test_file.txt"],
        source_base64=tarball_base64,
    )
    assert (
        "test_file.txt" in tarball_logs
    ), "eval_commands should extract tarballs correctly for the container"


def test_parse_output():
    """Test the parse output method.

    parse_output should return a list of dicts
    parse_output should ignore preambles
    parse_output should append every command log

    """

    response = parse_output("---\n[TEST] test\n")
    assert isinstance(response, list), "parse_output should return a list"
    assert isinstance(
        response[0], dict
    ), "parse_output should return a list of dicts"

    response = parse_output("should not show up---\n[COMMAND] ls\n")
    assert all(
        "should not show up" not in output
        for command in response
        for _, output in command.items()
    ), "parse_output should ignore preambles"

    for length in range(2, 10):
        output = "---\n[TEST] test\n" * length
        response = parse_output(output)
        assert (
            len(response) == length
        ), "parse_output should append every command log"


def test_run():
    """Test the run method.

    run should not raise errors

    """
    try:
        run({"commands": ["ls"]})
        run({"commands": ["ls"], "foo": "bar"})
        run({"foo": "bar"})
        run({"commands": ["false"]})
        run({"commands": []})
    except Exception as err:  # pylint: disable=broad-except
        assert False, str(err)


def test_archiver():
    api_client = APIClient()
    container = create_container(api_client())
    info = archiver(api_client, container)
    assert info.has("name"), "Archived data lacks name"
