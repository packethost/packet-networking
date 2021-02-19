import pytest
from .logical_interface_names_hook import LogicalInterfaceNamesHook


@pytest.fixture
def mocked_trigger_logical_names(mocked_trigger):
    def _builder(*args, **kwargs):

        phys_interfaces = [
            {"name": "enp0", "mac": "00:0c:29:51:53:a1", "names": {"LOGICAL": "ens0"}},
            {"name": "enp1", "mac": "00:0c:29:51:53:a2", "names": {"LOGICAL": "ens1"}},
        ]

        return mocked_trigger(*args, physical_interfaces=phys_interfaces, **kwargs)

    return _builder


def test_baremetal_hua_logical_interface_names_hook_iface0_name(
    mocked_trigger_logical_names,
):
    builder = mocked_trigger_logical_names(
        "baremetal_hua", (LogicalInterfaceNamesHook, "initialized")
    )
    assert builder.network.interfaces[0]["name"] == "ens0"


def test_baremetal_hua_logical_interface_names_hook_iface1_name(
    mocked_trigger_logical_names,
):
    builder = mocked_trigger_logical_names(
        "baremetal_hua", (LogicalInterfaceNamesHook, "initialized")
    )
    assert builder.network.interfaces[1]["name"] == "ens1"


def test_unmodified_plan_logical_interface_names_hook_iface0_name(
    mocked_trigger_logical_names,
):
    builder = mocked_trigger_logical_names(
        "unmodified.plan", (LogicalInterfaceNamesHook, "initialized")
    )
    assert builder.network.interfaces[0]["name"] == "enp0"


def test_unmodified_plan_logical_interface_names_hook_iface1_name(
    mocked_trigger_logical_names,
):
    builder = mocked_trigger_logical_names(
        "unmodified.plan", (LogicalInterfaceNamesHook, "initialized")
    )
    assert builder.network.interfaces[1]["name"] == "enp1"
