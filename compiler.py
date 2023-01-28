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
                        if self.get_char(x+l-1, y) == "\\":
                            l += 1
                            continue

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

                        if x + l >= len(line):
                            raise Exception("Code block not closed")

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
        if block.simple:
            for arrow in self.arrows:
                if arrow.start[0] in block.range and arrow.start[1] == block.y:
                    arrows.append(arrow)
        else:
            for arrow in self.arrows:
                if arrow.start[0] in block.sections[-1] and arrow.start[1] == block.y:
                    arrows.append(arrow)

        return arrows

    def arrows_from_section(self, block, index):
        arrows = []
        for arrow in self.arrows:
            if arrow.start[0] in block.sections[index] and arrow.start[1] == block.y:
                arrows.append(arrow)
        return arrows

    def arrows_to_range(self, x, y):
        arrows = []
        for arrow in self.arrows:
            if arrow.to[0] in x and arrow.to[1] == y:
                arrows.append(arrow)
        return arrows

    def block_at(self, x, y):
        for block in self.code_blocks:
            if x in block.range and y == block.y:
                return block

    def resolve_tree(self, block):
        if block.simple:
            code = self.resolve_inserts(block) + "\n"
            arrows = self.arrows_from_block(block)
            if len(arrows) > 0:
                code += self.resolve_tree(self.block_at(*arrows[0].to))
            return code
        else:
            code = ""
            for i, code_block in enumerate(self.resolve_inserts(block)[:-1]):
                code += code_block + ":\n"
                code += indent(self.resolve_tree(self.block_at(*self.arrows_from_section(block, i)[0].to))) + "\n"

            code += self.resolve_tree(self.block_at(*self.arrows_from_section(block, -1)[0].to)) + "\n"

            return code


    def resolve_inserts(self, block):
        code = block.code
        if not block.simple:
            code = "\n".join(block.code)
        index = 0
        for r in block.insert_ranges:
            while code[index] != "_":
                index += 1

            arrows = self.arrows_to_range(r, block.y)
            if len(arrows) > 0:
                insert_block = self.block_at(*arrows[0].start)
                insert_block.parse(force_simple=True)
                insert = self.resolve_inserts(insert_block)
                code = code[:index] + insert + code[index+len(r):]
            index += len(r)

        if not block.simple:
            code = code.split("\n")

        return code



    def write(self):
        dest = self.filename.removesuffix(".pyf")
        dest = dest + ".py"
        dest = "out/" + dest

        block = self.find_start()
        block = self.block_at(*self.arrows_from_block(block)[0].to)

        text = self.resolve_tree(block)

        with open(dest, "w") as f:
            f.write(text)

class CodeBlock:
    def __init__(self, line, x, y):
        self.line = line
        self.len = len(line)
        #self.code = line[1:-1]
        #self.code = self.code.strip()
        self.x = x
        self.y = y
        self.end = self.len + self.x
        self.range = range(self.x, self.end)
        self.insert_ranges = find_insert_ranges(self.line, self.x)
        self.parse()

    def parse(self, force_simple=False):
        code = self.line
        no_strings = remove_strings(code)
        semi_colons = [i for i, char in enumerate(no_strings) if char == ";"]
        if len(semi_colons) == 0 or force_simple:
            self.simple = True
            code = code.removeprefix("{").removesuffix("}")
            code = code.strip()
            self.code = code
        else:
            self.simple = False
            self.code = []
            start = 0
            for semi_colon in semi_colons:
                self.code.append(code[start:semi_colon])
                start = semi_colon + 1
            self.code.append(code[start:])

            self.code[0] = self.code[0].removeprefix("{")
            self.code[-1] = self.code[-1].removesuffix("}")
            self.code = list(map(lambda x: x.strip(), self.code))

            semi_colons.insert(0, -1)
            semi_colons.append(len(code))

            self.sections = [range(self.x+i+1, self.x+j) for i, j in zip(semi_colons[:-1], semi_colons[1:])]


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
                    raise Exception(f"Invalid character {char} at {start + 1}")

        self.start = start


def remove_strings(code):
    no_strings = ""
    string = None
    for i, char in enumerate(code):
        if i > 0 and code[i-1] == "\\":
            no_strings += char
            continue

        if string is None:
            if char == '"':
                string = '"'
            elif char == "'":
                string = "'"
        elif char == string:
            string = None

        if string is None:
            no_strings += char
        else:
            no_strings += " "

    return no_strings


def indent(code):
    lines = code.splitlines()
    lines = map(lambda x: "    "  + x, lines)
    return "\n".join(lines)


def find_insert_ranges(line, offset=0):
    ranges = []
    start = None
    for i, char in enumerate(line):
        if start is None:
            if char == "_":
                start = i
        else:
            if char != "_":
                ranges.append(range(start+offset, i+offset))
                start = None

    return ranges