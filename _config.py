import sys

NOT_LOADED = '<Not Loaded>'

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
        
    def __iter___(self):
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