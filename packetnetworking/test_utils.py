from . import utils
from unittest.mock import patch

import pytest


@pytest.mark.parametrize(
    "abspath",
    [
        pytest.param(False, id="Not using abs path"),
        pytest.param(True, id="Using abs path"),
    ],
)
@pytest.mark.parametrize(
    "initdepth,recerr,islinkcnt,readlinkcnt",
    [
        pytest.param(0, False, 2, 1, id="Depth: 0"),
        pytest.param(1, False, 2, 1, id="Init Depth: 1"),
        pytest.param(
            utils.MAX_RESOLVE_DEPTH - 1, False, 2, 1, id="Init Depth: MAX - 1"
        ),
        pytest.param(utils.MAX_RESOLVE_DEPTH, True, 1, 1, id="Init Depth: MAX"),
        pytest.param(utils.MAX_RESOLVE_DEPTH + 1, True, 0, 0, id="Init Depth: MAX + 1"),
    ],
)
@pytest.mark.parametrize(
    "path,link,expected",
    [
        pytest.param("/etc/resolv.conf", None, "/etc/resolv.conf", id="Regular file"),
        pytest.param(
            "/etc/resolv.conf",
            "/etc/resolv.conf.d/default.resolv.conf",
            "/etc/resolv.conf.d/default.resolv.conf",
            id="Absolute reference",
        ),
        pytest.param(
            "/etc/resolv.conf",
            "./resolv.conf.d/default.resolv.conf",
            "/etc/resolv.conf.d/default.resolv.conf",
            id="./ reference",
        ),
        pytest.param(
            "/etc/resolv.conf",
            "../etc/resolv.conf.d/default.resolv.conf",
            "/etc/resolv.conf.d/default.resolv.conf",
            id="../ reference",
        ),
        pytest.param(
            "/etc/resolv.conf",
            "../../../../etc/resolv.conf.d/default.resolv.conf",
            "/etc/resolv.conf.d/default.resolv.conf",
            id="../ reference (above root)",
        ),
    ],
)
def test_resolve_path(
    abspath, path, link, expected, initdepth, recerr, islinkcnt, readlinkcnt
):
    rootfs = "/mnt/target"
    expected = rootfs + expected
    if abspath:
        path = rootfs + path

    # If not a symlink, no recursion should happen
    if not link:
        if islinkcnt > 1:
            islinkcnt = islinkcnt - 1
        if readlinkcnt > 0:
            readlinkcnt = readlinkcnt - 1
            if readlinkcnt == 0:
                # RecursionError should not be hit
                recerr = False

    with patch("os.path.islink") as mocked_islink:
        mocked_islink.side_effect = [True if link else False, False]
        with patch("os.readlink") as mocked_readlink:
            mocked_readlink.return_value = link
            if recerr:
                with pytest.raises(RecursionError):
                    result = utils.resolve_path(rootfs, path, _depth=initdepth)
            else:
                result = utils.resolve_path(rootfs, path, _depth=initdepth)

    assert mocked_islink.call_count == islinkcnt
    assert mocked_readlink.call_count == readlinkcnt
    if not recerr:
        assert result == expected
