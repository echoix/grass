# Common pytest fixtures available for all tests in this directory or in a nested directory

# use as a decorator like @xfail_mp_spawn
xfail_mp_spawn = pytest.mark.xfail(
    multiprocessing.get_start_method() == "spawn",
    reason="Multiprocessing 'spawn' start method requires pickable functions",
    raises=AttributeError,
)
