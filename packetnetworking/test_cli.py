import copy
import re
import time
import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner
import pytest

from . import builder, cli, utils


default_args = ["--rootfs", "packet-networking-test"]
test_meta_interfaces = [
    {"name": "eth0", "mac": "00:0c:29:51:53:a1", "bond": "bond0"},
    {"name": "eth1", "mac": "00:0c:29:51:53:a2", "bond": "bond0"},
]
test_phys_interfaces = [
    {"name": "enp0", "mac": "00:0c:29:51:53:a1"},
    {"name": "enp1", "mac": "00:0c:29:51:53:a2"},
]
test_metadata = {
    "operating_system": {"slug": "centos_7", "distro": "centos", "version": "7"},
    "network": {"interfaces": test_meta_interfaces},
}
test_resolvers = ["1.1.1.1", "2.2.2.2"]


def assert_output(test, result):
    print("result.output:", result.output)
    if "output" in test:
        assert test["output"].search(result.output) is not None


@pytest.mark.parametrize(
    "test",
    [
        pytest.param(
            {
                "args": [],
                "exit_code": 2,
                "called_with": None,
                "output": re.compile(
                    """Missing option ['"]-t['"] / ['"]--rootfs['"]"""
                ),
            },
            id="rootfs required",
        ),
        pytest.param(
            {
                "args": ["--rootfs", "packet-networking-test"],
                "exit_code": 0,
                "called_with": (
                    None,  # metadata_file
                    "http://metadata.packet.net/metadata",  # metadata_url
                    None,  # operating_system
                    "packet-networking-test",  # rootfs
                    None,  # resolvers
                    0,  # verbose
                    False,  # quiet
                ),
            },
            id="rootfs: --rootfs",
        ),
        pytest.param(
            {
                "args": ["-t", "packet-networking-test"],
                "exit_code": 0,
                "called_with": (
                    None,  # metadata_file
                    "http://metadata.packet.net/metadata",  # metadata_url
                    None,  # operating_system
                    "packet-networking-test",  # rootfs
                    None,  # resolvers
                    0,  # verbose
                    False,  # quiet
                ),
            },
            id="rootfs: -t",
        ),
        pytest.param(
            {
                "args": default_args,
                "exit_code": 0,
                "called_with": (
                    None,  # metadata_file
                    "http://metadata.packet.net/metadata",  # metadata_url
                    None,  # operating_system
                    "packet-networking-test",  # rootfs
                    None,  # resolvers
                    0,  # verbose
                    False,  # quiet
                ),
            },
            id="--metadata-url/file undefined",
        ),
        pytest.param(
            {
                "args": default_args + ["--metadata-url", "http://localhost/metadata"],
                "exit_code": 0,
                "called_with": (
                    None,  # metadata_file
                    "http://localhost/metadata",  # metadata_url
                    None,  # operating_system
                    "packet-networking-test",  # rootfs
                    None,  # resolvers
                    0,  # verbose
                    False,  # quiet
                ),
            },
            id="--metadata-url defined",
        ),
        pytest.param(
            {
                "args": default_args + ["--metadata-file", "metadata.json"],
                "exit_code": 0,
                "called_with": (
                    "metadata.json",  # metadata_file
                    "http://metadata.packet.net/metadata",  # metadata_url
                    None,  # operating_system
                    "packet-networking-test",  # rootfs
                    None,  # resolvers
                    0,  # verbose
                    False,  # quiet
                ),
            },
            id="--metadata-file defined",
        ),
        pytest.param(
            {
                "args": default_args + ["--operating-system", "test version"],
                "exit_code": 0,
                "called_with": (
                    None,  # metadata_file
                    "http://metadata.packet.net/metadata",  # metadata_url
                    "test version",  # operating_system
                    "packet-networking-test",  # rootfs
                    None,  # resolvers
                    0,  # verbose
                    False,  # quiet
                ),
            },
            id="Operating System: --operating-system",
        ),
        pytest.param(
            {
                "args": default_args + ["-o", "test version"],
                "exit_code": 0,
                "called_with": (
                    None,  # metadata_file
                    "http://metadata.packet.net/metadata",  # metadata_url
                    "test version",  # operating_system
                    "packet-networking-test",  # rootfs
                    None,  # resolvers
                    0,  # verbose
                    False,  # quiet
                ),
            },
            id="Operating System: -o",
        ),
        pytest.param(
            {
                "args": default_args + ["--resolvers", "1.2.3.4,2.3.4.5"],
                "exit_code": 0,
                "called_with": (
                    None,  # metadata_file
                    "http://metadata.packet.net/metadata",  # metadata_url
                    None,  # operating_system
                    "packet-networking-test",  # rootfs
                    "1.2.3.4,2.3.4.5",  # resolvers
                    0,  # verbose
                    False,  # quiet
                ),
            },
            id="--resolvers defined",
        ),
        pytest.param(
            {
                "args": default_args + ["-v"],
                "exit_code": 0,
                "called_with": (
                    None,  # metadata_file
                    "http://metadata.packet.net/metadata",  # metadata_url
                    None,  # operating_system
                    "packet-networking-test",  # rootfs
                    None,  # resolvers
                    1,  # verbose
                    False,  # quiet
                ),
            },
            id="verbose level 1 (INFO): -v",
        ),
        pytest.param(
            {
                "args": default_args + ["-vv"],
                "exit_code": 0,
                "called_with": (
                    None,  # metadata_file
                    "http://metadata.packet.net/metadata",  # metadata_url
                    None,  # operating_system
                    "packet-networking-test",  # rootfs
                    None,  # resolvers
                    2,  # verbose
                    False,  # quiet
                ),
            },
            id="verbose level 2 (DEBUG): -v",
        ),
        pytest.param(
            {
                "args": default_args + ["-vvv"],
                "exit_code": 0,
                "called_with": (
                    None,  # metadata_file
                    "http://metadata.packet.net/metadata",  # metadata_url
                    None,  # operating_system
                    "packet-networking-test",  # rootfs
                    None,  # resolvers
                    3,  # verbose
                    False,  # quiet
                ),
            },
            id="verbose level 3+ (DEBUG): -v",
        ),
        pytest.param(
            {
                "args": default_args + ["--verbose"],
                "exit_code": 0,
                "called_with": (
                    None,  # metadata_file
                    "http://metadata.packet.net/metadata",  # metadata_url
                    None,  # operating_system
                    "packet-networking-test",  # rootfs
                    None,  # resolvers
                    1,  # verbose
                    False,  # quiet
                ),
            },
            id="verbose level 1 (INFO): --verbose",
        ),
        pytest.param(
            {
                "args": default_args + ["--verbose", "--verbose"],
                "exit_code": 0,
                "called_with": (
                    None,  # metadata_file
                    "http://metadata.packet.net/metadata",  # metadata_url
                    None,  # operating_system
                    "packet-networking-test",  # rootfs
                    None,  # resolvers
                    2,  # verbose
                    False,  # quiet
                ),
            },
            id="verbose level 2 (DEBUG): --verbose",
        ),
        pytest.param(
            {
                "args": default_args + ["--verbose", "--verbose", "--verbose"],
                "exit_code": 0,
                "called_with": (
                    None,  # metadata_file
                    "http://metadata.packet.net/metadata",  # metadata_url
                    None,  # operating_system
                    "packet-networking-test",  # rootfs
                    None,  # resolvers
                    3,  # verbose
                    False,  # quiet
                ),
            },
            id="verbose level 3+ (DEBUG): --verbose",
        ),
        pytest.param(
            {
                "args": default_args + ["--quiet"],
                "exit_code": 0,
                "called_with": (
                    None,  # metadata_file
                    "http://metadata.packet.net/metadata",  # metadata_url
                    None,  # operating_system
                    "packet-networking-test",  # rootfs
                    None,  # resolvers
                    0,  # verbose
                    True,  # quiet
                ),
            },
            id="quiet long option (--quiet)",
        ),
        pytest.param(
            {
                "args": default_args + ["-q"],
                "exit_code": 0,
                "called_with": (
                    None,  # metadata_file
                    "http://metadata.packet.net/metadata",  # metadata_url
                    None,  # operating_system
                    "packet-networking-test",  # rootfs
                    None,  # resolvers
                    0,  # verbose
                    True,  # quiet
                ),
            },
            id="quiet short option (-q)",
        ),
    ],
)
def test_cli(test, mockit):
    runner = CliRunner()
    with runner.isolated_filesystem(), mockit(cli.try_run) as mocked_try_run:
        if test["called_with"] and test["called_with"][0]:
            # metadata_file is populated, lets write it
            with open(test["called_with"][0], "w") as f:
                f.write("{}")

        result = runner.invoke(cli.cli, test["args"])

    assert_output(test, result)
    assert result.exit_code == test["exit_code"]
    if not test.get("called_with"):
        mocked_try_run.assert_not_called()
    else:
        if test["called_with"][0]:
            assert mocked_try_run.call_args_list[0].args[1:] == test["called_with"][1:]
        else:
            mocked_try_run.assert_called_with(*test["called_with"])


