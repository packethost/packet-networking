from .single_interface_hook import SingleInterfaceHook


def test_x1_small_x86_single_interface_hook(mocked_trigger):
    builder = mocked_trigger("x1.small.x86", (SingleInterfaceHook, "initialized"))
    assert len(builder.network.interfaces) == 1
    assert builder.network.interfaces[0]["mac"] == "00:0c:29:51:53:a1"


def test_baremetal_1e_single_interface_hook(mocked_trigger):
    builder = mocked_trigger("baremetal_1e", (SingleInterfaceHook, "initialized"))
    assert len(builder.network.interfaces) == 1
    assert builder.network.interfaces[0]["mac"] == "00:0c:29:51:53:a1"


def test_unmodified_plan_single_interface_hook(mocked_trigger):
    builder = mocked_trigger("unmodified.plan", (SingleInterfaceHook, "initialized"))
    assert len(builder.network.interfaces) == 2
    assert builder.network.interfaces[0]["mac"] == "00:0c:29:51:53:a1"
    assert builder.network.interfaces[1]["mac"] == "00:0c:29:51:53:a2"
