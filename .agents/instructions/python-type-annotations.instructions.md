---
applyTo: '**/*.py'
---

# Python Type Annotations

Annotate the shape the data actually has. When the shape is unknown, investigate it — inspect real values, print keys and `type()`, read the producer — instead of widening the type.

## Baseline

Target Python 3.15+. Check `requires-python` in `pyproject.toml` first; follow the repo when it pins an older version.

Annotations evaluate lazily (PEP 649): forward references need no quotes, and `from __future__ import annotations` is obsolete. Quoting stays legal. To read annotations at runtime, call `annotationlib.get_annotations(obj, format=Format.FORWARDREF)`; `__annotations__` and `get_type_hints()` raise `NameError` on a name not yet defined.

## Unions

`Any`, `Union`, `Optional`, `cast`, and bare `dict`/`list`/`tuple` are banned. Take generics from builtins and abstract types from `collections.abc` (`list[int]`, `Callable[[int], str]`), not from `typing.List`, `typing.Callable`, or the other `typing` aliases deprecated since 3.9.

When "absent" must stay distinct from every real value, `None` included, mark it with a `sentinel` and name it in the union; `x is MISSING` then narrows it away. An `object()` marker has no type of its own, so the union widens to `object` and never narrows.

```python
class Foo: ...
class Bar: ...
MISSING = sentinel('MISSING')

x: Foo | Bar             # correct
x: Foo | None            # correct
x: Foo | None | MISSING  # correct — None is a real value; MISSING means absent
x: 'Foo | Bar'           # correct — quoting is legal, unnecessary
x: Union[Foo, Bar]       # wrong
x: Optional[Foo]         # wrong
x: Foo | object          # wrong — an object() marker swallows Foo
```

## Dicts

A `dict` with program-fixed keys is a record: declare it as a `@dataclass` or a `TypedDict` with `closed=True` — without it, a `TypedDict` means "at least these keys". Never `dict[str, Any]`. A key that may be absent is `NotRequired[T]`; `T | None` means the key is present and may hold `None`. Keyword arguments with fixed names are `**kwargs: Unpack[Opts]` over such a `TypedDict`.

When a payload varies by a tag field, write a discriminated union, narrow on the tag, and end with `assert_never` so an unhandled variant fails type checking:

```python
class TextEvent(TypedDict, closed=True):
    kind: Literal['text']
    body: str

class FileEvent(TypedDict, closed=True):
    kind: Literal['file']
    path: Path
    size: int

type Event = TextEvent | FileEvent

def describe(e: Event) -> str:
    match e['kind']:
        case 'text': return e['body']
        case 'file': return str(e['path'])
        case _: assert_never(e)
```

For values that are genuinely open-ended, cover the static envelope with a `@dataclass` or `TypedDict` and type the open leaf `object`, narrowing at the point of use. Unknown keys beside declared ones are the `TypedDict`'s `extra_items`, not a reason to fall back to `dict[str, ...]`:

```python
class Response(TypedDict, extra_items=object):  # top-level keys unknown at author time
    status: int
    headers: dict[str, str]
    extensions: dict[str, object]  # nested keys unknown at author time; narrow before use
```

Where an annotation is not structurally required, omit it and add `# type: ignore` — never `Any`. Keep each ignore on the narrowest line, with a rule code and a short reason when the cause is not obvious.

## Precision

- A closed set of strings is a `Literal` or `Enum`, not `str`.
- Identifiers that must not be confused are distinct `NewType`s.
- Validated and unvalidated values are distinct types, not one type plus a runtime check.
- A string that must not carry external input, such as SQL or a shell command, is `LiteralString`.
- Binary input is `collections.abc.Buffer` or an explicit union such as `bytes | bytearray`; `ByteString` is deprecated.
- Accept `Sequence`/`Mapping`/`Iterable` in parameters; return concrete `list`/`dict`.

## Constructs

- `def f[T](x: T) -> T`, `class Box[T = int]`, and `type Alias = ...` (PEP 695, 696), not `TypeVar`/`TypeAlias`.
- Type decorators with `ParamSpec`, never erasing the signature to `Callable[..., object]`: `def deco[**P, R](fn: Callable[P, R]) -> Callable[P, R]` keeps it, and `Concatenate` expresses an added or removed parameter.
- `Protocol` for "anything with this shape", not inheritance or an `isinstance` chain. Decorate each protocol checked with `isinstance` with `@runtime_checkable`; subclasses do not inherit it.
- `@deprecated` (from `warnings`) on retired APIs, so the type checker reports every caller; a `warnings.warn` call reports only at runtime.
- `Self` for fluent and factory returns; `@override` on intended overrides.
- `TypeIs` for custom narrowing; `TypeGuard` only when the negative branch must stay unnarrowed.
- `TypeForm[T]` for a parameter that receives a type expression (`int | None`, `list[int]`); `type[T]` only when it must be a class.
- `Final`, `ReadOnly`, and `frozendict` where mutation is not part of the contract.

