import numpy as np

alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def compile(filename):
    file = CodeFile(filename)

class CodeFile:
    def __init__(self, filename):
        self.filename = filename
        with open(self.filename) as f:
            self.text = f.readlines()

        self.text = list(map(lambda x: x.removesuffix("\n"), self.text))

        self.code_blocks = []
        self.find_code_blocks()

        self.arrows = []
        self.find_arrows()

        self.write()

    def find(self, string):
        pass

    def get_char(self, x, y):
        if 0 <= y < len(self.text):
            if 0 <= x < len(self.text[y]):
                return self.text[y][x]

        return " "

    def find_code_blocks(self):
        for y, line in enumerate(self.text):
            chars_left = 0
            for x in range(len(line)):
                if chars_left > 0:
                    chars_left -= 1
                    continue
                char = self.get_char(x, y)
                if char == "{":
                    l = 1
                    depth = 1
                    string = None
                    while not depth == 0:
                        if self.get_char(x+l, y) == "{" and string is None:
                            depth += 1
                        elif self.get_char(x+l, y) == "}" and string is None:
                            depth -= 1
                        elif self.get_char(x+l, y) == '"':
                            if string is None:
                                string = '"'
                            elif string == '"':
                                string = None
                        elif self.get_char(x+l, y) == "'":
                            if string is None:
                                string = "'"
                            elif string == "'":
                                string = None
                        l += 1

                    chars_left = l - 1

                    self.code_blocks.append(CodeBlock(line[x:x+l], x, y))


    def find_arrows(self):
        for y, line in enumerate(self.text):
            for x in range(len(line)):
                if not self.in_code_block(x, y):
                    char = self.get_char(x, y)
                    if char in "><^v":
                        self.arrows.append(Arrow((x, y), self))

    def in_code_block(self, x, y):
        for block in self.code_blocks:
            if x in block.range and y == block.y:
                return True
        return False

    def find_start(self):
        for block in self.code_blocks:
            if block.code == "start":
                return block

    def arrows_from(self, x, y):
        arrows = []
        for arrow in self.arrows:
            if arrow.start[0] == x and arrow.start[1] == y:
                arrows.append(arrow)
        return arrows

    def arrows_from_block(self, block):
        arrows = []
        for arrow in self.arrows:
            if arrow.start[0] in block.range and arrow.start[1] == block.y:
                arrows.append(arrow)
        return arrows

    def block_at(self, x, y):
        for block in self.code_blocks:
            if x in block.range and y == block.y:
                return block


    def write(self):
        dest = self.filename.removesuffix(".pyf")
        dest = dest + ".py"
        dest = "out/" + dest

        text = ""
        block = self.find_start()
        while len(self.arrows_from_block(block)) > 0:
            block = self.block_at(*self.arrows_from_block(block)[0].to)
            text += block.code + "\n"

        with open(dest, "w") as f:
            f.write(text)

class CodeBlock:
    def __init__(self, line, x, y):
        self.line = line
        self.len = len(line)
        self.code = line[1:-1]
        self.code = self.code.strip()
        self.x = x
        self.y = y
        self.end = self.len + self.x
        self.range = range(self.x, self.end)

class Arrow:
    def __init__(self, end, file):
        self.file = file
        self.end = np.array(end)
        char = self.get_char(end[0], end[1])
        if char == ">":
            self.direction = np.array((1, 0))
        elif char == "<":
            self.direction = np.array((-1, 0))
        elif char == "^":
            self.direction = np.array((0, -1))
        elif char == "v":
            self.direction = np.array((0, 1))

        self.to = self.end + self.direction

        self.find_start()

    def get_char(self, x, y):
        return self.file.get_char(x, y)

    def find_start(self):
        found = False
        current_direction = self.direction
        start = np.copy(self.end)
        while not found:
            start -= current_direction
            if self.file.in_code_block(start[0], start[1]):
                found = True
            else:
                char = self.get_char(start[0], start[1])
                if char == "|":
                    assert current_direction[0] == 0

                elif char == "-":
                    assert current_direction[1] == 0

                elif char == "*":
                    possible_directions = []
                    if current_direction[0] == 0:
                        possible_directions.append(np.array((1, 0)))
                        possible_directions.append(np.array((-1, 0)))
                    else:
                        possible_directions.append(np.array((0, 1)))
                        possible_directions.append(np.array((0, -1)))

                    for direction in possible_directions:
                        p = start - direction
                        if self.get_char(p[0], p[1]) != " ":
                            current_direction = direction
                            break

                else:
                    raise Exception("Invalid character")

        self.start = start

