from .distro_builder import DistroBuilder, get_distro_builder
import pytest


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
        def __init__(self, metadata):
            pass

        def build(self):
            pass

        def run(self, rootfs_path):
            pass

    return FakeNetworkBuilder


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
    fake_distro_builder, fake_network_builder
):
    fake_distro = fake_distro_builder(["fakeos4"])
    fake_distro.network_builders = [fake_network_builder]

    distro = fake_distro(None)
    distro.build()

    assert isinstance(distro.builders[0], fake_network_builder)


def test_distro_builder_returns_true_with_tasks(
    fake_distro_builder, fake_network_builder
):
    def true_run(self, rootfs_path):
        return True

    fake_network_builder.run = true_run

    fake_distro = fake_distro_builder(["fakeos5"])
    fake_distro.network_builders = [fake_network_builder]

    distro = fake_distro(None)
    distro.build()
    assert distro.run(None) is True


def test_distro_builder_returns_none_without_tasks(
    fake_distro_builder, fake_network_builder
):
    def false_run(self, rootfs_path):
        return False

    fake_network_builder.run = false_run

    fake_distro = fake_distro_builder(["fakeos6"])
    fake_distro.network_builders = [fake_network_builder]

    distro = fake_distro(None)
    distro.build()
    assert distro.run(None) is None
