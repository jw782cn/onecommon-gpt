
# ('S_N3atbPCA1hsEIsRn', 'C_5e57c484d8d24b788d3e13577b8617ef')

import sys
sys.path.append("fns")

from context import get_ctx
from shapes import is_triangle, is_line, is_square
from spatial import all_close, are_above, are_below, are_right, are_left
from spatial import are_above_left, are_above_right, are_below_right, are_below_left
from spatial import are_middle
from spatial import get_top, get_bottom, get_right, get_left
from spatial import get_top_right, get_top_left, get_bottom_right, get_bottom_left
from spatial import get_middle
from color import is_dark, is_grey, is_light, lightest, darkest, same_color, different_color, are_darker, are_lighter
from size import is_large, is_small, is_medium, largest, smallest, same_size, different_size, are_larger, are_smaller
from iterators import get1idxs, get2idxs, get3idxs
from lists import add
import numpy as np
from functools import partial


def get_ctx():
    ctx = np.array([[-0.765, -0.33, 0.6666666666666666, 0.9066666666666666], [-0.575, -0.76, 0.0, -0.24], [0.565, 0.085, -1.0, 0.9866666666666667], [-0.83, 0.405, 0.0, -0.6], [-0.365, 0.035, 0.3333333333333333, -0.88], [0.785, -0.025, 0.0, 0.30666666666666664], [0.59, 0.5, -0.6666666666666666, -0.22666666666666666]])
    return ctx



idxs = np.arange(7)

# New.
ctx = get_ctx()
state = []

# Them: Got a triangle of 3 light grey dots.
def turn(state):
    # New question.
    results = []
    for x,y,z in get3idxs(idxs):
        if is_triangle([x,y,z], ctx) and all(map(partial(is_light, ctx=ctx), [x,y,z])):
            results.append(np.array([x,y,z]))
    return results
state = turn(state)
# End.

# You: Could be. One on right is largest with a small gray on top??
def turn(state):
    # Follow up question.
    results = []
    for result in state:
        if (largest(result, ctx) == get_right(result, ctx)).all() and is_small(get_top(result, ctx), ctx):
            results.append(result)
    return results
state = turn(state)
# End.

# Them: Nevermind. Do you see a pair of dark dots? One with another above and to the right of it? Same size as well.
def turn(state):
    # New question.
    results = []
    for result in get2idxs(idxs):
        if (
            all_close(result, ctx)
            and all(map(partial(is_dark, ctx=ctx), result))
            and are_right(result[1], result[0], ctx)
            and are_above(result[1], result[0], ctx)
            and same_size(result, ctx)
        ):
            results.append(result)
    return results
state = turn(state)
# End.

# You: No.
def turn(state):
    # New question.
    results = []
    return results
state = turn(state)
# End.

# Them: What about a large medium grey dot?
def turn(state):
    # New question.
    results = []
    for dot in get1idxs(idxs):
        if is_large(dot, ctx):
            results.append(dot)
    return results
state = turn(state)
# End.

# You: Is there a small black one next to it?
def turn(state):
    # Follow up question, new dot.
    results = []
    for result in state:
        for dot in get1idxs(idxs):
            if is_small(dot, ctx) and is_dark(dot, ctx) and all_close(add(result, dot), ctx) and not are_middle(dot, result, ctx):
                results.append(add(result, dot))
    return results
state = turn(state)
# End.

# Them: No. Do you see three dots in a diagonal line, where the top left dot is light, middle dot is grey, and bottom right dot is dark?
def turn(state):
    # New question.
    results = []
    for x, y, z in get3idxs(idxs):
        if (
            is_line([x,y,z], ctx)
            and x == get_top_left([x, y, z], ctx)
            and is_light(x, ctx)
            and are_middle([y], [x,y,z], ctx)
            and is_grey(y, ctx)
            and z == get_bottom_right([x, y, z], ctx)
            and is_dark(z, ctx)
        ):
            results.append(np.array([x,y,z]))
    return results
state = turn(state)
# End.

# You: Yes. Is the top one close to the middle one?
def turn(state):
    # Follow up question.
    results = []
    for result in state:
        if all_close([get_top(result, ctx), get_middle(result, ctx)], ctx):
            results.append(result)
    return results
state = turn(state)
# End.

# Them: Yes, let's select the large one. <selection>.
def select(state):
    # Select a dot.
    results = []
    for result in state:
        for dot in result:
            if is_large([dot], ctx):
                results.append(np.array([dot]))
    return results
state = select(state)
# End.

# New.
ctx = get_ctx()
state = []

# You: Do you see a large black dot on the bottom left?
def turn(state):
    # New question.
    results = []
    for dot in get1idxs(idxs):
        if is_large(dot, ctx) and is_dark(dot, ctx) and are_below_left(dot, None, ctx):
            results.append(dot)
    return results
state = turn(state)
# End.
 
# Them: I see a large black dot next to two small dots. We have different views though.
def turn(state):
    # New question.
    results = []
    for x,y,z in get3idxs(idxs):
        if all_close(np.array([x,y,z]), ctx) and is_large(x, ctx) and is_dark(z, ctx) and is_small(y, ctx) and is_small(z, ctx):
            results.append(np.array([x,y,z]))
    return results
state = turn(state)
# End.

# You: Select the larges one.
def turn(state):
    # Follow up question.
    results = []
    for result in state:
        results.append(get_largest(result, ctx))
    return results
state = turn(state)
# End.
 
# Them: Okay.
def turn(state):
    # No op.
    return state
state = turn(state)
# End.
 
# You: Okay. <selection>.
def select(state):
    # Select a dot.
    return state
state = select(state)
# End.


# New.
dots = get_ctx()
state = []

# Them: I have a light grey small dot next to a medium grey medium dot.
def turn(state):
    # New question.
    results = []
    for x,y in get2idxs(dots):
        if all_close(np.array([x,y]), dots) and is_light(x, dots) and is_small(x, dots) and is_medium(y, dots) and is_grey(y, dots):
            results.append(np.array([x,y]))
    return results
state = turn(state)


print([x.tolist() for x in state])
# state: num_candidates x size x feats=4
# dots: 7 x feats=4
# heuristic: take first candidate state[0]
"""
if state:
    print(state[0].tolist())
else:
    print("None")
"""