"""Functions to verify Canal View solutions."""

from typing import Sequence

def get_neighbors(current: tuple[int,int],
                  C: Sequence[Sequence[bool]]) -> list[tuple[int,int]]:
    """Collect (shaded) neighbors of current."""
    nrow = len(C)
    ncol = len(C[0])

    i, j = current
    nbors = list()
    if i > 0 and not C[i-1][j]:
        nbors.append((i-1,j,))
    if i < nrow-1 and not C[i+1][j]:
        nbors.append((i+1,j,))
    if j > 0 and not C[i][j-1]:
        nbors.append((i,j-1,))
    if j < ncol-1 and not C[i][j+1]:
        nbors.append((i,j+1,))

    return nbors

def visible_canal(i: int, j: int,
                  C: Sequence[Sequence[bool]]) -> int:
    """Count visible canal cell from (i,j)."""
    nrow = len(C)
    ncol = len(C[0])
    visible = 0

    for k in range(i-1,-1,-1): # going up
        if not C[k][j]:
            visible += 1
        else:
            break

    for k in range(i+1,nrow): # going down
        if not C[k][j]:
            visible += 1
        else:
            break

    for k in range(j-1,-1,-1): # going left
        if not C[i][k]:
            visible += 1
        else:
            break

    for k in range(j+1,ncol): # going right
        if not C[i][k]:
            visible += 1
        else:
            break

    return visible

def find_first_shaded(C: Sequence[Sequence[bool]]) -> tuple[int,int]:
    """Return coordinates of first shaded square."""
    nrow = len(C)
    ncol = len(C[0])

    for i in range(nrow):
        for j in range(ncol):
            if not C[i][j]:
                return (i,j)

    raise ValueError('No shaded square!')

def verify(grid: Sequence[Sequence[int]],
           C: Sequence[Sequence[bool]],
           allow_weak: bool = False) -> None:
    """Verify solution to Canal View puzzle."""
    nrow = len(grid)
    ncol = len(grid[0])

    # No 2x2 region is entirely shaded.
    for i in range(nrow-1):
        for j in range(ncol-1):
            if not (C[i][j] or C[i][j+1] or C[i+1][j] or C[i+1][j+1]):
                raise ValueError(f'Shaded 2x2 with upper-left corner at ({i+1},{j+1})')

    for i in range(nrow):
        for j in range(ncol):
            clue = grid[i][j]
            if clue > -2:
                if not C[i][j]:
                    raise ValueError(f'r{i+1}c{j+1} is shaded though it has a clue')
                if clue >= 0:
                    visible = visible_canal(i, j, C)
                    if visible != clue:
                        raise ValueError(f'{visible} canal squares visible from r{i+1}c{j+1} instead of {clue}')

    # Count shaded cells in the whole grid.
    totalcount = 0
    for i in range(nrow):
        count = sum([not C[i][j] for j in range(ncol)])
        totalcount += count

    # We allow no shaded cells if all constraints are satisfied.
    if totalcount == 0:
        return

    root = find_first_shaded(C)

    # Check reachability of all shaded cells from chosen root.
    if not allow_weak:
        reached = set()
        work = {root}

        while len(work) > 0:
            current = work.pop()
            reached.add(current)
            for cell in get_neighbors(current, C):
                if cell not in reached:
                    work.add(cell)

        if len(reached) != totalcount:
            raise ValueError(f'reached {len(reached)} cells instead of {totalcount}')
