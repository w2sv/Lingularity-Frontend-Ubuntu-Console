from abc import ABC


class MonoStateClass(ABC):
    _mono_state = {}
    _refcount = 0

    def __new__(cls, *args, **kwargs):
        if not kwargs.get('classmethod_invocation') and cls._refcount != 0:
            raise AttributeError('monostate class not to be reinitialized')

        cls._refcount += 1

        return super().__new__(cls)

    def __init__(self):
        self.__dict__ = self._mono_state

    @classmethod
    def get_instance(cls):
        instance = cls.__new__(cls, classmethod_invocation=True)
        super(cls, instance).__init__()
        return instance