@pytest.mark.parametrize(
    "opt,n,runs,sleep",
    [
        pytest.param(
            "--max-attempts", 2, 2, 4, id="Max Attempts long option (--max-attempts)"
        ),
        pytest.param("-n", 2, 2, 4, id="Max Attempts short option (-n)"),
        pytest.param("--max-attempts", -1, 1, None, id="Attempt -1: no sleep"),
        pytest.param("--max-attempts", 0, 1, None, id="Attempt 0: no sleep"),
        pytest.param("--max-attempts", 1, 1, None, id="Attempt 1: no sleep"),
        pytest.param("--max-attempts", 2, 2, 4, id="Attempt 2: sleep 4 seconds"),
        pytest.param("--max-attempts", 7, 7, 128, id="Attempt 7: sleep 128 seconds"),
        pytest.param("--max-attempts", 8, 8, 128, id="Attempt 8: sleep 128 seconds"),
    ],
)
def test_cli_retries_on_exception(opt, n, runs, sleep, mockit):
    runner = CliRunner()
    # fmt: off
    with runner.isolated_filesystem(), \
            mockit(cli.try_run) as mocked_try_run, \
            patch("packetnetworking.cli.log") as mocked_log, \
            mockit(time.sleep) as mocked_time_sleep:
        mocked_try_run.side_effect = Exception("fail")
        result = runner.invoke(cli.cli, default_args + [opt, str(n)])
    # fmt: on

    # try_run is executed for every attempt.
    assert mocked_try_run.call_count == runs
    # log and sleep are executed on every exception excluding the last
    assert mocked_log.error.call_count == runs - 1
    assert mocked_time_sleep.call_count == runs - 1
    if sleep is not None:
        mocked_time_sleep.assert_called_with(sleep)

    # Exception raised, therefore bad exit code
    assert result.exit_code != 0


