from ... import utils
from ...builder import OSInfo
from .bonded import RedhatBondedNetwork

def test_bonded_tasks(mockit, redhatbuilder):
    osinfo = OSInfo('centos', 7)
    redhatbuilder.build(osinfo)

    bonded_builders = 0
    for builder in redhatbuilder.builders:
        if isinstance(builder, RedhatBondedNetwork):
            bonded_builders += 1
            assert len(builder.tasks) == 14

    assert bonded_builders > 0

