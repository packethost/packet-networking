from ... import utils
from textwrap import dedent


def test_public_bonded_tasks(redhat_bonded_network):
    """Checks the expected number of tasks are created for a public bond"""
    builder = redhat_bonded_network()
    assert len(builder.tasks) == 14


def test_private_bonded_tasks(redhat_bonded_network):
    """Checks the expected number of tasks are created for a private bond"""
    builder = redhat_bonded_network(public=False)
    assert len(builder.tasks) == 12


def test_public_bonded_task_etc_sysconfig_network(redhat_bonded_network):
    """Validates /etc/sysconfig/network for a public bond"""
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


def test_private_bonded_task_etc_sysconfig_network(redhat_bonded_network):
    """Validates /etc/sysconfig/network for a private only bond"""
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


def test_bonded_task_etc_modprobe_d_bonding(redhat_bonded_network):
    """Validates /etc/modprobe.d/bonding.conf has correct bonding mode"""
    builder = redhat_bonded_network()
    tasks = builder.render()
    result = dedent(
        """\
        alias bond0 bonding
        options bond0 mode={mode} miimon=100 downdelay=200 updelay=200 xmit_hash_policy=layer3+4 lacp_rate=1
    """
    ).format(mode=builder.network.bonding.mode)
    assert tasks["etc/modprobe.d/bonding.conf"] == result


def test_public_bonded_task_etc_sysconfig_network_scripts_ifcfg_bond0(
    redhat_bonded_network
):
    """Validates /etc/sysconfig/network-scripts/ifcfg-bond0 for a public bond"""
    builder = redhat_bonded_network(public=True)
    tasks = builder.render()
    result = dedent(
        """\
        DEVICE=bond0
        NAME=bond0
        IPADDR={ipv4pub.address}
        NETMASK={ipv4pub.netmask}
        GATEWAY={ipv4pub.gateway}
        BOOTPROTO=none
        ONBOOT=yes
        USERCTL=no
        TYPE=Bond
        BONDING_OPTS="mode={bonding_mode} miimon=100 downdelay=200 updelay=200"

        IPV6INIT=yes
        IPV6ADDR={ipv6pub.address}/{ipv6pub.cidr}
        IPV6_DEFAULTGW={ipv6pub.gateway}
        DNS1={dns1}
        DNS2={dns2}
    """
    ).format(
        ipv4pub=builder.ipv4pub.first,
        ipv6pub=builder.ipv6pub.first,
        bonding_mode=builder.network.bonding.mode,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/sysconfig/network-scripts/ifcfg-bond0"] == result
