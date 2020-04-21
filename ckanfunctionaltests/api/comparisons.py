from collections.abc import Mapping, Sequence
from functools import lru_cache
from numbers import Number
import re
from types import MappingProxyType
from typing.re import Pattern


class RestrictedAny:
    """
    Analogous to mock.ANY, this class takes an arbitrary callable in its constructor and the returned instance will
    appear to "equal" anything that produces a truthy result when passed as an argument to the ``condition`` callable.

    Useful when wanting to assert the contents of a larger structure but be more flexible for certain members, e.g.

    # only care that second number is odd
    >>> (4, 5, 6,) == (4, RestrictedAny(lambda x: x % 2), 6,)
    True
    >>> (4, 9, 6,) == (4, RestrictedAny(lambda x: x % 2), 6,)
    True
    """
    def __init__(self, condition):
        self._condition = condition

    def __eq__(self, other):
        return self._condition(other)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._condition})"

    def __hash__(self):
        return None


class AnySupersetOf(RestrictedAny):
    def __new__(cls, subset, recursive=False, seq_norm_order=False):
        if isinstance(subset, Mapping):
            return AnySupersetOfMapping(subset, recursive=recursive, seq_norm_order=seq_norm_order)
        elif isinstance(subset, Sequence) and not isinstance(subset, (str, bytes)):
            return AnySupersetOfSeq(subset, recursive=recursive, seq_norm_order=seq_norm_order)
        else:
            return subset


class AnySupersetOfImpl(AnySupersetOf):
    "This class simply exists to reset the __new__ method for any AnySupersetOf implementations"
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)


class AnySupersetOfMapping(AnySupersetOfImpl):
    """
    Instance will appear to "equal" any dictionary-like object that is a "superset" of the constructor-supplied
    ``subset_dict``, i.e. will ignore any keys present in the dictionary in question but missing from the reference
    dict. e.g.

    >>> [{"a": 123, "b": 456, "less": "predictabananas"}, 789] == [AnySupersetOfMapping({"a": 123, "b": 456}), 789]
    True

    If constructed with the ``recursive`` option, this fuzzy equality behaviour will also be applied to any contained
    Mapping or any contained Sequence (using AnySupersetOfSeq), applied recursively.

    The ``seq_norm_order`` flag only applies to any recursively-discovered child sequences, and therefore has no
    meaning without ``recursive=True``.
    """
    def __init__(self, subset_dict, recursive=False, seq_norm_order=False):
        # take an immutable dict copy of supplied dict-like object
        self._subset_dict = MappingProxyType({
            k: AnySupersetOf(v, recursive=recursive, seq_norm_order=seq_norm_order) if recursive else v
            for k, v in subset_dict.items()
        })
        super().__init__(lambda other: (
            isinstance(other, Mapping)
            and self._subset_dict == {k: v for k, v in other.items() if k in self._subset_dict}
        ))

    def __repr__(self):
        return f"{self.__class__.__name__}({self._subset_dict})"


