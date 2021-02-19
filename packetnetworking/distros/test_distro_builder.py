import mock
import pytest

from .distro_builder import DistroBuilder, get_distro_builder
from .. import utils
from ..builder import NetworkData


@pytest.fixture
def fake_distro_builder():
    def func(distros):
        class FakeDistroBuilder(DistroBuilder):
            pass

        FakeDistroBuilder.distros = distros

        return FakeDistroBuilder

    return func


@pytest.fixture
def fake_network_builder():
    class FakeNetworkBuilder:
        templates_base = "fake/distro/templates"
        tasks = None

        def __init__(self, metadata):
            pass

        def build(self):
            pass

        def run(self, rootfs_path):
            pass

    return FakeNetworkBuilder


@pytest.fixture
def fake_metadata(metadata):
    return metadata({"network": None})


@pytest.fixture
def fake_distro_builder_with_metadata(mockit, fake, metadata, patch_dict):
    gen_metadata = metadata

    def func(metadata=None, public=True):
        meta_interfaces = [
            {"name": "eth0", "mac": "00:0c:29:51:53:a1", "bond": "bond0"},
            {"name": "eth1", "mac": "00:0c:29:51:53:a2", "bond": "bond0"},
        ]
        phys_interfaces = [
            {"name": "enp0", "mac": "00:0c:29:51:53:a1"},
            {"name": "enp1", "mac": "00:0c:29:51:53:a2"},
        ]
        _metadata = {"network": {"interfaces": meta_interfaces}}
        if metadata:
            patch_dict(_metadata, metadata)
        md = gen_metadata(_metadata, public=public)

        network_data = NetworkData()
        with mockit(utils.get_interfaces, return_value=phys_interfaces):
            network_data.load(md.network)
        md.network = network_data

        return DistroBuilder(md)

    return func


def test_get_distro_builder_finds_correct_builder(fake_distro_builder):
    fake_distro = fake_distro_builder(["fakeos1", "fakeos2"])
    assert get_distro_builder("fakeos1") is fake_distro
    assert get_distro_builder("fakeOS2") is fake_distro
    assert get_distro_builder("fakeos3") is None


def test_get_distro_builder_finds_catch_all(fake_distro_builder):
    fake_distro1 = fake_distro_builder(["fakeos3"])
    fake_distro2 = fake_distro_builder("*")
    assert get_distro_builder("fakeos3") is fake_distro1
    assert get_distro_builder("catchmeos") is fake_distro2


def test_distro_builder_initializes_network_builders(
    fake_distro_builder, fake_network_builder, fake_metadata
):
    fake_distro = fake_distro_builder(["fakeos4"])
    fake_distro.network_builders = [fake_network_builder]

    distro = fake_distro(fake_metadata)
    distro.build()

    assert isinstance(distro.builders[0], fake_network_builder)


def test_distro_builder_returns_dict_with_tasks(
    fake_distro_builder, fake_network_builder, fake_metadata
):
    fake_distro = fake_distro_builder(["fakeos5"])
    distro = fake_distro(fake_metadata)
    distro.build()
    with mock.patch.object(distro, "render", return_value={"task": None}):
        with mock.patch("os.path.lexists") as mock_lexists:
            with mock.patch("os.remove") as mock_remove:
                with mock.patch.object(
                    fake_distro, "has_network_tasks", new_callable=mock.PropertyMock
                ) as mock_hnt:
                    mock_lexists.return_value = True
                    mock_remove.return_value = True
                    mock_hnt.return_value = True
                assert isinstance(distro.run("/path/to/rootfs"), dict)


def test_distro_builder_returns_dict_without_tasks(
    fake_distro_builder, fake_network_builder, fake_metadata
):
    fake_distro = fake_distro_builder(["fakeos6"])
    distro = fake_distro(fake_metadata)
    distro.build()
    with mock.patch.object(distro, "render", return_value=None):
        with mock.patch("os.path.lexists") as mock_lexists:
            with mock.patch("os.remove") as mock_remove:
                with mock.patch.object(
                    fake_distro, "has_network_tasks", new_callable=mock.PropertyMock
                ) as mock_hnt:
                    mock_lexists.return_value = True
                    mock_remove.return_value = True
                    mock_hnt.return_value = True
                    resp = distro.run("/path/to/rootfs")
                    assert isinstance(resp, dict)
                    assert len(resp) == 0


