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


# pylama:ignore=E501
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


def test_private_bonded_task_etc_sysconfig_network_scripts_ifcfg_bond0(
    redhat_bonded_network
):
    """
    When no public ip is assigned, we should see the private ip details in the
    /etc/sysconfig/network-scripts/ifcfg-bond0 interface file.
    """
    builder = redhat_bonded_network(public=False)
    tasks = builder.render()
    result = dedent(
        """\
        DEVICE=bond0
        NAME=bond0
        IPADDR={ipv4priv.address}
        NETMASK={ipv4priv.netmask}
        GATEWAY={ipv4priv.gateway}
        BOOTPROTO=none
        ONBOOT=yes
        USERCTL=no
        TYPE=Bond
        BONDING_OPTS="mode={bonding_mode} miimon=100 downdelay=200 updelay=200"

        DNS1={dns1}
        DNS2={dns2}
    """
    ).format(
        ipv4priv=builder.ipv4priv.first,
        bonding_mode=builder.network.bonding.mode,
        dns1=builder.network.resolvers[0],
        dns2=builder.network.resolvers[1],
    )
    assert tasks["etc/sysconfig/network-scripts/ifcfg-bond0"] == result


def test_private_alias_task_etc_sysconfig_network_scripts_ifcfg_bond0_0(
    redhat_bonded_network
):
    """
    When a public ip is assigned, the private ip address should become an
    alias, this validates /etc/sysconfig/network-scripts/ifcfg-bond0:0 alias
    has been created for the private ip
    """
    builder = redhat_bonded_network(public=True)
    tasks = builder.render()
    result = dedent(
        """\
        DEVICE=bond0:0
        NAME=bond0:0
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
    assert tasks["etc/sysconfig/network-scripts/ifcfg-bond0:0"] == result


def test_private_alias_task_missing_for_private_only_bond(redhat_bonded_network):
    """
    When no public ip is assigned, we should not see an alias created
    therefore /etc/sysconfig/network-scripts/ifcfg-bond0:0 should not exist.
    """
    builder = redhat_bonded_network(public=False)
    tasks = builder.render()
    assert "etc/sysconfig/network-scripts/ifcfg-bond0:0" not in tasks


def test_private_route_task_etc_sysconfig_network_scripts_route_bond0(
    redhat_bonded_network
):
    """
    When using a public ip, the private ip is assigned as an alias, this
    validates the /etc/sysconfig/network-scripts/route-bond0 route is created
    for the private subnet.
    """
    builder = redhat_bonded_network(public=True)
    tasks = builder.render()
    result = dedent(
        """\
        10.0.0.0/8 via {ipv4priv.gateway} dev bond0:0
    """
    ).format(ipv4priv=builder.ipv4priv.first)
    assert tasks["etc/sysconfig/network-scripts/route-bond0"] == result


def test_private_route_task_missing_for_private_only_bond(redhat_bonded_network):
    """
    When no public ip is assigned, we should not see a route file created
    therefore /etc/sysconfig/network-scripts/route-bond0 should not exist.
    """
    builder = redhat_bonded_network(public=False)
    tasks = builder.render()
    assert "etc/sysconfig/network-scripts/route-bond0" not in tasks
