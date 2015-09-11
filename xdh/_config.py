import abc
import builtins
import collections.abc
import copy
import functools
import gzip
import itertools
import sys
import types


def parse_element(elem):
    isinstance = builtins.isinstance
    
    if isinstance(elem, type):
        ret = elem
        
    elif isinstance(elem, BaseConfig):
        ret = elem
        
    elif isinstance(elem, collections.abc.Mapping):
        ret = DictConfig(elem)
        
    elif isinstance(elem, collections.abc.Set):
        ret = frozenset(parse_element(value) for value in elem)
        
    elif not isinstance(elem, (str, bytes, bytearray)) and all(
        isinstance(elem, type_)
        for type_ in {
            collections.abc.Sized,
            collections.abc.Iterable,
            collections.abc.Container,
            collections.abc.Sequence
        }
    ):
        ret = tuple(parse_element(value) for value in elem)
        
    else:
        ret = elem
        
    return ret

def unpack_element(elem, *, memo={}):
    try:
        return memo[id(self)]
        
    except KeyError:
        isinstance = builtins.isinstance
        
        if isinstance(elem, type):
            ret = elem
            
    
        elif isinstance(elem, collections.abc.Mapping):
            ret = {
                key: unpack_element(value, memo=memo)
                for key, value in elem.items()
            }
            
        elif isinstance(elem, collections.abc.Set):
            ret = {unpack_element(value, memo=memo) for value in elem}
            
        elif not isinstance(elem, (str, bytes, bytearray)) and all(
            isinstance(elem, type_)
            for type_ in {
                collections.abc.Sized,
                collections.abc.Iterable,
                collections.abc.Container,
                collections.abc.Sequence
            }
        ):
            ret = [unpack_element(value, memo=memo) for value in elem]
            
        else:
            ret = elem
            
        memo[id(self)] = ret
            
        return memo[id(self)]


class SingletonMeta(type):
    __slots__ = ()
    
    def __new__(cls, name, bases, namespace, slots=()):
        return super().__new__(cls, name, bases, namespace)
        
    def __init__(cls, name, bases, namespace, slots=()):
        namespace['__slots__'] = slots
        super().__init__(name, bases, namespace)
        
        original_new = cls.__new__
        
        def my_new(cls, *args, **kwargs):
            try: return cls._instance
            except AttributeError:
                cls._instance = original_new(cls, *args, **kwargs)
                return cls._instance
                
        cls.__new__ = staticmethod(my_new)
        
class NotLoaded(metaclass=SingletonMeta):

    def __str__(self):
        return 'Not Loaded'

    def __repr__(self):
        return '<NotLoaded>'

    def __bool__(self):
        return False

    def __hash__(self):
        return hash(type(self).__name__)


NotLoaded = NotLoaded()


class ConfigValuesView(collections.abc.ValuesView):
    def __repr__(self):
        return ''.join([type(self).__name__, '(', repr(tuple(self)), ')'])


class ConfigKeysView(collections.abc.KeysView):
    def __repr__(self):
        return ''.join([type(self).__name__, '(', repr(set(self)), ')'])


class ConfigItemsView(collections.abc.ItemsView):
    def __repr__(self):
        return ''.join([type(self).__name__, '(', repr(tuple(self)), ')'])


class ConfigMeta(abc.ABCMeta):
    __slots__ = ()

    @staticmethod
    def config_dir(self):
        "Return dir(self)."

        my_vars = set(self)
        skips = self.bad_names | my_vars

        yield from (
            attr
            for attr in dir(type(self))
            if (
                attr not in skips and
                not (
                    attr.startswith('_') and
                    not attr.startswith('__') and
                    hasattr(self, attr[1:])
                ) and hasattr(self, attr)
            )
        )

        yield from my_vars
    
    @classmethod
    def __prepare__(metacls, name, bases, *, slots=None, bad_names=None):
        if slots is None:
            slots = ()
            
        if bad_names is None:
            bad_names = set()
            
        return {
            '__slots__': tuple(
                attr
                if not attr.startswith('__')
                else ''.join(['_', name, attr])
                for attr in slots
            ),
            '__dir__': metacls.config_dir,
            '__bad_names__': tuple({
                attr
                if not attr.startswith('__')
                else ''.join(['_', name, attr])
                for attr in bad_names
            } | {'__bad_names__', 'bad_names'} | {
                attr
                for base in bases
                for attr in getattr(base, '__bad_names__', ())
            }),
            'bad_names': property(
                lambda s: frozenset(getattr(s, '__bad_names__'))
            )
        }
        
    def __new__(cls, name, bases, namespace, **kwargs):
        return super().__new__(cls, name, bases, namespace)
        
    def __init__(cls, name, bases, namespace, **kwargs):
        super().__init__(name, bases, namespace)

