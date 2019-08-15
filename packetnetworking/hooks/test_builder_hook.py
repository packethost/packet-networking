from .builder_hook import BuilderHook


class FakeHook(BuilderHook):
    pass


def test_builder_hook_not_implemented_doesnt_raise_exception(mocked_trigger):
    builder = mocked_trigger("x1.small.x86", (FakeHook, "initialized"))
    builder.initialize()
    # No exception should be raised
