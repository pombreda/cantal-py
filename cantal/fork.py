import time
from contextlib import contextmanager

from .simple_state import State
from .counters import Counter


class Branch(object):
    __slots__ = ('name', '_parent', '_counter', '_duration')

    def __init__(self, suffix, state, parent, **kwargs):
        self.name = suffix
        self._parent = parent
        self._counter = Counter(state=state + '.' + suffix,
            metric='count', **kwargs)
        self._duration = Counter(state=state + '.' + suffix,
            metric='duration', **kwargs)

    def enter(self):
        self._parent.enter_branch(self)

    def _commit(self, start, fin):
        self._counter.incr(1)
        self._duration.incr(fin - start)


class Fork(object):

    def __init__(self, branches, state, **kwargs):
        state_obj = State(state=state, **kwargs)
        for name in branches:
            setattr(self, name, Branch(name,
                parent=self, state=state, **kwargs))
        self._state = state_obj
        self._branch = None
        # We do our best not to crash any code which does accouning the
        # wrong way. So to report the problems we use a separate counter
        self._err = Counter(metric="err", state=state, **kwargs)

    @contextmanager
    def context(self):
        if self._branch is not None:
            self._err.incr()
        self._branch = None
        self._state.enter('_')
        try:
            yield
        finally:
            ts = int(time.time()*1000)
            if self._branch is not None:
                self._branch._commit(self._timestamp, ts)
            self._state.exit()
            self._branch = None

    def enter_branch(self, branch):
        ts = int(time.time()*1000)
        if self._branch is not None:
            self._branch._commit(self._timestamp, ts)
        self._state.enter(branch.name, _timestamp=ts)
        self._timestamp = ts
        self._branch = branch