class AnySupersetOfSeq(AnySupersetOfImpl):
    """
    Instance will appear to "equal" any sequence that is a "superset" of the constructor-supplied ``subset_seq``,
    i.e. will ignore any items present in the sequence in question but missing from the reference sequence, This is
    done in an order-sensitive manner. e.g.

    >>> {"a": "b", "c": [1, 2, "three", None, 4.5]} == {"a": "b", "c": AnySupersetOfSeq(["three", 4.5])}
    True

    If constructed with the ``recursive`` option, this fuzzy equality behaviour will also be applied to any contained
    Sequence or any contained Mapping (using AnySupersetOfMapping), applied recursively.

    If constructed with the ``seq_norm_order`` option, will attempt to compare sequences in an order-insensitive way.
    This is done by sorting both sides of the comparison using the ``get_norm_order_key`` method as a key function. The
    default implementation of this looks for likely-stable, identifying keys in any child mappings it finds. It is not
    faultless as I realized that doing order-insensitive superset testing "perfectly" is equivalent to solving a
    bipartite graph matching problem, which is NP-complete. So this will have to do. Remember, we can't "just use sets"
    becuase it's likely the elements aren't hashable.
    """
    def __init__(self, subset_seq, recursive=False, seq_norm_order=False):
        self._seq_norm_order = seq_norm_order
        if self._seq_norm_order:
            subset_seq = tuple(sorted(subset_seq, key=self.get_norm_order_key))
        self._subset_seq = tuple(
            (AnySupersetOf(v, recursive=recursive, seq_norm_order=seq_norm_order) if recursive else v)
            for v in subset_seq
        )
        super().__init__(self._is_equal)

    def _is_equal(self, other):
        if not (isinstance(other, Sequence) and not isinstance(other, (str, bytes))):
            return False

        # this technique should work as long as `other` (the superset sequence doesn't have
        # any items with "funny" equality properties (like, say, another RestrictedAny)
        # because we don't perform any backtracking. we just attempt to do a parallel
        # iteration of the two sequences and see which one runs out first
        sub_iter = iter(self._subset_seq)
        try:
            current_sub = next(sub_iter)
        except StopIteration:
            # an empty sequence is a subsequence of anything
            return True

        if self._seq_norm_order:
            other = sorted(other, key=self.get_norm_order_key)

        for current_super in other:
            if current_sub == current_super:
                # excellent, we can continue advancing both iterators and assume any super
                # items we had skipped were superfluous
                try:
                    current_sub = next(sub_iter)
                except StopIteration:
                    # we've run out of items in the sub_iter, any items remaining in the super
                    # seq can be ignored
                    return True
            # else we simply advance the super iterator to see if *its* next item equals
            # current_sub
        else:
            # not all items in sub_iter were matched
            return False

    norm_order_mapping_keys = ("key", "name", "position",)
    norm_order_stringifiable_types = (str, bytes, bool, Number,)

    @classmethod
    def get_norm_order_key(cls, item):
        # all return values must be tuples of the form (int, str?) (the string being optional) to ensure their
        # comparability. the leading integer denotes which "category" of key this is. this is done so that keys
        # retrieved by different means end up segregated once sorted.
        key_categories_skipped = 0
        if isinstance(item, Mapping):
            return next(
                (
                    (i, str(item[k]))
                    for i, k in enumerate(cls.norm_order_mapping_keys, key_categories_skipped)
                    if k in item
                ),
                # for mappings with no matched keys
                (key_categories_skipped + len(cls.norm_order_mapping_keys),),
            )

        key_categories_skipped += len(cls.norm_order_mapping_keys) + 1

        return next(
            (
                (i, str(item))
                for i, _type in enumerate(cls.norm_order_stringifiable_types, key_categories_skipped)
                if isinstance(item, _type)
            ),
            # if the item is a more complex type than any of these, it's less likely it will have a stable string
            # representation (consider e.g. order of items in a dict which doesn't affect equality).
            # it's tempting to return a string representation of the item as a final effort, but it's better to return a
            # constant and hopefully allow the stability of the sorting algorithm keep all such items in their
            # originally returned order
            (key_categories_skipped + len(cls.norm_order_stringifiable_types),),
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({self._subset_seq})"


class AnyStringMatching(RestrictedAny):
    """
    Instance will appear to "equal" any string that matches the constructor-supplied regex pattern

    >>> {"a": "Metempsychosis", "b": "c"} == {"a": AnyStringMatching(r"m+.+psycho.*", flags=re.I), "b": "c"}
    True
    """
    _cached_re_compile = staticmethod(lru_cache(maxsize=32)(re.compile))

    def __init__(self, *args, **kwargs):
        """
        Construct an instance which will equal any string matching the supplied regex pattern. Supports all arguments
        recognized by ``re.compile``, alternatively accepts an existing regex pattern object as a single argument.
        """
        self._regex = (
            args[0]
            if len(args) == 1 and isinstance(args[0], Pattern)
            else self._cached_re_compile(*args, **kwargs)
        )
        super().__init__(lambda other: isinstance(other, (str, bytes)) and bool(self._regex.match(other)))

    def __repr__(self):
        return f"{self.__class__.__name__}({self._regex})"


class ExactIdentity(RestrictedAny):
    """
    Instance will appear to "equal" only to the exact object supplied at construction time.

    >>> x = []
    >>> (7, ExactIdentity(x),) == (7, x,)
    True
    >>> (7, ExactIdentity(x),) == (7, [],)
    False
    """
    def __init__(self, reference_object):
        self._reference_object = reference_object
        super().__init__(lambda other: self._reference_object is other)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._reference_object!r} @ {hex(id(self._reference_object))})"