def test_try_run_with_url(mockit, metadata):
    # fmt: off
    with patch("requests.get") as mocked_requests_get, \
            mockit(utils.get_interfaces, return_value=test_phys_interfaces), \
            patch.object(builder.Builder, "run", return_value=True):
        mocked_requests_get.return_value.status_code = 200
        mocked_requests_get.return_value.json = MagicMock(
            return_value=metadata(test_metadata)
        )
        cli.try_run(
            None,
            "http://localhost/metadata",
            None,
            "/tmp/packet-networking-test",
            None,
            None,
            None,
        )
    # fmt: on

    assert mocked_requests_get.call_count == 1
    mocked_requests_get.assert_called_with("http://localhost/metadata")


def test_try_run_with_file(mockit, metadata):
    md = metadata(test_metadata)
    # fmt: off
    with mockit(json.load) as mocked_json_load, \
            mockit(utils.get_interfaces, return_value=test_phys_interfaces), \
            patch.object(builder.Builder, "load_metadata") as mocked_builder_load_metadata, \
            patch.object(builder.Builder, "run", return_value=True):
        mocked_json_load.return_value = md
        cli.try_run(
            "i'm a file handler",
            "http://localhost/metadata",
            None,
            "/tmp/packet-networking-test",
            None,
            None,
            None,
        )
    # fmt: on

    mocked_builder_load_metadata.assert_not_called()
    assert mocked_json_load.call_count == 1
    mocked_json_load.assert_called_with("i'm a file handler")


