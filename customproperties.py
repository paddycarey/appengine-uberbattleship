"""
    nacelle microframework
    Copyright Patrick Carey 2012
    See LICENSE file for licencing details
"""
from google.appengine.ext import db


class _DerivedProperty(db.Property):
    def __init__(self, derive_func, *args, **kwargs):
        super(_DerivedProperty, self).__init__(*args, **kwargs)
        self.derive_func = derive_func

    def __get__(self, model_instance, model_class):
        if model_instance is None:
            return self
        return self.derive_func(model_instance)

    def __set__(self, model_instance, value):
        pass
        #raise db.DerivedPropertyError("Cannot assign to a DerivedProperty")


def DerivedProperty(derive_func=None, *args, **kwargs):

    if derive_func:
        # Regular invocation
        return _DerivedProperty(derive_func, *args, **kwargs)
    else:
        # Decorator function
        def decorate(decorated_func):
            return _DerivedProperty(decorated_func, *args, **kwargs)
        return decorate
