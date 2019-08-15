from .builder_hook import BuilderHook


class FakeHook(BuilderHook):
    pass


def test_builder_hook_not_implemented_doesnt_raise_exception(mocked_trigger):
    mocked_trigger("x1.small.x86", (FakeHook, "initialized"))
    # No exception should be raised