@pytest.mark.parametrize(
    "md_file,md_url,expected",
    [
        pytest.param(None, "http://url", (False, True), id="URL"),
        pytest.param("file", None, (True, False), id="File"),
        pytest.param("file", "http://url", (True, False), id="File+URL"),
    ],
)
def test_setup_builder(md_file, md_url, expected, mockit, metadata):
    # fmt: off
    with mockit(json.load) as mocked_json_load, \
            patch.object(builder.Builder, "set_metadata") as set_metadata, \
            patch.object(builder.Builder, "load_metadata") as load_metadata:
        cli.setup_builder(md_file, md_url)
    # fmt: on

    expect_set, expect_load = expected
    assert set_metadata.called == expect_set
    assert load_metadata.called == expect_load
    if md_file is not None:
        mocked_json_load.assert_called_with(md_file)


@pytest.mark.parametrize(
    "md_os,os,expected",
    [
        pytest.param(True, None, ("distro", "version", False, False), id="None"),
        pytest.param(True, "", ("distro", "version", False, False), id="Empty"),
        pytest.param(False, "nospace", (None, None, True, False), id="No Space"),
        pytest.param(
            False, "too many spaces", (None, None, True, False), id="Too Many Spaces"
        ),
        pytest.param(
            True, "distro version", ("distro", "version", False, False), id="Matches"
        ),
        pytest.param(
            False,
            "distro version",
            ("distro", "version", False, True),
            id="Diff: Missing",
        ),
        pytest.param(
            True,
            "Distro version",
            ("distro", "version", False, False),
            id="Diff: Distro Case",
        ),
        pytest.param(
            True,
            "distro Version",
            ("distro", "version", False, False),
            id="Diff: Version Case",
        ),
    ],
)
def test_set_os(md_os, os, expected, mockit, metadata):
    tmd = copy.deepcopy(test_metadata)
    orig_distro = "distro"
    orig_version = "version"
    if not md_os:
        orig_distro = None
        orig_version = None

    tmd["operating_system"]["distro"] = orig_distro
    tmd["operating_system"]["version"] = orig_version
    b = builder.Builder()
    b.set_metadata(metadata(tmd))
    e_distro, e_version, e_empty, e_mismatch = expected
    with patch("packetnetworking.cli.log") as mocked_log:
        if e_empty:
            with pytest.raises(SystemExit):
                cli.set_os(b, os, False)
        else:
            cli.set_os(b, os, False)

    if e_mismatch:
        assert mocked_log.debug.call_count == 1
    else:
        mocked_log.debug.assert_not_called()

    assert b.metadata.operating_system.distro == e_distro
    assert b.metadata.operating_system.version == e_version

    if e_mismatch:
        assert b.metadata.operating_system.orig_distro == orig_distro
        assert b.metadata.operating_system.orig_version == orig_version


@pytest.mark.parametrize(
    "md_resolvers,resolvers,expected",
    [
        pytest.param(True, None, test_resolvers, id="None (With metadata)"),
        pytest.param(True, "", test_resolvers, id="Empty (With metadata)"),
        pytest.param(False, None, None, id="None (Without metadata"),
        pytest.param(False, "", None, id="Empty (Without metadata"),
        pytest.param(True, "1.2.3.4", ["1.2.3.4"], id="Single Resolver"),
        pytest.param(
            True, "1.2.3.4,2.3.4.5", ["1.2.3.4", "2.3.4.5"], id="Multiple Resolvers"
        ),
        pytest.param(
            True,
            ",,1.2.3.4,,,2.3.4.5,,",
            ["1.2.3.4", "2.3.4.5"],
            id="Multiple Resolvers with extra commas",
        ),
    ],
)
def test_set_resolvers(md_resolvers, resolvers, expected, metadata):
    b = builder.Builder()
    if md_resolvers:
        b.network.resolvers = test_resolvers

    cli.set_resolvers(b, resolvers)

    assert b.network.resolvers == expected
