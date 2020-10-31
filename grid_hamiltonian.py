#!/usr/bin/env python3
from __future__ import annotations
from typing import NamedTuple
from enum import Enum

import random
import time
import sys

import ansi_term

# GRID_SIZE = (150, 50)  # w, h
# GRID_SIZE = (16, 10)  # w, h

WILSON_WALK_DELAY = 0.01
CYCLE_WALK_DELAY = 0.001

if len(sys.argv) == 3:
    GRID_SIZE = (int(sys.argv[1]), int(sys.argv[2]))
else:
    # TERM_SIZE = tuple(map(int, os.popen('stty size', 'r').read().split()))[::-1]
    term_size = ansi_term.get_term_size()
    GRID_SIZE = (term_size[0] - 3, term_size[1] - 4)


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @staticmethod
    def random_direction():
        return random.choice(list(Direction))


class GridField:
    direction: Direction
    previous: bool

    _repr_mapping = {
        Direction.UP: '↑',
        Direction.DOWN: '↓',
        Direction.LEFT: '←',
        Direction.RIGHT: '→',
        None: ' ',
    }

    def __init__(self, direction=None, previous=False):
        self.direction = direction
        self.previous = previous

    def __repr__(self):
        field_char = self._repr_mapping[self.direction]
        if self.previous:
            return ansi_term.Color.Dim.text(field_char)
            # return f"\033[2m{field_char}\033[0m"
        else:
            return field_char

    def empty(self):
        return self.direction is None


class Position(NamedTuple):
    x: int
    y: int

    def next_pos(self, direction):
        d = direction.value
        return Position(x=self.x + d[0], y=self.y + d[1])

    def equals(self, other: Position) -> bool:
        return self.x == other.x and self.y == other.y

    def equals_point(self, x: int, y: int) -> bool:
        return self.x == x and self.y == y

    @staticmethod
    def random_pos(width, height):
        return Position(x=random.randrange(width - 1), y=random.randrange(height - 1))

    @staticmethod
    def random_pos_left(grid):
        positions_left = []
        for y, row in enumerate(grid):
            for x, field in enumerate(row):
                if field.direction is None:
                    positions_left.append(Position(x, y))

        if len(positions_left) > 0:
            return random.choice(positions_left)
        else:
            return None


def make_grid(w, h, fill_factory):
    grid = []
    for i in range(h):
        grid.append(w * [fill_factory()])
    return grid


def print_grid(grid):
    grid_rows = [[str(field) for field in row] for row in grid]
    line = (2 + len(grid[0])) * '-'
    print(line)
    for row in grid_rows:
        print('|' + ''.join(row) + '|')
    print(line)


def mark_all_as_previous(grid, previous=True):
    for row in grid:
        for field in row:
            if field.direction is not None:
                field.previous = previous


def walk_path(grid, start_pos: Position, end_pos: Position):
    grid_height = len(grid)
    grid_width = len(grid[0])

    def next_random_neighbour(from_pos: Position):
        pos = Position(x=-1, y=-1)
        while pos.x < 0 or pos.x >= grid_width or pos.y < 0 or pos.y >= grid_height:
            d = Direction.random_direction()
            pos = from_pos.next_pos(d)
        return (pos, d)

    pos = start_pos
    while True:
        # print('WALK', pos.x, pos.y, grid[pos.y][pos.x])

        if pos.equals(end_pos) or grid[pos.y][pos.x].previous:
            end_pos = Position(x=-1, y=-1)
            next_start_pos = Position.random_pos_left(grid)

            # print('\033[0;0H')
            ansi_term.set_cursor_position(0, 0)
            print_grid(grid)
            # print('next_start_pos:', next_start_pos)
            sys.stdout.flush()
            time.sleep(WILSON_WALK_DELAY)

            mark_all_as_previous(grid)
            if next_start_pos is None:
                break
            else:
                pos = next_start_pos

        elif grid[pos.y][pos.x].empty():
            next_pos, next_dir = next_random_neighbour(pos)
            # print(f'{(next_pos.x, next_pos.y)} pos {pos} next_dir {next_dir}')
            grid[pos.y][pos.x] = GridField(direction=next_dir)
            pos = next_pos

        else:
            erase_loop(grid, pos, GridField())


