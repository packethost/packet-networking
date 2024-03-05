from textwrap import dedent
from ... import utils
import os
import pytest
from .conftest import versions


@pytest.fixture
def individual_network_builder(generic_redhat_individual_network):
    def _builder(distro, version, **kwargs):
        return generic_redhat_individual_network(distro, version, **kwargs)

    return _builder


@pytest.mark.parametrize("distro,version", versions)
def test_public_individual_task_etc_sysconfig_network(
    individual_network_builder, distro, version
):
    """Validates /etc/sysconfig/network for a public bond"""
    builder = individual_network_builder(distro, version, public=True)
    tasks = builder.render()
    result = dedent(
        """\
        NETWORKING=yes
        HOSTNAME={hostname}
        GATEWAY={gateway}
        GATEWAYDEV=enp0
        NOZEROCONF=yes
    """
    ).format(hostname=builder.metadata.hostname, gateway=builder.ipv4pub.first.gateway)
    assert tasks["etc/sysconfig/network"] == result


@pytest.mark.parametrize("distro,version", versions)
def test_public_individual_task_etc_sysconfig_network_scripts_ifcfg_enp0(
    individual_network_builder, distro, version
):
    """Validates /etc/sysconfig/network-scripts/ifcfg-enp0 for a public bond"""
    builder = individual_network_builder(distro, version, public=True)
    tasks = builder.render()
    result = dedent(
        """\
        DEVICE=enp0
        NAME=enp0
        IPADDR={ipv4pub.address}
        NETMASK={ipv4pub.netmask}
        GATEWAY={ipv4pub.gateway}
        BOOTPROTO=none
        ONBOOT=yes
        USERCTL=no

        IPV6INIT=yes
        IPV6ADDR={ipv6pub.address}/{ipv6pub.cidr}
        IPV6_DEFAULTGW={ipv6pub.gateway}
        DNS1={dns1}
        DNS2={dns2}
    """
    ).format(
        ipv4pub=builder.ipv4pub.first,
        ipv6pub=builder.ipv6pub.first,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/sysconfig/network-scripts/ifcfg-enp0"] == result


@pytest.mark.parametrize("distro,version", versions)
def test_private_individual_task_etc_sysconfig_network_scripts_ifcfg_enp0(
    individual_network_builder, distro, version
):
    """
    When no public ip is assigned, we should see the private ip details in the
    /etc/sysconfig/network-scripts/ifcfg-enp0 interface file.
    """
    builder = individual_network_builder(distro, version, public=False)
    tasks = builder.render()
    result = dedent(
        """\
        DEVICE=enp0
        NAME=enp0
        IPADDR={ipv4priv.address}
        NETMASK={ipv4priv.netmask}
        GATEWAY={ipv4priv.gateway}
        BOOTPROTO=none
        ONBOOT=yes
        USERCTL=no

        DNS1={dns1}
        DNS2={dns2}
    """
    ).format(
        ipv4priv=builder.ipv4priv.first,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/sysconfig/network-scripts/ifcfg-enp0"] == result


@pytest.mark.parametrize("distro,version", versions)
def test_private_alias_task_etc_sysconfig_network_scripts_ifcfg_enp0_0(
    individual_network_builder, distro, version
):
    """
    When a public ip is assigned, the private ip address should become an
    alias, this validates /etc/sysconfig/network-scripts/ifcfg-enp0:0 alias
    has been created for the private ip
    """
    builder = individual_network_builder(distro, version, public=True)
    tasks = builder.render()
    result = dedent(
        """\
        DEVICE=enp0:0
        NAME=enp0:0
        IPADDR={ipv4priv.address}
        NETMASK={ipv4priv.netmask}
        GATEWAY={ipv4priv.gateway}
        BOOTPROTO=none
        ONBOOT=yes
        USERCTL=no
        DNS1={dns1}
        DNS2={dns2}
    """
    ).format(
        ipv4priv=builder.ipv4priv.first,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/sysconfig/network-scripts/ifcfg-enp0:0"] == result


@pytest.mark.parametrize("distro,version", versions)
def test_private_alias_task_missing_for_private_only_enp(
    individual_network_builder, distro, version
):
    """
    When no public ip is assigned, we should not see an alias created
    therefore /etc/sysconfig/network-scripts/ifcfg-enp0:0 should not exist.
    """
    builder = individual_network_builder(distro, version, public=False)
    tasks = builder.render()
    assert "etc/sysconfig/network-scripts/ifcfg-enp0:0" not in tasks


@pytest.mark.parametrize("distro,version", versions)
def test_private_route_task_etc_sysconfig_network_scripts_route_enp0(
    individual_network_builder, distro, version
):
    """
    When using a public ip, the private ip is assigned as an alias, this
    validates the /etc/sysconfig/network-scripts/route-enp0 route is created
    for the private subnet.
    """
    builder = individual_network_builder(distro, version, public=True)
    tasks = builder.render()
    result = dedent(
        """\
        10.0.0.0/8 via {ipv4priv.gateway} dev enp0:0
    """
    ).format(ipv4priv=builder.ipv4priv.first)
    assert tasks["etc/sysconfig/network-scripts/route-enp0"] == result


@pytest.mark.parametrize("distro,version", versions)
def test_private_route_task_etc_sysconfig_network_scripts_route_enp0_with_custom_private_subnets(
    individual_network_builder, distro, version
):
    """
    When using a public ip, the private ip is assigned as an alias, this
    validates the /etc/sysconfig/network-scripts/route-enp0 route is created
    for the private subnet.
    """
    subnets = {"private_subnets": ["192.168.5.0/24", "172.16.0.0/12"]}
    builder = individual_network_builder(distro, version, public=True, metadata=subnets)
    tasks = builder.render()
    result = dedent(
        """\
        192.168.5.0/24 via {ipv4priv.gateway} dev enp0:0
        172.16.0.0/12 via {ipv4priv.gateway} dev enp0:0
    """
    ).format(ipv4priv=builder.ipv4priv.first)
    assert tasks["etc/sysconfig/network-scripts/route-enp0"] == result


@pytest.mark.parametrize("distro,version", versions)
def test_private_route_task_missing_for_private_only_enp(
    individual_network_builder, distro, version
):
    """
    When no public ip is assigned, we should not see a route file created
    therefore /etc/sysconfig/network-scripts/route-enp0 should not exist.
    """
    builder = individual_network_builder(distro, version, public=False)
    tasks = builder.render()
    assert "etc/sysconfig/network-scripts/route-enp0" not in tasks


@pytest.mark.parametrize("distro,version", versions)
def test_etc_resolvers_configured(individual_network_builder, fake, distro, version):
    """
    Validates /etc/resolv.conf is configured correctly
    """
    builder = individual_network_builder(distro, version)
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


@pytest.mark.parametrize("distro,version", versions)
def test_etc_hostname_configured(individual_network_builder, distro, version):
    """
    Validates /etc/hostname is configured correctly
    """
    builder = individual_network_builder(distro, version)
    tasks = builder.render()
    result = dedent(
        """\
        {hostname}
    """
    ).format(hostname=builder.metadata.hostname)
    assert tasks["etc/hostname"] == result


@pytest.mark.parametrize("distro,version", versions)
def test_etc_hosts_configured(individual_network_builder, distro, version):
    """
    Validates /etc/hosts is configured correctly
    """
    builder = individual_network_builder(distro, version)
    tasks = builder.render()
    result = dedent(
        """\
        127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
        ::1         localhost localhost.localdomain localhost6 localhost6.localdomain6
    """
    )
    assert tasks["etc/hosts"] == result


@pytest.mark.parametrize("distro,version", versions)
def test_network_manager_is_disabled(individual_network_builder, distro, version):
    """
    When using certain operating systems, we want to disable Network Manager,
    here we make sure those distros remove the necessary files
    """
    builder = individual_network_builder(distro, version)
    tasks = builder.render()
    for service in (
        "dbus-org.freedesktop.NetworkManager",
        "dbus-org.freedesktop.nm-dispatcher",
        "multi-user.target.wants/NetworkManager",
    ):
        assert (
            tasks.get(os.path.join("etc/systemd/system", service + ".service")) is None
        )


@pytest.mark.parametrize("distro,version", versions)
def test_persistent_interface_names(individual_network_builder, distro, version):
    """
    When using certain operating systems, we want to bypass driver interface name,
    here we make sure the /etc/udev/rules.d/70-persistent-net.rules is generated.
    """
    builder = individual_network_builder(distro, version)
    tasks = builder.render()
    result = dedent(
        """\
        {header}
        #
        # You can modify it, as long as you keep each rule on a single
        # line, and change only the value of the NAME= key.

        # PCI device (custom name provided by external tool to mimic Predictable Network Interface Names)
        SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", ATTR{{address}}=="{iface0.mac}", ATTR{{dev_id}}=="0x0", ATTR{{type}}=="1", NAME="{iface0.name}"

        # PCI device (custom name provided by external tool to mimic Predictable Network Interface Names)
        SUBSYSTEM=="net", ACTION=="add", DRIVERS=="?*", ATTR{{address}}=="{iface1.mac}", ATTR{{dev_id}}=="0x0", ATTR{{type}}=="1", NAME="{iface1.name}"
    """
    ).format(
        header=utils.generated_header(),
        iface0=builder.network.interfaces[0],
        iface1=builder.network.interfaces[1],
    )
    if distro in ("almalinux", "centos"):
        # except for centos, we do not want a persistent-net.rules for centos
        assert "etc/udev/rules.d/70-persistent-net.rules" not in tasks
    else:
        assert tasks["etc/udev/rules.d/70-persistent-net.rules"] == result
