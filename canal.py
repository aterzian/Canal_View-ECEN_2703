"""Z3-based solver of Canal View puzzles.

Canal View is played on a rectangular grid.  The objective is to shade
some squares, subject to the constraints below.  The shaded squares
form the "canals."

1. Some squares are shaded.
2. The unshaded squares form a connected region.
3. No 2x2 areas are shaded.
4. The clues are never shaded.
5. A numeric clue in a square counts the canal squares visible
   from that square, both horizontally and vertically.

"""

from typing import Sequence, Optional

import sys
import time
from z3 import (Solver, Bool, BoolRef, BoolVal, # type: ignore
                If, And, Or, Not, PbEq, sat, unknown,
                ModelRef, is_true, simplify, ExprRef, IntVal)

from canalinputs import get_grid, check_grid, parse_command
from canaldisplay import print_unicode, print_matplotlib
from canalverify import verify


def evaluate_model(mdl: ModelRef,
                   C: Sequence[Sequence[BoolRef]],
                   H: Sequence[Sequence[Sequence[BoolRef]]],
                   V: Sequence[Sequence[Sequence[BoolRef]]],
                   P: Sequence[Sequence[BoolRef]],
                   R: Sequence[Sequence[BoolRef]]
                   ) -> tuple[list[list[bool]], list[list[str]], list[list[bool]], list[list[bool]]]:
    """Extract a complete solution from the solver's model."""
    nrow = len(C)
    ncol = len(C[0])
    Cbool = [[is_true(mdl.eval(C[i][j], model_completion=True))
              for j in range(ncol)] for i in range(nrow)]
    # Decode the H and V variables into "arrow" characters ('^','v','>','<'),
    # plus ' ' for no arrow and '?' for unexpected cases.
    Estr = [[(' ' if is_true(mdl.eval(And(absent_edge(H[i][j]), absent_edge(V[i][j])),
                                      model_completion=True)) else
              '^' if is_true(mdl.eval(And(up_right_edge(V[i][j]),absent_edge(H[i][j])),
                                      model_completion=True)) else
              'v' if is_true(mdl.eval(And(down_left_edge(V[i][j]),absent_edge(H[i][j])),
                                      model_completion=True)) else
              '>' if is_true(mdl.eval(And(up_right_edge(H[i][j]),absent_edge(V[i][j])),
                                      model_completion=True)) else
              '<' if is_true(mdl.eval(And(down_left_edge(H[i][j]),absent_edge(V[i][j])),
                                      model_completion=True)) else
              '?') for j in range(ncol)] for i in range(nrow)] 
    Pbool = [[is_true(mdl.eval(P[i][j], model_completion=True))
              for j in range(ncol)] for i in range(nrow)]
    Rbool = [[is_true(mdl.eval(R[i][j], model_completion=True))
              for j in range(ncol)] for i in range(nrow)]
    return Cbool, Estr, Pbool, Rbool

def solve_and_print(grid: Sequence[Sequence[int]],
                    slv: Solver,
                    C: Sequence[Sequence[BoolRef]],
                    H: Sequence[Sequence[Sequence[BoolRef]]],
                    V: Sequence[Sequence[Sequence[BoolRef]]],
                    P: Sequence[Sequence[BoolRef]],
                    R: Sequence[Sequence[BoolRef]]) -> None:
    """Compute and print solutions."""
    # Replace the exception with your code.
    raise NotImplementedError

def absent_edge(a: Sequence[BoolRef]) -> BoolRef:
    """Return constraint for absent edge."""
    return And(Not(a[0]), Not(a[1]))

def up_right_edge(a: Sequence[BoolRef]) -> BoolRef:
    """Return constraint for edge pointing up or right."""
    return a[1]

def down_left_edge(a: Sequence[BoolRef]) -> BoolRef:
    """Return constraint for edge pointing down or left."""
    return a[0]

def legal_edge(a: Sequence[BoolRef]) -> BoolRef:
    """Return constraint preventing forbidden edge value."""
    return Or(Not(a[0]), Not(a[1]))

def add_constraints(grid: Sequence[Sequence[int]],
                    slv: Solver,
                    C: Sequence[Sequence[BoolRef]],
                    H: Sequence[Sequence[Sequence[BoolRef]]],
                    V: Sequence[Sequence[Sequence[BoolRef]]],
                    P: Sequence[Sequence[BoolRef]],
                    R: BoolRef) -> None:
    """Encode puzzle."""
    # Replace the exception with your code.
    raise NotImplementedError

if __name__ == '__main__':

    starttime = time.process_time()

    sys.stdout.reconfigure(encoding='utf-8') # type: ignore

    args = parse_command()

    comment = '#'

    try:
        grid = get_grid(args.puzzle)
        check_grid(grid)
    except Exception as err:
        raise SystemExit(err)

    nrow = len(grid)
    ncol = len(grid[0])

    if args.drawonly:
        if args.matplotlib:
            print_matplotlib(grid, C=None, fontsize=args.fontsize)
        else:
            print_unicode(grid)
        raise SystemExit(0)

    slv = Solver()

    # C[i][j] is true if Cell (i,j) is unshaded.
    C = [] # add definition

    # For each arrow:
    # (false,false) means "absent."
    # (false,true)  means "pointing up or right."
    # (true,false)  means "pointing down or left."
    # (true,true)   is forbidden.

    # Horizontal edges.
    H = [] # add definition
    # Vertical edges.
    V = [] # add definition

    # Turn parity variables.
    P = [] # add definition

    # Root variables.
    R = [] # add definition

    add_constraints(grid, slv, C, H, V, P, R)

    if args.verbose > 1:
        for a in slv.assertions():
            print(a)

    print(comment, 'Encoding time: {0:.4} s'.format(time.process_time() - starttime))

    solve_and_print(grid, slv, C, H, V, P, R)

    print(comment, 'CPU time: {0:.4} s'.format(time.process_time() - starttime))
