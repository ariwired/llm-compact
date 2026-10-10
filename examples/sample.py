from __future__ import annotations

import os
from typing import Optional


def compute(a: int, b: int = 2, *args, **kwargs) -> int:
    total = a + b
    values = [1, 2, 3,]

    mapping = {'a': 1, "b": 2,}

    if total > 10 and not (a == b):
        total -= 1
    elif total < -5:
        total = - -total
    else:
        total = a if b else -1
    text = f"{a!r:>10} {mapping["a"]} {{literal}} {values[0]:{b}d}"
    raw = r"\d+  \w+"
    
    cont = 1 + \
        2
    return total + sum(values) + cont + len(text) + len(raw)


class Box:
    def __init__(self, v: Optional[int] = None):
        self.v = v

    @property
    def double(self) -> int:
        return (self.v or 0) * 2


lam = lambda x, *y: (x, y)

if (n := len("abc")) > 2:
    print(n, end = "")

x = 1 if True else 2
