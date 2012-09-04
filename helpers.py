import random

ships = {
    'aircraft carrier': 5,
    'battleship': 4,
    'submarine': 3,
    'destroyer': 3,
    'patrol boat': 2,
}

directions = {
    0: lambda x, y: (x, y + 1),  # north
    1: lambda x, y: (x + 1, y),  # east
    2: lambda x, y: (x, y - 1),  # south
    3: lambda x, y: (x - 1, y),  # west
}


def generate_board(size):
    if not 7 < size < 200:
        raise Exception('Invalid board size, must be between 8 and 200')
    board = []
    for row in range(size):
        board.append([None for x in range(size)])
    return board


def is_collision(coords, ship_coords):

    for coord in ship_coords:
        if coord in coords:
            return True
    else:
        return False


def randomise_board(board, ship_compliment):
    raw_coords = []
    coords = []
    for ship_type, ship_length in ship_compliment.items():
        position_allowed = False
        while not position_allowed:
            direction = directions[random.randint(0, 3)]
            x_start = random.randint(0, len(board) - 1)
            y_start = random.randint(0, len(board) - 1)
            start_coords = (x_start, y_start)
            ship_coords = []
            prev_coords = start_coords
            for i in range(ship_length):
                x = prev_coords[0]
                y = prev_coords[1]
                ship_coords.append((x, y))
                prev_coords = direction(x, y)
            else:
                if (x >= 0 and x < (len(board) - 1)) and (y >= 0 and y < (len(board) - 1)):
                    if not is_collision(raw_coords, ship_coords):
                        position_allowed = True
                        coords.append([ship_type, ship_coords])
                        for coord in ship_coords:
                            board[coord[0]][coord[1]] = ship_type
                            raw_coords.append(coord)
    return board