def test_distro_builder_has_correct_ipv_responses(
    fake_distro_builder_with_metadata, fake_address
):
    pub_ipv4_1 = fake_address()
    pub_ipv4_2 = fake_address()
    pub_ipv6_1 = fake_address(
        address_family=6, netmask="ffff:ffff:ffff:ffff:ffff:ffff:ffff:fffe"
    )
    pub_ipv6_2 = fake_address(
        address_family=6, netmask="ffff:ffff:ffff:ffff:ffff:ffff:ffff:fffe"
    )
    priv_ipv4_1 = fake_address(public=False)
    priv_ipv4_2 = fake_address(public=False)
    fake_distro = fake_distro_builder_with_metadata(
        {
            "network": {
                "!addresses": [
                    pub_ipv4_1,
                    pub_ipv4_2,
                    pub_ipv6_1,
                    pub_ipv6_2,
                    priv_ipv4_1,
                    priv_ipv4_2,
                ]
            }
        }
    )

    assert fake_distro.ipv4pub == [pub_ipv4_1, pub_ipv4_2]
    assert fake_distro.ipv6pub == [pub_ipv6_1, pub_ipv6_2]
    assert fake_distro.ipv4priv == [priv_ipv4_1, priv_ipv4_2]

    assert fake_distro.ipv4pub.first == pub_ipv4_1
    assert fake_distro.ipv6pub.first == pub_ipv6_1
    assert fake_distro.ipv4priv.first == priv_ipv4_1


def test_distro_builder_context_as_expected(fake_distro_builder_with_metadata):
    fake_distro = fake_distro_builder_with_metadata()
    context = fake_distro.context()
    wanted_context = {
        "hostname": fake_distro.metadata.hostname,
        "interfaces": fake_distro.network.interfaces,
        "iface0": fake_distro.network.interfaces[0],
        "ip4priv": fake_distro.ipv4priv.first,
        "ip4pub": fake_distro.ipv4pub.first,
        "ip6pub": fake_distro.ipv6pub.first,
        "net": fake_distro.network,
        "osinfo": fake_distro.metadata.operating_system,
        "private_subnets": fake_distro.network.private_subnets,
        "resolvers": fake_distro.network.resolvers,
    }

    assert context == wanted_context


def test_distro_builder_render_calls_has_network_tasks(
    fake_distro_builder_with_metadata,
):
    fake_distro = fake_distro_builder_with_metadata()
    fake_distro.tasks = {
        "path/to/file": """
        hostname = {{ hostname }}
    """
    }
    with mock.patch.object(
        fake_distro.__class__,
        "has_network_tasks",
        return_value=True,
        new_callable=mock.PropertyMock,
    ) as mock_has_network_tasks:
        fake_distro.render()

    mock_has_network_tasks.assert_called()


def test_distro_builder_render_does_nothing_with_delete_tasks(
    fake_distro_builder_with_metadata,
):
    fake_distro = fake_distro_builder_with_metadata()
    fake_distro.tasks = {"path/to/file": None}

    with mock.patch.object(
        fake_distro.__class__,
        "has_network_tasks",
        return_value=True,
        new_callable=mock.PropertyMock,
    ):
        rendered_tasks = fake_distro.render()
    assert rendered_tasks["path/to/file"] is None


def test_distro_builder_render_renders_string_tasks(fake_distro_builder_with_metadata):
    fake_distro = fake_distro_builder_with_metadata()
    fake_distro.tasks = {
        "path/to/file": """
        hostname = {{ hostname }}
    """
    }
    with mock.patch.object(
        fake_distro.__class__,
        "has_network_tasks",
        return_value=True,
        new_callable=mock.PropertyMock,
    ):
        rendered_tasks = fake_distro.render()

    wanted_content = "\nhostname = {hostname}\n".format(**fake_distro.context())
    assert rendered_tasks["path/to/file"] == wanted_content


def test_distro_builder_render_renders_dict_tasks(fake_distro_builder_with_metadata):
    fake_distro = fake_distro_builder_with_metadata()
    fake_distro.tasks = {
        "path/to/file": {
            "mode": 0o755,
            "template": """
                hostname = {{ hostname }}
            """,
        }
    }
    with mock.patch.object(
        fake_distro.__class__,
        "has_network_tasks",
        return_value=True,
        new_callable=mock.PropertyMock,
    ):
        rendered_tasks = fake_distro.render()

    wanted_mode = 0o755
    wanted_content = "\nhostname = {hostname}\n".format(**fake_distro.context())
    assert rendered_tasks["path/to/file"]["mode"] == wanted_mode
    assert rendered_tasks["path/to/file"]["content"] == wanted_content


