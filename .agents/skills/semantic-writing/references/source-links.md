# Source Links

Every reference to a location in a file is a link. Prose carries no unclickable location — no bare line number, no "in that switch".

## Path base

The base differs by destination, and getting it wrong breaks every link silently.

- Written into chat: relative to the workspace root.
- Written into a file: relative to that file's own directory.

A target outside every workspace folder does not resolve in chat. Write the plain path and line number rather than a link that cannot be followed.

## One line

[`raw codeline`](path/to/file#L<n>)

The display text is the source line itself, verbatim, less its leading indentation. The reader gets the code and its location in one object.

Non-contiguous locations are separate links; one anchor joining them with a comma does not resolve. The path never carries backticks, and when the path is the display text the two must match exactly.

## A run of lines

The fallback, taken only when no single line carries the point, because a fenced block cannot sit inside link text — link text is inline-only. Do not reach for HTML to work around this. Give the link, a colon, then the block:

[description](path/to/file#L<n>-L<m>):

```lang
def foo():
    pass
```

