from .builder import Builder
from .metadata import Metadata
from . import utils
import mock
import pytest


@pytest.fixture
def fake_metadata(mockit, fake, metadata, patch_dict):
    gen_metadata = metadata

    def func(metadata=None, public=None):
        meta_interfaces = [
            {"name": "eth0", "mac": "00:0c:29:51:53:a1", "bond": "bond0"},
            {"name": "eth1", "mac": "00:0c:29:51:53:a2", "bond": "bond0"},
        ]
        _metadata = {"network": {"interfaces": meta_interfaces}}
        if metadata:
            patch_dict(_metadata, metadata)
        return gen_metadata(_metadata, public=public)

    return func


def test_builder_sets_metadata(fake_metadata):
    builder = Builder(fake_metadata())
    assert isinstance(builder.metadata, Metadata)


def test_builder_loading_metadata_from_url(fake_metadata):
    builder = Builder()
    with mock.patch("requests.get") as mocked_request_get:
        mocked_request_get.return_value.status_code = 200
        mocked_request_get.return_value.json = mock.MagicMock(
            return_value=fake_metadata()
        )
        builder.load_metadata("http://metadata.example.com/metadata")
    mocked_request_get.return_value.raise_for_status.assert_called_once()
    mocked_request_get.return_value.json.assert_called_once()
    assert isinstance(builder.metadata, Metadata)
    assert builder.metadata != {}


def test_builder_initializes(mockit, fake_metadata):
    builder = Builder(fake_metadata())
    phys_interfaces = [
        {"name": "enp0", "mac": "00:0c:29:51:53:a1"},
        {"name": "enp1", "mac": "00:0c:29:51:53:a2"},
    ]
    with mockit(utils.get_interfaces, return_value=phys_interfaces) as mocked_ifaces:
        builder.initialize()

    mocked_ifaces.assert_called_once()
    assert builder.initialized is True


def test_builder_raises_exception_if_not_initialized(mockit, fake_metadata):
    builder = Builder()
    with pytest.raises(Exception):
        builder.run("/path/to/rootfs")


def test_builder_runs(mockit, fake_metadata):
    builder = Builder(fake_metadata())
    phys_interfaces = [
        {"name": "enp0", "mac": "00:0c:29:51:53:a1"},
        {"name": "enp1", "mac": "00:0c:29:51:53:a2"},
    ]
    with mockit(utils.get_interfaces, return_value=phys_interfaces):
        builder.initialize()

    class FakeDistroBuilder:
        def __init__(self, metadata):
            pass

        def build(self):
            pass

        def run(self, rootfs_path):
            return True

    with mock.patch.object(
        builder, "get_builder", return_value=FakeDistroBuilder
    ) as mocked_get_builder:
        builder.run("/path/to/rootfs")

    mocked_get_builder.assert_called_with(builder.metadata.operating_system.distro)