def test_distro_builder_run_deletes_file(fake_distro_builder_with_metadata):
    fake_distro = fake_distro_builder_with_metadata()
    fake_distro.tasks = {"path/to/file": None}

    with mock.patch("os.path.lexists") as mock_lexists:
        with mock.patch("os.remove") as mock_remove:
            with mock.patch.object(
                fake_distro.__class__,
                "has_network_tasks",
                new_callable=mock.PropertyMock,
            ) as mock_hnt:
                mock_lexists.return_value = True
                mock_remove.return_value = True
                mock_hnt.return_value = True
                fake_distro.run("/path/to/rootfs")

    mock_lexists.assert_called_with("/path/to/rootfs/path/to/file")
    mock_remove.assert_called_with("/path/to/rootfs/path/to/file")


def test_distro_builder_run_skips_deleting_missing_file(
    fake_distro_builder_with_metadata,
):
    fake_distro = fake_distro_builder_with_metadata()
    fake_distro.tasks = {"path/to/file": None}

    with mock.patch("os.path.lexists") as mock_lexists:
        with mock.patch("os.remove") as mock_remove:
            with mock.patch.object(
                fake_distro.__class__,
                "has_network_tasks",
                new_callable=mock.PropertyMock,
            ) as mock_hnt:
                mock_lexists.return_value = False
                mock_remove.return_value = True
                mock_hnt.return_value = True
                fake_distro.run("/path/to/rootfs")

    mock_lexists.assert_called_with("/path/to/rootfs/path/to/file")
    mock_remove.assert_not_called()


def test_distro_builder_creates_file(fake_distro_builder_with_metadata):
    fake_distro = fake_distro_builder_with_metadata()
    fake_distro.tasks = {
        "path/to/file": """
        hostname = {{ hostname }}
    """
    }

    with mock.patch("os.path.lexists") as mock_lexists:
        with mock.patch("os.makedirs") as mock_makedirs:
            open_ = mock.mock_open()
            with mock.patch("builtins.open", open_) as mock_open:
                with mock.patch.object(
                    fake_distro.__class__,
                    "has_network_tasks",
                    new_callable=mock.PropertyMock,
                ) as mock_hnt:
                    mock_lexists.return_value = False
                    mock_makedirs.return_value = True
                    mock_hnt.return_value = True
                    fake_distro.run("/path/to/rootfs")

    mock_lexists.assert_called_with("/path/to/rootfs/path/to")
    mock_makedirs.assert_called_with("/path/to/rootfs/path/to", exist_ok=True)
    fh = mock_open.return_value.__enter__.return_value
    fh.write.assert_called_with(
        "\nhostname = {hostname}\n".format(**fake_distro.context())
    )


def test_distro_builder_creates_file_with_mode(fake_distro_builder_with_metadata):
    fake_distro = fake_distro_builder_with_metadata()
    fake_distro.tasks = {
        "path/to/file": {
            "mode": 0o755,
            "template": """
                hostname = {{ hostname }}
            """,
        }
    }

    with mock.patch("os.path.lexists") as mock_lexists:
        with mock.patch("os.makedirs") as mock_makedirs:
            open_ = mock.mock_open()
            with mock.patch("builtins.open", open_) as mock_open:
                with mock.patch("os.chmod") as mock_chmod:
                    with mock.patch.object(
                        fake_distro.__class__,
                        "has_network_tasks",
                        new_callable=mock.PropertyMock,
                    ) as mock_hnt:
                        mock_lexists.return_value = False
                        mock_makedirs.return_value = True
                        mock_chmod.return_value = True
                        mock_hnt.return_value = True
                        fake_distro.run("/path/to/rootfs")

    mock_lexists.assert_called_with("/path/to/rootfs/path/to")
    mock_makedirs.assert_called_with("/path/to/rootfs/path/to", exist_ok=True)
    mock_open.assert_called_with("/path/to/rootfs/path/to/file", "w")
    fh = mock_open()
    fh.write.assert_called_with(
        "\nhostname = {hostname}\n".format(**fake_distro.context())
    )
    mock_chmod.assert_called_with("/path/to/rootfs/path/to/file", 0o755)
