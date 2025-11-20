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
                If, And, Or, Not, Implies, PbEq, Xor, sat, unknown,
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
    
    args = parse_command()
    nrow = len(C)
    ncol = len(C[0])
    num_solutions = 0

    while slv.check() == sat:
        mdl = slv.model()
        Cbool, Estr, Pbool, _ = evaluate_model(mdl, C, H, V, P, R)
        verify(grid, Cbool, allow_weak=True)

        # Safe checks for matplotlib and fontsize
        use_matplotlib = getattr(args, "matplotlib", False)
        fontsize = getattr(args, "fontsize", 12)

        if use_matplotlib:
            print_matplotlib(grid, Cbool, Estr, Pbool, fontsize=fontsize)
        else:
            print_unicode(grid, Cbool)

        num_solutions += 1
        print(f"# Found solution {num_solutions}")

        # Safe check for slimit
        slimit = getattr(args, "slimit", None)
        if slimit is not None and num_solutions >= slimit:
            break

        # Block the current solution
        block = [C[i][j] != is_true(mdl.eval(C[i][j], model_completion=True))
                 for i in range(nrow) for j in range(ncol)]
        slv.add(Or(*block))

    if num_solutions == 0:
        print("# No solution found")
    else:
        print(f"# Total solutions found: {num_solutions}")

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
                    R: Sequence[Sequence[BoolRef]]) -> None:
    """Encode puzzle."""
    nrow = len(C)
    ncol = len(C[0])

    # Root constraints: exactly one root cell.
    slv.add(PbEq([(R[i][j], 1) for i in range(nrow) for j in range(ncol)], 1))

    for i in range(nrow):
        for j in range(ncol):

            # If cell has a clue, it cannot be shaded.
            if grid[i][j] is not None:
                slv.add(And(C[i][j], True))
                if grid[i][j] != '?':
                    # Number of shaded cells visible from clue cell is equal to clue.
                    clue = IntVal(grid[i][j])
                    numLeft = IntVal(0)
                    numRight = IntVal(0)
                    numUp = IntVal(0)
                    numDown = IntVal(0)
                    y = j
                    blocked = BoolVal(False)
                    while(y > 0):
                        numLeft = numLeft + If(And(Not(C[i][y-1]), Not(blocked)), IntVal(1), IntVal(0))
                        blocked = Or(blocked, C[i][y-1])
                        y = y - 1
                    y = j
                    blocked = BoolVal(False)
                    while(y < ncol - 1):
                        numRight = If(And(Not(C[i][y+1]), Not(blocked)), numRight + IntVal(1), numRight)
                        blocked = Or(blocked, C[i][y+1])
                        y = y + 1
                    x = i
                    blocked = BoolVal(False)
                    while(x > 0):
                        numUp = If(And(Not(C[x-1][j]), Not(blocked)), numUp + IntVal(1), numUp)
                        blocked = Or(blocked, C[x-1][j])
                        x = x - 1
                    x = i
                    blocked = BoolVal(False)
                    while(x < nrow - 1):
                        numDown = If(And(Not(C[x+1][j]), Not(blocked)), numDown + IntVal(1), numDown)
                        blocked = Or(blocked, C[x+1][j])
                        x = x + 1
                    
                    slv.add(clue == numLeft + numRight + numUp + numDown)                    

            # Root constraints
            absentH = And(Not(H[i][j][0]), Not(H[i][j][1]))
            absentV = And(Not(V[i][j][0]), Not(V[i][j][1]))
            slv.add(Implies(R[i][j], Not(C[i][j])))
            slv.add(Implies(R[i][j], And(absentH, absentV)))

            # Legality defined first to help solver
            legalH = Or(Not(H[i][j][0]), Not(H[i][j][1]))
            legalV = Or(Not(V[i][j][0]), Not(V[i][j][1]))
            legal = And(legalH, legalV)
            slv.add(legal)

            # No 2x2 shaded areas.
            if i < nrow - 1 and j < ncol - 1:
                slv.add(Not(And(Not(C[i][j]), Not(C[i+1][j]), Not(C[i][j+1]), Not(C[i+1][j+1]))))

            # If cell is shaded and not the root, exactly one of horizontal or vertical arrow is present
            slv.add(Implies(And(Not(C[i][j]), Not(R[i][j])), PbEq([(H[i][j][0], 1), (H[i][j][1], 1), (V[i][j][0], 1), (V[i][j][1], 1)], 1)))

            # Prevent two cells from pointing to each other
            # Prevent out of bounds arrows
            # Ensure that parent link points to an unshaded cell
            if j > 0:
                slv.add(Implies(H[i][j][0], Not(H[i][j-1][1])))
                slv.add(Implies(And(Not(C[i][j]), H[i][j][0]), Not(C[i][j-1])))
            else:
                slv.add(Not(H[i][j][0]))
            if j < ncol - 1:
                slv.add(Implies(H[i][j][1], Not(H[i][j+1][0])))
                slv.add(Implies(And(Not(C[i][j]), H[i][j][1]), Not(C[i][j+1])))
            else:
                slv.add(Not(H[i][j][1]))
            if i > 0:
                slv.add(Implies(V[i][j][1], Not(V[i-1][j][0])))
                slv.add(Implies(And(Not(C[i][j]), V[i][j][1]), Not(C[i-1][j])))
            else:
                slv.add(Not(V[i][j][1]))
            if i < nrow - 1:
                slv.add(Implies(V[i][j][0], Not(V[i+1][j][1])))
                slv.add(Implies(And(Not(C[i][j]), V[i][j][0]), Not(C[i+1][j])))
            else:
                slv.add(Not(V[i][j][0]))

            #Parity constraints
            if j > 0 and j < ncol - 1:
                rightright = Implies(And(H[i][j-1][1], H[i][j][1]), P[i][j-1] == P[i][j])
                leftleft = Implies(And(H[i][j+1][0], H[i][j][0]), P[i][j+1] == P[i][j])
                slv.add(And(rightright, leftleft))
            if i > 0 and i < nrow - 1:
                downdown = Implies(And(V[i-1][j][0], V[i][j][0]), P[i-1][j] == P[i][j])
                upup = Implies(And(V[i+1][j][1], V[i][j][1]), P[i+1][j] == P[i][j])
                slv.add(And(downdown, upup))
            if j < ncol - 1 and i > 0:
                leftup = Implies(And(H[i][j+1][0], V[i][j][1]), P[i][j+1] == P[i][j])
                downright = Implies(And(V[i-1][j][0], H[i][j][1]), P[i-1][j] == P[i][j])
                slv.add(And(leftup, downright))
            if i < nrow - 1 and j > 0:
                upleft = Implies(And(V[i+1][j][1], H[i][j][0]), P[i+1][j] == P[i][j])
                rightdown = Implies(And(H[i][j-1][1], V[i][j][0]), P[i][j-1] == P[i][j])
                slv.add(And(upleft, rightdown))
            if i > 0 and j > 0:
                downleft = Implies(And(V[i-1][j][0], H[i][j][0]), P[i-1][j] == P[i][j])
                ### Constraint for changing parity ###
                rightup = Implies(And(H[i][j-1][1], V[i][j][1]), P[i][j-1] != P[i][j])
                slv.add(And(downleft, rightup))
            if j < ncol - 1 and i < nrow - 1:
                leftdown = Implies(And(H[i][j+1][0], V[i][j][0]), P[i][j+1] == P[i][j])
                ### Constraint for changing parity ###
                upright = Implies(And(V[i+1][j][1], H[i][j][1]), P[i+1][j] != P[i][j])
                slv.add(And(leftdown, upright))


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
    C = [[Bool(f"C_{i}_{j}") for j in range(ncol)] for i in range(nrow)] # add definition

    # For each arrow:
    # (false,false) means "absent."
    # (false,true)  means "pointing up or right."
    # (true,false)  means "pointing down or left."
    # (true,true)   is forbidden.

    # Horizontal edges.
    H = [[[Bool(f'H_{i}_{j}_{k}') for k in range(2)] for j in range(ncol)] for i in range(nrow)] # add definition
    # Vertical edges.
    V = [[[Bool(f'V_{i}_{j}_{k}') for k in range(2)] for j in range(ncol)] for i in range(nrow)] # add definition

    # Turn parity variables.
    P = [[Bool(f"P_{i}_{j}") for j in range(ncol)] for i in range(nrow)] # add definition

    # Root variables.
    R = [[Bool(f"R_{i}_{j}") for j in range(ncol)] for i in range(nrow)] # add definition

    add_constraints(grid, slv, C, H, V, P, R)

    if args.verbose > 1:
        for a in slv.assertions():
            print(a)

    print(comment, 'Encoding time: {0:.4} s'.format(time.process_time() - starttime))

    solve_and_print(grid, slv, C, H, V, P, R)

    print(comment, 'CPU time: {0:.4} s'.format(time.process_time() - starttime))
