import builtins
import collections.abc
import functools
import sys

NOT_LOADED = '<Not Loaded>'

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

def unpack_element(elem):
    isinstance = builtins.isinstance
    
    if isinstance(elem, type):
        ret = elem
        
    elif isinstance(elem, BaseConfig):
        ret = {key: unpack_element(getattr(elem, key)) for key in elem}
        
    elif isinstance(elem, collections.abc.Mapping):
        ret = {key: unpack_element(value) for key, value in elem.items()}
        
    elif isinstance(elem, collections.abc.Set):
        ret = {unpack_element(value) for value in elem}
        
    elif not isinstance(elem, (str, bytes, bytearray)) and all(
        isinstance(elem, type_)
        for type_ in {
            collections.abc.Sized,
            collections.abc.Iterable,
            collections.abc.Container,
            collections.abc.Sequence
        }
    ):
        ret = [unpack_element(value) for value in elem]
        
    else:
        ret = elem
        
    return ret

class BaseConfig(collections.Mapping):
    @property
    def __dict__(self):
        try:
            ret = vars(super())
            
        except TypeError:
            ret = {}
            
        ret.update({
            entry: (
                self.__internal_dict[entry]
                if entry in self.__internal_dict
                else NOT_LOADED
            )
            for entry in self.__attr_set - self.bad_names
        })
        
        return ret
        
    def __repr__(self):
        return repr(vars(self))
        
    def __getitem__(self, key):
        ret = vars(self)[key]
        
        if ret == NOT_LOADED:
            ret = getattr(self, key)
            
        return ret
        
    def __contains__(self, key):
        return key in vars(self)
        
    def __str__(self):
        return str(vars(self))
        
    def __sizeof__(self):
        return sys.getsizeof(vars(self))
        
    def __len__(self):
        return len(vars(self))
        
    def __iter__(self):
        yield from vars(self)
        
    def __eq__(self, other):
        return vars(self) == other
        
    def __ne__(self, other):
        return vars(self) != other
        
    def keys(self):
        yield from self
        
    def values(self):
        yield from (self.get(key, NOT_LOADED) for key in self)

    def items(self):
        yield from (
            (
                key,
                self.get(key, NOT_LOADED)
            )
            for key in self
        )
        
    def __dir__(self):
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
                    'Facory-generated specialized subclass.',
                    cls.__doc__ if cls.__doc__ is not None else ''
                ])
            })
            return super().__new__(new_cls)
            
    @property
    def bad_names(self):
        try:
            return self.__data['bad_names']
            
        except KeyError:
            self.bad_names = {
                'bad_names',
                'register_attr'
            } | {
                ''.join(['__BaseConfig', attr])
                for attr in {
                    '__attr_data',
                    '__attr_set',
                    '__data',
                    '__internal_dict'
                }
            }
            
            return self.__data['bad_names']
    
    @bad_names.setter
    def bad_names(self, new_bad_names):
        self.__data['bad_names'] = new_bad_names
        
    def copy(self):
        return vars(self).copy()
        
    def get(self, key, default=None):
        return vars(self).get(key, default)

    def deepcopy(self):
        return unpack_element(self)
        
    @property
    def __data(self):
        try:
            return self.__attr_data
            
        except AttributeError:
            self.__attr_data = {}
            return self.__attr_data
            
    @property
    def __internal_dict(self):
        try:
            return self.__data['internal_dict']
            
        except KeyError:
            self.__data['internal_dict'] = {}
            return self.__data['internal_dict']
            
    @property
    def __attr_set(self):
        try:
            return self.__data['attr_set']
            
        except KeyError:
            self.__data['attr_set'] = set()
            return self.__data['attr_set']
            
    def _replace_attr(self, name, func, doc=None, setable=False):
        self._unregister_attr(name)
        self.register_attr(name, func, doc, setable)
        
    def _unregister_attr(self, name):
        delattr(type(self), name)
        self.__attr_set.discard(name)
        
        try:
            del self.__internal_dict[name]
            
        except KeyError:
            pass
        
    def register_attr(self, name, func, doc=None, setable=False):
        if doc is None:
            doc = ' '.join(['The', name, 'attribute.'])
            
        if setable:
            def get_(self):
                try:
                    return self.__internal_dict[name]
                    
                except KeyError:
                    raise AttributeError(
                        ' '.join([name, 'attribute does not exist'])
                    )
                    
            def set_(self, value):
                if name in self.__internal_dict:
                    raise AttributeError(
                        ' '.join(["can't change", name, 'attribute'])
                    )
                    
                self.__internal_dict[name] = func(value)
            
            attr_func = property(get_, set_, doc=doc)
        
        else:
            def get_(self):
                try:
                    return self.__internal_dict[name]
                    
                except KeyError:
                    self.__internal_dict[name] = func()
                    return self.__internal_dict[name]
                    
            attr_func = property(get_, doc=doc)
                
        setattr(type(self), name, attr_func)
        self.__attr_set.add(name)
        
    def get_path(self, *path):
        ret = self
        for key in path:
            ret = ret[key]
            
        return ret
        
class DictConfig(BaseConfig):
    def __init__(self, source):
        for name, value in source.items():
            self.register_attr(
                name,
                functools.partial(parse_epement, value)
            )
            
class MainConfig(BaseConfig):
    def __init__(self):
        super().__init__()
        
        self.register_attr('Base', lambda: BaseConfig, BaseConfig.__doc__)
        
        self.register_attr('Dict', lambda: DictConfig, DictConfig.__doc__)
        
        self.register_attr(
            'to_config',
            lambda: parse_element,
            parse_element.__doc__
        )