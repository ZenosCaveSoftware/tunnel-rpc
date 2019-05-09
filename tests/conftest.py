# -*- coding: utf-8 -*-
"""Pytest Fixtures for Tunnel RPC.

"""
import pytest


@pytest.fixture()
def docker_client():
    """Provides a docker-api client.

    """
    import docker

    return docker.APIClient()


@pytest.fixture()
# pragma pylint: disable=redefined-outer-name
def container_factory(docker_client):
    """Provides a container creation factory.

    Assumes The tunnel_rpc create_container works properly.

    """
    from tunnel_rpc.methods import create_container

    return lambda: create_container(docker_client)


@pytest.fixture()
def tarball64_factory():
    """Provides a factor for creating base64 encoded contents of a tarball.

    """

    def tarball_(input_dir):
        """Creates a base64 encoded tarball fro input_dir.

        Args:
            input_dir (dict): The tree structure of the files.
                              keys represent filenames,
                              and values represent contents.

        Returns:
            (str) a tarball encoded in base64 for the input_dir.

        """
        import tarfile
        import time
        from contextlib import closing
        from io import BytesIO
        from base64 import b64encode

        tar_stream = BytesIO()
        with tarfile.open(mode="w:gz", fileobj=tar_stream) as tar:
            for filename, content in input_dir.items():
                byte_str = content.encode()
                with closing(BytesIO(byte_str)) as file_obj:
                    tarinfo = tarfile.TarInfo(filename)
                    tarinfo.size = len(byte_str)
                    tarinfo.mtime = time.time()
                    tar.addfile(tarinfo, fileobj=file_obj)
        tar_stream.seek(0)
        return b64encode(tar_stream.getvalue())

    return tarball_
