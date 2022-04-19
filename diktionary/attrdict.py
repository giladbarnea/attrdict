"""
python3 -m timeit -s 'from domain.attrdict import AttrDict' -s 'a=AttrDict(dict(b="c"))' 'a.b'
"""
import typing
from collections.abc import Mapping, Sequence
from typing import Dict
from functools import cache
NoneType = type(None)
PRIMITIVE_SCALAR_TYPES = {bool, str, int, float}
Annotation = typing.TypeVar('Annotation', bound=type)
T = typing.TypeVar('T')
Map = typing.TypeVar('Map', bound=Mapping)

class SimpleAttrDict(dict):
    """Does not do anything with type annotations"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self
    
    def __getattr__(self, key):
        return self[key]
    
    def __setattr__(self, key, value):
        self[key] = value
    
    def __delattr__(self, key):
        del self[key]
    
    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"
    
    
class AttrDict(dict):
    # def __repr__(self) -> str:
    #     return f"{self.__class__.__name__}({super().__repr__()})"

    @classmethod
    @cache
    def _safe_annotations(cls) -> Dict[str, typing.Type]:
        try:
            return cls.__annotations__
        except:
            return {}
    
    @classmethod
    # def _construct_from_annotation(cls, value: T, annotation: Annotation=None) -> Annotation[T]:
    def _construct_from_annotation(cls, value: T, annotation: Annotation=None):
        if value is None:
            return value
        # TODO (idea): cache annotation in PRIMITIVE_SCALAR_TYPES?
        if annotation in PRIMITIVE_SCALAR_TYPES:
            return value
        value_type = type(value)
        if value_type is dict:
            return cls._construct_mapping_from_annotation(value, annotation)
        if value_type in (list, tuple):
            return cls._construct_sequence_from_annotation(value, annotation)
        else:
            return cls._construct_scalar_from_annotation(value, annotation)

    @staticmethod
    def _construct_mapping_from_annotation(value: dict, annotation: typing.Type[Map]) -> Map:
        if isinstance(value, AttrDict):
            return value
        if not annotation:
            return AttrDict(**value)
        annotation_origin = typing.get_origin(annotation)
        if not annotation_origin:
            # e.g dict
            return annotation(**value)
        if annotation_origin is typing.Union:
            # e.g Optional[DnsSetting], or Union[DnsSetting, dict]
            annotation_args = typing.get_args(annotation)
            if not annotation_args:
                raise TypeError(f"Naked Union or Optional: {annotation}"
                                f"Define the type annotation with a variable, e.g Optional[str]")
            # value is not None, because None is not a Mapping
            first_truthy_annotation = None
            for annotation_arg in annotation_args:
                if annotation_arg is not NoneType:
                    if first_truthy_annotation is not None:
                        raise TypeError(f"Ambiguous Optional annotation: {annotation}. "
                                        f"Value is not None, can't infer which type is correct: {annotation_args}\n"
                                        f"Value: {value!r}")
                    first_truthy_annotation = annotation_arg
            return first_truthy_annotation(**value)
        else:
            # e.g Dict -> dict
            return annotation_origin(**value)

    @staticmethod
    @typing.overload
    def _construct_sequence_from_annotation(value: list, annotation: typing.Type[list]) -> list: ...
    @staticmethod
    @typing.overload
    def _construct_sequence_from_annotation(value: tuple, annotation: typing.Type[tuple]) -> tuple: ...
    @staticmethod
    def _construct_sequence_from_annotation(value: typing.Union[list, tuple], annotation: typing.Type[Sequence]) -> Sequence:
        value_type = type(value)
        if not annotation:
            return value_type(map(AttrDict._construct_from_annotation, value))
        # e.g rules: List[PortForwardingRuleDef] -> list
        annotation_origin = typing.get_origin(annotation)
        if not annotation_origin:
            # e.g rules: list[PortForwardingRuleDef]
            annotation_origin = value_type
        annotation_args = typing.get_args(annotation)
        if not annotation_args:
            # no type var; e.g rules: List
            return annotation_origin(map(AttrDict._construct_from_annotation, value))
        # e.g list[PortForwardingRuleDef] -> PortForwardingRuleDef
        annotation_arg, *more_annotation_args = annotation_args
        if more_annotation_args:
            raise TypeError(f"Ambiguous sequence annotation: {annotation}. "
                            f"Can't build a {annotation_origin} of {annotation_args}\n"
                            f"Value: {value!r}")
        return annotation_origin(map(annotation_arg, value))

    @staticmethod
    # def _construct_scalar_from_annotation(value: T, annotation: Annotation) -> Annotation[T]:
    def _construct_scalar_from_annotation(value: T, annotation: Annotation):
        if not annotation:
            return value
        # if annotation in PRIMITIVE_SCALAR_TYPES:
        #     return value
        annotation_origin = typing.get_origin(annotation)
        if not annotation_origin:
            return annotation(value)
        if annotation_origin in PRIMITIVE_SCALAR_TYPES:
            return value
        if annotation_origin is typing.Union:
            annotation_args = typing.get_args(annotation)
            if not annotation_args:
                raise TypeError(f"Naked Union or Optional: {annotation}"
                                f"Define the type annotation with a variable, e.g Optional[str]")
            first_truthy_annotation = None
            for annotation_arg in annotation_args:
                if annotation_arg is not NoneType:
                    if first_truthy_annotation is not None:
                        return value
                        # raise TypeError(f"Ambiguous Optional annotation: {annotation}. "
                        #                 f"Value is not None, can't infer which type is correct: {annotation_args}\n"
                        #                 f"Value: {value!r}")
                    first_truthy_annotation = annotation_arg
            return first_truthy_annotation(value)
        else:
            raise NotImplementedError(value, annotation, annotation_origin)

    def __getattr__(self, name: str):
        if name[0] == '_':
            return super().__getattr__(name)
        
        # TODO(perf): consider just 'if "__cache__" in self.__dict__', and setdefault later before returning
        __cache__ = self.__dict__.setdefault('__cache__', {})
        if __cache__:
            if name in __cache__:
                return __cache__[name]
        try:
            value = self[name]
        except KeyError:
            annotation = self._safe_annotations().get(name)
            if any(annotation_arg is NoneType for annotation_arg in typing.get_args(annotation)):
                __cache__[name] = None
                return None
            for supercls in self.__class__.__mro__[1:]:
                supercls_annotation = supercls.__annotations__.get(name)
                if any(annotation_arg is NoneType for annotation_arg in typing.get_args(supercls_annotation)):
                    __cache__[name] = None
                    return None
            raise AttributeError(name) from None

        annotation: typing.Type = self._safe_annotations().get(name)
        constructed = self._construct_from_annotation(value, annotation)
        __cache__[name] = constructed
        return constructed


    def __setattr__(self, name, value):
        self[name] = value
        __cache__ = self.__dict__.setdefault('__cache__', {})
        if __cache__:
            if name in __cache__:
                del __cache__[name]

    def __delattr__(self, name):
        del self[name]
        __cache__ = self.__dict__.setdefault('__cache__', {})
        if __cache__:
            if name in __cache__:
                del __cache__[name]