class BaseConfig(
    collections.Mapping,
    metaclass=ConfigMeta,
    slots=(
        '__attr_data',
        '__attr_func',
    ),
    bad_names={
        '_simple_get_',
        '_loadable_get_',
        '_setable_get_',
        '_setable_set_',
        '_attr_data_',
        '_attr_func_',
        '_set_attr',
        '_reset_attr',
        '_abc_cache',
        '_abc_negative_cache',
        '_abc_negative_cache_version',
        '_abc_registry',
        '__abstractmethods__',
        '__factory_subclass',
        '__delattr__',
        '__attr_data',
        '__attr_func',
        '__gen_keys',
        '__gen_items',
    }
):
    def __new__(cls, *args, **kwargs):
        """
        Constructs a new instance. This functions like a factory, and will
        make a dummy subclass of the class before sending to
        :py:meth:`__init__`, in order to ensure that properties (attributes)
        do not bleed across instances of the class.
        """

        if hasattr(cls, '__factory_subclass'):
            return super().__new__(*args, **kwargs)

        else:
            new_cls_name = cls.__name__
            new_cls = type(new_cls_name, (cls, ), {
                '__slots__': cls.__slots__,
                '__module__': '.'.join([
                    cls.__module__,
                    cls.__name__,
                    'subclass'
                ]),
                '__factory_subclass': True,
                '__doc__': '\n'.join([
                    'Factory-generated specialized subclass.'.format(
                        name=cls.__name__
                    ),
                    cls.__doc__ if cls.__doc__ is not None else ''
                ])
            })
            return super().__new__(new_cls)

    def __init__(self, *, attrs):
        if not attrs:
            return

        data, funcs, attrs = zip(*[
            (
                attr['name'],
                (attr['name'], attr['func'] if 'func' in attr else None),
                {
                    key: value
                    for key, value in attr.items()
                    if key != 'func'
                }
            )
            for attr in attrs
        ])
        self._attr_data_ = data
        funcs = dict(item for item in funcs if item is not None)
        self._attr_func_ = funcs.keys()
        list(
            itertools.starmap(
                setattr,
                (
                    (self.__attr_func, key, value)
                    for key, value in funcs.items()
                    if value is not None
                )
            )
        )
        list(map(lambda a: self._set_attr(**a), attrs))

    @property
    def _attr_data_(self):
        "Special property containing the memoized data."
        try:
            return self.__attr_data

        except AttributeError:
            self.__attr_data = type(
                ''.join([type(self).__name__, 'EmptyData']),
                (),
                {
                    '__module__': type(self).__module__,
                    '__slots__': ()
                }
            )()
            return self.__attr_data

    @_attr_data_.setter
    def _attr_data_(self, slots):
        """
        Does not work as expected, makes an empty object with a new __slots__
        definition.
        """
        self.__attr_data = type(
            ''.join([type(self).__name__, 'Data']),
            (),
            {
                '__module__': type(self).__module__,
                '__slots__': tuple(set(slots))
            }
        )()

    @property
    def _attr_func_(self):
        "Special property containing functions to be lazily-evaluated."

        try:
            return self.__attr_func

        except AttributeError:
            self.__attr_func = type(
                ''.join([type(self).__name__, 'EmptyFuncs']),
                (),
                {
                    '__module__': type(self).__module__,
                    '__slots__': ()
                }
            )()
            return self.__attr_func

    @_attr_func_.setter
    def _attr_func_(self, slots):
        """
        Does not work as expected, makes an empty object with a new __slots__
        definition.
        """

        self.__attr_func = type(
            ''.join([type(self).__name__, 'Funcs']),
            (),
            {
                '__module__': type(self).__module__,
                '__slots__': tuple(set(slots))
            }
        )()

    @staticmethod
    def _simple_get_(name, self):
        "Used to read evaluated & memoized attributes."

        return getattr(self._attr_data_, name)

    @staticmethod
    def _loadable_get_(name, self):
        "Used to lazily-evaluate & memoize an attribute."

        func = getattr(self._attr_func_, name)
        ret = func()
        setattr(self._attr_data_, name, ret)
        setattr(
            type(self),
            name,
            property(
                functools.partial(self._simple_get_, name)
            )
        )
        delattr(self._attr_func_, name)
        return ret

    @staticmethod
    def _setable_get_(name, self):
        "Used to raise an exception for attributes unable to be evaluated yet."

        raise AttributeError(
            "'{typename}' object has no attribute '{name}'".format(
                typename=type(self).__name__,
                name=name
            )
        )

    @staticmethod
    def _setable_set_(name, self, func):
        "Used to set the attribute a single time using the given function."

        setattr(self._attr_data_, name, func())

        if hasattr(self._attr_func_, name):
            delattr(self._attr_func_, name)

        setattr(
            type(self),
            name,
            property(
                functools.partial(self._simple_get_, name)
            )
        )

    def _set_attr(self, name, doc=None, preload=False):
        "Initially sets up an attribute."

        if doc is None:
            doc = 'The {name} attribute.'.format(name=name)

        if not hasattr(self._attr_func_, name):
            attr_prop = property(
                functools.partial(self._setable_get_, name),
                functools.partial(self._setable_set_, name),
                doc=doc
            )

        elif preload:
            func = getattr(self._attr_func_, name)
            setattr(self._attr_data_, name, func())
            delattr(self._attr_func_, name)
            attr_prop = property(
                functools.partial(self._simple_get_, name),
                doc=doc
            )

        else:
            attr_prop = property(
                functools.partial(self._loadable_get_, name),
                doc=doc
            )

        setattr(type(self), name, attr_prop)

    def _reset_attr(self, name, func=None, doc=None, preload=False):
        "Resets an attribute (or adds a new attribute) to be lazily-evaluated."

        keys = set(self)
        if name not in keys:
            try:
                data, funcs = zip(*[
                    (
                        (
                            key, (
                                getattr(self._attr_data_, key)
                                if hasattr(self._attr_data_, key)
                                else None
                            )
                        ),
                        (
                            key, (
                                getattr(self._attr_func_, key)
                                if hasattr(self._attr_func_, key)
                                else None
                            )
                        ),
                    )
                    for key in keys
                ])

                keys.add(name)
                self._attr_data_ = keys
                self._attr_func_ = keys

                [
                    setattr(self._attr_data_, key,  value)
                    for key, value in data
                    if value is not None
                ]
                [
                    setattr(self._attr_func_, key,  value)
                    for key, value in funcs
                    if value is not None
                ]

            except ValueError:
                keys.add(name)
                self._attr_data_ = keys
                self._attr_func_ = keys

        if hasattr(self._attr_data_, name):
            delattr(self._attr_data_, name)

        if func is not None:
            setattr(self._attr_func_, name, func)

        elif hasattr(self._attr_func_, name):
            delattr(self._attr_func_, name)

        self._set_attr(name, doc, preload)

    def __gen_keys(self):
        yield from sorted(
            key
            for key in (
                set(
                    self._attr_func_.__slots__
                ) | set(
                    self._attr_data_.__slots__
                )
            )
            if hasattr(self._attr_func_, key) or hasattr(self._attr_data_, key)
        )

    def __gen_items(self):
        yield from (
            (key, getattr(self._attr_data_, key, NotLoaded))
            for key in self.__gen_keys()
        )

    def __hash__(self):
        structure = (type(self).__name__,) + tuple(
            sorted(
                set(self._attr_data_.__slots__) |
                set(self._attr_func_.__slots__)
            )
        )
        return hash(structure)

    @property
    def __dict__(self):
        return types.MappingProxyType(dict(self.__gen_items()))

    def __repr__(self):
        "Return repr(self)."

        return repr(dict(self.__gen_items()))

    def __getitem__(self, key):
        "Return self[key]."

        return getattr(self, key)

    def __setitem__(self, key, value):
        raise TypeError(
            "'{name}' object does not support item assignment".format(
                name=type(self).__name__
            )
        )

    def __delitem__(self, key):
        raise TypeError(
            "'{name}' object does not support item deletion".format(
                name=type(self).__name__
            )
        )

    def __contains__(self, key):
        "Return key in self."

        return key in set(self.__gen_keys())

    def __str__(self):
        "Return str(self)."

        return str(dict(self.__gen_items()))

    def __sizeof__(self):
        "Return sys.getsizeof(self)."

        return sys.getsizeof(vars(self))

    def __len__(self):
        "Return len(self)."

        return len(tuple(self.__gen_keys()))

    def __iter__(self):
        "Return iter(self)."

        yield from self.__gen_keys()

    def __eq__(self, other):
        "Return self==other."

        return vars(self) == other

    def __ne__(self, other):
        "Return self!=other."
        return vars(self) != other

    def keys(self):
        """
        Returns a set-like object providing a view of the config object's
        keys.
        """

        return ConfigKeysView(self)

    def values(self):
        """
        Returns a set-like object providing a view of the config object's
        values.
        """

        return ConfigValuesView(self)

    def items(self):
        """
        Returns a set-like object providing a view of the config object's
        items.
        """

        return ConfigItemsView(self)

    def copy(self):
        "D.copy() -> a shallow copy of D"

        return copy.copy(self)

    def __copy__(self):
        "For use with the :py:func:`copy.copy` function."
        return copy.copy(dict(self.__gen_items()))

    def get(self, key, default=None):
        "D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None."

        return getattr(self, key, default)

    def __deepcopy__(self, memo):
        "For use with the :py:func:`copy.deepcopy` function."
        try:
            return memo[id(self)]

        except KeyError:
            memo[id(self)] = unpack_element(self, memo=memo)
            return memo[id(self)]

    @functools.lru_cache(maxsize=128)
    def get_path(self, *path):
        ret = self
        for key in path:
            ret = ret[key]

        return ret

    def __getstate__(self):
        return {
            key: value
            for key, value in self.__gen_items()
            if value is not NotLoaded
        }

    def __setstate__(self, state):
        for key, value in state.items():
            setattr(self._attr_data_, key)
            setattr(
                type(self),
                key,
                property(functools.partial(self._simple_get_, key))
            )

            try:
                delattr(self._attr_func_, key)

            except AttributeError:
                pass

    @abc.abstractmethod
    def __reduce__(self):
        pass

