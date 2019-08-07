from ... import utils
from textwrap import dedent


def test_bonded_tasks(mockit, redhat_bonded_network):
    """Checks the expected number of tasks are created"""
    builder = redhat_bonded_network()
    assert len(builder.tasks) == 14


def test_public_bonded_task_etc_sysconfig_network(mockit, redhat_bonded_network):
    builder = redhat_bonded_network(public=True)
    tasks = builder.render()
    result = dedent(
        """\
        NETWORKING=yes
        HOSTNAME={hostname}
        GATEWAY={gateway}
        GATEWAYDEV=bond0
        NOZEROCONF=yes
    """
    ).format(hostname=builder.metadata.hostname, gateway=builder.ipv4pub.first.gateway)
    assert tasks["etc/sysconfig/network"] == result


def test_private_bonded_task_etc_sysconfig_network(mockit, redhat_bonded_network):
    builder = redhat_bonded_network(public=False)
    tasks = builder.render()
    result = dedent(
        """\
        NETWORKING=yes
        HOSTNAME={hostname}
        GATEWAY={gateway}
        GATEWAYDEV=bond0
        NOZEROCONF=yes
    """
    ).format(hostname=builder.metadata.hostname, gateway=builder.ipv4priv.first.gateway)
    assert tasks["etc/sysconfig/network"] == result
