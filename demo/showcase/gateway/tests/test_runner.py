from __future__ import annotations

import pytest

from showcase_gateway.runner import DockerRunner, RunnerError

from .conftest import make_settings


@pytest.mark.parametrize("servers", [(), ("1.1.1.1",), ("1.1.1.1", "9.9.9.9")])
async def test_kept_containers_use_configured_dns_servers(monkeypatch, servers):
    monkeypatch.setenv("WEB_DNS_SERVERS", ",".join(servers))
    runner = DockerRunner(make_settings())
    commands = []

    async def docker(*args, **kwargs):
        commands.append(args)
        if "{{.Id}}" in args:
            raise RunnerError("No such container")
        return "10.0.1.2"

    monkeypatch.setattr(runner, "_docker", docker)
    address = await runner.start_persistent(
        "nmw-test",
        {},
        volumes={"test-data": "/data"},
        network="web-net",
        memory="1g",
        cpus="1",
        pids=256,
        image="nanomuse:test",
    )

    command = next(cmd for cmd in commands if cmd[0] == "run")
    actual = tuple(command[i + 1] for i, arg in enumerate(command) if arg == "--dns")
    assert actual == servers
    assert address == "10.0.1.2" and command[-1] == "nanomuse:test"
