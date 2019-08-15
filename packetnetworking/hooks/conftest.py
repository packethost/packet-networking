import pytest
import mock
from ..builder import Builder
from .. import utils


@pytest.fixture
def plan_builder(fake, metadata, patch_dict):
    gen_metadata = metadata

    def _builder(plan, metadata=None, public=True):
        meta_interfaces = [
            {"name": "eth0", "mac": "00:0c:29:51:53:a1", "bond": "bond0"},
            {"name": "eth1", "mac": "00:0c:29:51:53:a2", "bond": "bond0"},
        ]
        _metadata = patch_dict(
            {"plan": plan, "network": {"interfaces": meta_interfaces}}, metadata or {}
        )
        md = gen_metadata(_metadata, public=public)
        return Builder(md)

    return _builder


@pytest.fixture
def mocked_trigger(mockit, plan_builder):
    def _builder(plan, *hooks, physical_interfaces=None, **kwargs):
        builder = plan_builder(plan, **kwargs)
        triggers = {}
        for hook_cls, trigger in hooks:
            if trigger not in triggers:
                triggers[trigger] = [hook_cls]
            else:
                triggers[trigger].append(hook_cls)

        def trigger(trigger, *args, **kwargs):
            hook_classes = triggers.get(trigger, [])
            results = []
            for hook_cls in hook_classes:
                hook = hook_cls()
                try:
                    results.append(
                        getattr(hook, "hook_" + trigger)(builder, *args, **kwargs)
                    )
                except AttributeError:
                    pass
            return results

        phys_interfaces = physical_interfaces or [
            {"name": "enp0", "mac": "00:0c:29:51:53:a1"},
            {"name": "enp1", "mac": "00:0c:29:51:53:a2"},
        ]
        with mockit(utils.get_interfaces, return_value=phys_interfaces):
            with mock.patch.object(builder, "trigger", trigger):
                return builder.initialize()

    return _builder
