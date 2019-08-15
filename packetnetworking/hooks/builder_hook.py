import re


class BuilderHook:
    pass


def trigger_hook(hook_name, context):
    hook_func = re.sub("[^a-z0-9]+", "_", hook_name, flags=re.I).lower()
    results = []
    for Hook in BuilderHook.__subclasses__():
        hook = Hook()
        try:
            results.append(getattr(hook, "hook_" + hook_func)(context))
        except AttributeError:
            pass
    return results