class DictConfig(BaseConfig):
    def __init__(self, source, extra_attrs=None):
        if extra_attrs is None:
            extra_attrs = []

        super().__init__(
            attrs=[
                {
                    'name': key,
                    'func': functools.partial(parse_element, value),
                    'preload': True
                }
                for key, value in source.items()
            ] + extra_attrs
        )

    def __reduce__(self):
        return (DictConfig, (copy.deepcopy(self), ), self.__getstate__())

            
class MainConfig(BaseConfig):
    """
    Class used by :py:mod:`xdh.config`, the module itself is replaced with an
    instance of this class.
    """
    
    def __init__(self):
        super().__init__(
            attrs=[
                {
                    'name': 'Base',
                    'func': lambda: BaseConfig,
                    'doc': BaseConfig.__doc__,
                    'preload': True
                },
                
                {
                    'name': 'Dict',
                    'func': lambda: DictConfig,
                    'doc': DictConfig.__doc__,
                    'preload': True
                },
                
                {
                    'name': 'to_config',
                    'func': lambda: parse_element,
                    'doc': parse_element.__doc__,
                    'preload': True
                },
                
                {
                    'name': 'from_config',
                    'func': lambda: unpack_element,
                    'doc': unpack_element.__doc__,
                    'preload': True
                },
            ]
        )
        
    def __reduce__(self):
        return (MainConfig, (), self.__getstate__())