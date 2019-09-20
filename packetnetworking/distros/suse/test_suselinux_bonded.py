from textwrap import dedent
import pytest
from jinja2.exceptions import UndefinedError


@pytest.fixture
def suselinux_bonded_network(generic_suse_bonded_network):
    def _builder(**kwargs):
        return generic_suse_bonded_network("suselinux", 7, **kwargs)

    return _builder


def test_suselinux_private_only_throws_error(suselinux_bonded_network):
    """
    Verifies a jinja2 UndefinedError is thrown when providing only
    private ip information
    """
    builder = suselinux_bonded_network(public=False)
    with pytest.raises(UndefinedError):
        builder.render()


# pylama:ignore=E501
def test_suselinux_bonded_task_etc_modprobe_d_bonding(suselinux_bonded_network):
    """Validates /etc/modprobe.d/bonding.conf has correct bonding mode"""
    builder = suselinux_bonded_network()
    tasks = builder.render()
    result = dedent(
        """\
            alias bond0 bonding
            options bond0 mode={mode} miimon=100 downdelay=200 updelay=200 xmit_hash_policy=layer3+4 lacp_rate=1
    """
    ).format(mode=builder.network.bonding.mode)
    assert tasks["etc/modprobe.d/bonding.conf"] == result


def test_suselinux_public_bonded_task_etc_sysconfig_network_ifcfg_bond0(
    suselinux_bonded_network
):
    """Validates /etc/sysconfig/network/ifcfg-bond0 for a public bond"""
    builder = suselinux_bonded_network(public=True)
    tasks = builder.render()
    result = dedent(
        """\
        STARTMODE='onboot'
        BOOTPROTO='static'
        IPADDR='{ipv4pub.address}/{ipv4pub.cidr}'
        BONDING_MASTER='yes'
        BONDING_SLAVE_0='{iface0.name}'
        BONDING_SLAVE_1='{iface1.name}'
        BONDING_MODULE_OPTS='mode={bonding_mode} miimon=100'
        IPADDR1='{ipv4priv.address}'
        NETMASK1='{ipv4priv.netmask}'
        GATEWAY1='{ipv4priv.gateway}'
        LABEL1='0'
        IPADDR2='{ipv6pub.address}/{ipv6pub.cidr}'
        GATEWAY2='{ipv6pub.gateway}'
        LABEL2='1'
    """
    ).format(
        ipv4pub=builder.ipv4pub.first,
        ipv4priv=builder.ipv4priv.first,
        ipv6pub=builder.ipv6pub.first,
        iface0=builder.network.interfaces[0],
        iface1=builder.network.interfaces[1],
        bonding_mode=builder.network.bonding.mode,
    )
    assert tasks["etc/sysconfig/network/ifcfg-bond0"] == result


def test_suselinux_public_route_task_etc_sysconfig_network_routes(
    suselinux_bonded_network
):
    """
    Validates /etc/sysconfig/network/routes is configured correctly
    """
    builder = suselinux_bonded_network(public=True)
    tasks = builder.render()
    result = dedent(
        """\
        default     {ipv4pub.gateway}
        10.0.0.0/8  {ipv4priv.gateway}
    """
    ).format(ipv4pub=builder.ipv4pub.first, ipv4priv=builder.ipv4priv.first)
    assert tasks["etc/sysconfig/network/routes"] == result


def test_suselinux_public_route_task_etc_sysconfig_network_routes_with_custom_ip_space_routes(
    suselinux_bonded_network
):
    """
    Validates /etc/sysconfig/network/routes is configured correctly
    """
    routes = {"private_ip_space": ["192.168.5.0/24", "172.16.0.0/12"]}
    builder = suselinux_bonded_network(public=True, metadata=routes)
    tasks = builder.render()
    result = dedent(
        """\
        default     {ipv4pub.gateway}
        192.168.5.0/24  {ipv4priv.gateway}
        172.16.0.0/12  {ipv4priv.gateway}
    """
    ).format(ipv4pub=builder.ipv4pub.first, ipv4priv=builder.ipv4priv.first)
    assert tasks["etc/sysconfig/network/routes"] == result


def test_suselinux_public_task_etc_sysconfig_network_ifcfg_enp0(
    suselinux_bonded_network
):
    """
    For each interface, we should see the corresponding ifcfg file
    located at /etc/sysconfig/network/ifcfg-*
    """
    builder = suselinux_bonded_network(public=True)
    tasks = builder.render()
    result = dedent(
        """\
        STARTMODE='hotplug'
        BOOTPROTO='none'
    """
    )
    assert tasks["etc/sysconfig/network/ifcfg-enp0"] == result


def test_suselinux_public_task_etc_sysconfig_network_ifcfg_enp1(
    suselinux_bonded_network
):
    """
    For each interface, we should see the corresponding ifcfg file
    located at /etc/sysconfig/network/ifcfg-*
    """
    builder = suselinux_bonded_network(public=True)
    tasks = builder.render()
    result = dedent(
        """\
        STARTMODE='hotplug'
        BOOTPROTO='none'
    """
    )
    assert tasks["etc/sysconfig/network/ifcfg-enp1"] == result


def test_suselinux_etc_resolvers_configured(suselinux_bonded_network, fake):
    """
    Validates /etc/resolv.conf is configured correctly
    """
    builder = suselinux_bonded_network()
    resolver1 = fake.ipv4()
    resolver2 = fake.ipv4()
    builder.network.resolvers = (resolver1, resolver2)
    tasks = builder.render()
    result = dedent(
        """\
        nameserver {resolver1}
        nameserver {resolver2}
    """
    ).format(resolver1=resolver1, resolver2=resolver2)
    assert tasks["etc/resolv.conf"] == result


def test_suselinux_etc_hostname_configured(suselinux_bonded_network):
    """
    Validates /etc/hostname is configured correctly
    """
    builder = suselinux_bonded_network()
    tasks = builder.render()
    result = dedent(
        """\
        {hostname}
    """
    ).format(hostname=builder.metadata.hostname)
    assert tasks["etc/hostname"] == result


def test_suselinux_etc_hosts_configured(suselinux_bonded_network):
    """
    Validates /etc/hosts is configured correctly
    """
    builder = suselinux_bonded_network()
    tasks = builder.render()
    result = dedent(
        """\
        127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
        ::1         localhost localhost.localdomain localhost6 localhost6.localdomain6
    """
    )
    assert tasks["etc/hosts"] == result
