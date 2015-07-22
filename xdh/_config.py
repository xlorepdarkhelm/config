import abc
import builtins
import collections.abc
import copy
import functools
import gzip
import itertools
import sys

class NotLoaded:
    def __new__(cls, *args, **kwargs):
        try:
            return cls.__instance

        except AttributeError:
            cls.__instance = super().__new__(cls, *args, **kwargs)
            return cls.__instance

    def __str__(self):
        return 'Not Loaded'

    def __repr__(self):
        return '<NotLoaded>'

    def __bool__(self):
        return False

    def __hash__(self):
        return hash(type(self).__name__)


NotLoaded = NotLoaded()


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

class BaseConfig(collections.Mapping, metaclass=abc.ABCMeta):
    def __gen_valid_keys(self):
        yield from (
            key
            for key in (
                set(self._attr_func.__slots__) | set(self._attr_data.__slots__)
            )
            if hasattr(self._attr_func, key) or hasattr(self._attr_data, key)
        )
    
    def __gen_unloaded_items(self):
        yield from (
            (key, getattr(self._attr_data, key, NotLoaded))
            for key in self.__gen_valid_keys()
        )

    def __gen_loaded_items(self):
        yield from (
            (key, getattr(self, key))
            for key in self.__gen_valid_keys()
        )

    @property
    def __dict__(self):
        "Return vars(self)."

        entries = dict(self.__gen_unloaded_items())

        try:
            return dict(vars(super()).items(), **entries)

        except TypeError:
            return entries
        
    def __repr__(self):
        "Return repr(self)."

        return repr(vars(self))

    def __getitem__(self, key):
        "Return self[key]."

        return getattr(self, key)

    def __contains__(self, key):
        "Return key in self."

        return key in vars(self)

    def __str__(self):
        "Return str(self)."

        return str(vars(self))

    def __sizeof__(self):
        "Return sys.getsizeof(self)."

        return sys.getsizeof(vars(self))

    def __len__(self):
        "Return len(self)."

        return len(vars(self))

    def __iter__(self):
        "Return iter(self)."

        yield from vars(self)

    def __eq__(self, other):
        "Return self==other."

        return vars(self) == other

    def __ne__(self, other):
        "Return self!=other."
        return vars(self) != other

    def keys(self):
        """
        Returns a DictKeys object providing a view of the config object's
        keys.
        """

        return dict(self.__gen_unloaded_items()).keys()

    def values(self):
        """
        Returns a DictValues object providing a view of the config object's
        values.
        """

        return dict(self.__gen_loaded_items()).values()

    def items(self):
        """
        Returns a DictItems object providing a view of the config object's
        items.
        """

        return dict(self.__gen_loaded_items()).items()

    def __dir__(self):
        "Return dir(self)."

        my_vars = set(vars(self))
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
        self._attr_data = data
        funcs = dict(item for item in funcs if item is not None)
        self._attr_func = funcs.keys()
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
    def bad_names(self):
        """
        A set containing strings of attributes & methods for the class that
        should not be included in dir(self).
        """

        try:
            return frozenset(self.__bad_names)

        except AttributeError:
            self.bad_names = {
                'bad_names',
                '_simple_get_',
                '_loadable_get_',
                '_setable_get_',
                '_setable_set_',
                '_attr_data',
                '_attr_func',
            } | {
                ''.join(['_BaseConfig', attr])
                for attr in {
                    '__bad_names',
                    '__attr_data',
                    '__attr_func',
                    '__gen_valid_keys',
                    '__gen_unloaded_items',
                    '__gen_loaded_items',
                }
            }

            return frozenset(self.__bad_names)

    @bad_names.setter
    def bad_names(self, new_bad_names):
        self.__bad_names = tuple(new_bad_names)

    def copy(self):
        "D.copy() -> a shallow copy of D"

        return copy.copy(self)
        
    def __copy__(self):
        return copy.copy(vars(self))

    def get(self, key, default=None):
        "D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None."

        return getattr(self, key, default)

    def __deepcopy__(self, memo):

        try:
            return memo[id(self)]
            
        except KeyError:
            memo[id(self)] = unpack_element(self, memo=memo)
            return memo[id(self)]


    @property
    def _attr_data(self):
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

    @_attr_data.setter
    def _attr_data(self, data):
        self.__attr_data = type(
            ''.join([type(self).__name__, 'Data']),
            (),
            {
                '__module__': type(self).__module__,
                '__slots__': tuple(set(data))
            }
        )()

    @property
    def _attr_func(self):
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

    @_attr_func.setter
    def _attr_func(self, data):
        self.__attr_func = type(
            ''.join([type(self).__name__, 'Funcs']),
            (),
            {
                '__module__': type(self).__module__,
                '__slots__': tuple(set(data))
            }
        )()

    @staticmethod
    def _simple_get_(name, self):
        return getattr(self._attr_data, name)

    @staticmethod
    def _loadable_get_(name, self):
        func = getattr(self._attr_func, name)
        ret = func()
        setattr(self._attr_data, name, ret)
        setattr(
            type(self),
            name,
            property(
                functools.partial(self._simple_get_, name)
            )
        )
        delattr(self._attr_func, name)
        return ret

    @staticmethod
    def _setable_get_(name, self):
        raise AttributeError(
            "'{typename}' object has no attribute '{name}'".format(
                typename=type(self).__name__,
                name=name
            )
        )

    @staticmethod
    def _setable_set_(name, self, func):
        setattr(self._attr_func, name, func)
        setattr(
            type(self),
            name,
            property(
                functools.partial(self._loadable_get_, name)
            )
        )
        if hasattr(self._attr_data, name):
            delattr(self._attr_data, name)

    def _set_attr(self, name, doc=None):
        if doc is None:
            doc = 'The {name} attribute.'.format(name=name)

        if not hasattr(self._attr_func, name):
            attr_func = property(
                functools.partial(self._setable_get_, name),
                functools.partial(self._setable_set_, name),
                doc=doc
            )

        else:
            attr_func = property(
                functools.partial(self._loadable_get_, name),
                doc=doc
            )

        setattr(type(self), name, attr_func)

    def _reset_attr(self, name, func=None, doc=None):
        if hasattr(self._attr_data, name):
            delattr(self._attr_data, name)

        if func is not None:
            setattr(self._attr_func, name, func)

        elif hasattr(self._attr_func, name):
            delattr(self._attr_func, name)

        self._set_attr(name, doc)

    def get_path(self, *path):
        ret = self
        for key in path:
            ret = ret[key]

        return ret
        
    def __getstate__(self):
        ret = {
            key: value
            for key, value in self.__gen_unloaded_items()
            if value is not NotLoaded
        }
        
    def __setstate__(self):
        for key, value in state.items():
            setattr(self._attr_Data, key, value)
            setattr(
                type(self),
                key,
                property(functools,partial(self._simple_get_, key))
            )
            
            try:
                delattr(self._attr_func, key)
                
            except AttributeError:
                pass
            
    @abc.abstractmethod
    def __reduce__(self):
        pass


class DictConfig(BaseConfig):
    def __init__(self, source):
        super().__init__(
            attrs=[
                {
                    'name': key,
                    'func': functools.partial(parse_element, value),
                }
                for key, value in source.items()
            ]
        )
        
    def __reduce__(self):
        return (DictConfig, (self.deepcopy(), ), self.__getstate__())

            
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
                    'doc': BaseConfig.__doc__
                },
                
                {
                    'name': 'to_config',
                    'func': lambda: parse_element,
                    'doc': parse_element.__doc__
                },
                
                {
                    'name': 'from_config',
                    'func': lambda: unpack_element,
                    'doc': unpack_element.__doc__
                },
            ]
        )
        
    def __reduce__(self):
        return (MainConfig, (), self.__getstate__())