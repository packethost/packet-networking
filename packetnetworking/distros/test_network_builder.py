from .network_builder import NetworkBuilder
from ..builder import NetworkData
from .. import utils
import mock
import pytest


@pytest.fixture
def fake_network_builder(mockit, fake, metadata, patch_dict):
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

        return NetworkBuilder(md)

    return func


def test_network_builder_has_correct_ipv_responses(fake_network_builder, fake_address):
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
    fake_network = fake_network_builder(
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

    assert fake_network.ipv4pub == [pub_ipv4_1, pub_ipv4_2]
    assert fake_network.ipv6pub == [pub_ipv6_1, pub_ipv6_2]
    assert fake_network.ipv4priv == [priv_ipv4_1, priv_ipv4_2]

    assert fake_network.ipv4pub.first == pub_ipv4_1
    assert fake_network.ipv6pub.first == pub_ipv6_1
    assert fake_network.ipv4priv.first == priv_ipv4_1


def test_network_builder_context_as_expected(fake_network_builder):
    fake_network = fake_network_builder()
    context = fake_network.context()
    wanted_context = {
        "hostname": fake_network.metadata.hostname,
        "interfaces": fake_network.network.interfaces,
        "iface0": fake_network.network.interfaces[0],
        "ip4priv": fake_network.ipv4priv.first,
        "ip4pub": fake_network.ipv4pub.first,
        "ip6pub": fake_network.ipv6pub.first,
        "net": fake_network.network,
        "osinfo": fake_network.metadata.operating_system,
        "private_subnets": fake_network.network.private_subnets,
        "resolvers": fake_network.network.resolvers,
    }

    assert context == wanted_context


def test_network_builder_render_does_nothing_with_delete_tasks(fake_network_builder):
    fake_network = fake_network_builder()
    fake_network.tasks = {"path/to/file": None}

    rendered_tasks = fake_network.render()
    assert rendered_tasks["path/to/file"] is None


def test_network_builder_render_renders_string_tasks(fake_network_builder):
    fake_network = fake_network_builder()
    fake_network.tasks = {
        "path/to/file": """
        hostname = {{ hostname }}
    """
    }
    rendered_tasks = fake_network.render()

    wanted_content = "\nhostname = {hostname}\n".format(**fake_network.context())
    assert rendered_tasks["path/to/file"] == wanted_content


def test_network_builder_render_renders_dict_tasks(fake_network_builder):
    fake_network = fake_network_builder()
    fake_network.tasks = {
        "path/to/file": {
            "mode": 0o755,
            "template": """
                hostname = {{ hostname }}
            """,
        }
    }
    rendered_tasks = fake_network.render()

    wanted_mode = 0o755
    wanted_content = "\nhostname = {hostname}\n".format(**fake_network.context())
    assert rendered_tasks["path/to/file"]["mode"] == wanted_mode
    assert rendered_tasks["path/to/file"]["content"] == wanted_content


def test_network_builder_run_deletes_file(fake_network_builder):
    fake_network = fake_network_builder()
    fake_network.tasks = {"path/to/file": None}

    with mock.patch("os.path.lexists") as mock_lexists:
        with mock.patch("os.remove") as mock_remove:
            mock_lexists.return_value = True
            mock_remove.return_value = True
            fake_network.run("/path/to/rootfs")

    mock_lexists.assert_called_with("/path/to/rootfs/path/to/file")
    mock_remove.assert_called_with("/path/to/rootfs/path/to/file")


def test_network_builder_run_skips_deleting_missing_file(fake_network_builder):
    fake_network = fake_network_builder()
    fake_network.tasks = {"path/to/file": None}

    with mock.patch("os.path.lexists") as mock_lexists:
        with mock.patch("os.remove") as mock_remove:
            mock_lexists.return_value = False
            mock_remove.return_value = True
            fake_network.run("/path/to/rootfs")

    mock_lexists.assert_called_with("/path/to/rootfs/path/to/file")
    mock_remove.assert_not_called()


def test_network_builder_creates_file(fake_network_builder):
    fake_network = fake_network_builder()
    fake_network.tasks = {
        "path/to/file": """
        hostname = {{ hostname }}
    """
    }

    with mock.patch("os.path.lexists") as mock_lexists:
        with mock.patch("os.makedirs") as mock_makedirs:
            open_ = mock.mock_open()
            with mock.patch("builtins.open", open_) as mock_open:
                mock_lexists.return_value = False
                mock_makedirs.return_value = True
                fake_network.run("/path/to/rootfs")

    mock_lexists.assert_called_with("/path/to/rootfs/path/to")
    mock_makedirs.assert_called_with("/path/to/rootfs/path/to", exist_ok=True)
    fh = mock_open.return_value.__enter__.return_value
    fh.write.assert_called_with(
        "\nhostname = {hostname}\n".format(**fake_network.context())
    )


def test_network_builder_creates_file_with_mode(fake_network_builder):
    fake_network = fake_network_builder()
    fake_network.tasks = {
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
                    mock_lexists.return_value = False
                    mock_makedirs.return_value = True
                    mock_chmod.return_value = True
                    fake_network.run("/path/to/rootfs")

    mock_lexists.assert_called_with("/path/to/rootfs/path/to")
    mock_makedirs.assert_called_with("/path/to/rootfs/path/to", exist_ok=True)
    mock_open.assert_called_with("/path/to/rootfs/path/to/file", "w")
    fh = mock_open()
    fh.write.assert_called_with(
        "\nhostname = {hostname}\n".format(**fake_network.context())
    )
    mock_chmod.assert_called_with("/path/to/rootfs/path/to/file", 0o755)