def erase_loop(grid, start_pos: Position, replace_with=None):
    pos = start_pos

    while not grid[pos.y][pos.x].empty() :
        # print('ERASE', pos.x, pos.y, grid[pos.y][pos.x])
        field = grid[pos.y][pos.x]
        grid[pos.y][pos.x] = replace_with
        pos = pos.next_pos(field.direction)


class FieldWalls(NamedTuple):
    north: bool  # ↑
    south: bool  # ↓
    west: bool   # ←
    east: bool   # →

    @staticmethod
    def walls_from_field(grid, pos: Position):
        w, h = len(grid[0]), len(grid)
        field = grid[pos.y][pos.x]
        neighbour_n_dir = grid[pos.y - 1][pos.x].direction if pos.y > 0 else None
        neighbour_s_dir = grid[pos.y + 1][pos.x].direction if pos.y < h - 1 else None
        neighbour_w_dir = grid[pos.y][pos.x - 1].direction if pos.x > 0 else None
        neighbour_e_dir = grid[pos.y][pos.x + 1].direction if pos.x < w - 1 else None

        return FieldWalls(
            north=field.direction != Direction.UP and neighbour_n_dir != Direction.DOWN,
            south=field.direction != Direction.DOWN and neighbour_s_dir != Direction.UP,
            west=field.direction != Direction.LEFT and neighbour_w_dir != Direction.RIGHT,
            east=field.direction != Direction.RIGHT and neighbour_e_dir != Direction.LEFT,
        )


def hamiltonian_from_grid_walk(grid):
    grid_width, grid_height = len(grid[0]), len(grid)

    grid_walls = make_grid(grid_width, grid_height, lambda: None)
    for y, row in enumerate(grid):
        for x, field in enumerate(row):
            grid_walls[y][x] = FieldWalls.walls_from_field(grid, Position(x, y))

    # print('\n'.join(map(str, grid_walls)))

    cycle_grid = make_grid(2 * grid_width, 2 * grid_height, lambda: GridField())
    for y, row in enumerate(grid_walls):
        for x, walls in enumerate(row):
            n_field_dir = Direction.LEFT if walls.north else Direction.UP
            w_field_dir = Direction.DOWN if walls.west else Direction.LEFT
            s_field_dir = Direction.RIGHT if walls.south else Direction.DOWN
            e_field_dir = Direction.UP if walls.east else Direction.RIGHT

            cycle_grid[2 * y][2 * x + 1] = GridField(direction=n_field_dir)
            cycle_grid[2 * y][2 * x] = GridField(direction=w_field_dir)
            cycle_grid[2 * y + 1][2 * x] = GridField(direction=s_field_dir)
            cycle_grid[2 * y + 1][2 * x + 1] = GridField(direction=e_field_dir)

    return cycle_grid


def animate_cycle_grid(grid, start_pos, anim_delay=0.001):
    # print('\033[?25l')  # hide cursor
    ansi_term.Control.hide_cursor()
    orig_grid_height = len(grid) // 2
    pos = start_pos
    mark_all_as_previous(grid)
    # print_grid(grid)

    field = grid[start_pos.y][start_pos.x]
    while field.previous:
        field.previous = False
        pos = pos.next_pos(field.direction)
        field = grid[pos.y][pos.x]

        # print(f'\033[{orig_grid_height + 3};0H')
        ansi_term.set_cursor_position(0, orig_grid_height + 3)
        print_grid(grid)
        sys.stdout.flush()
        time.sleep(anim_delay)

    # print('\033[?25h')  # show cursor
    ansi_term.Control.show_cursor()
    assert pos.equals(start_pos)


if __name__ == '__main__':
    # print('\033[2J')
    # ansi_term.clear()
    ansi_term.Control.clear()
    print('GRID SIZE:', GRID_SIZE)

    grid = make_grid(*GRID_SIZE, lambda: GridField())
    start_pos = Position.random_pos(*GRID_SIZE)
    end_pos = Position.random_pos(*GRID_SIZE)
    walk_path(grid, start_pos, end_pos)

    # print_grid(grid)

    cycle_grid = hamiltonian_from_grid_walk(grid)
    # print_grid(cycle_grid)
    animate_cycle_grid(cycle_grid, Position(0, 0), CYCLE_WALK_DELAY)

    import itertools
    assert all([x.previous is False for x in list(itertools.chain.from_iterable(cycle_grid))])
    print('OK!')

    # print(f'Start: {start_pos}, end: {end_pos}')
