import compiler


def main():
    test = compiler.import_file("test.pyf")
    print(test.add(1, 2))
    print(test.sub(1, 2))
    nestedbranch = compiler.import_file("tests/nestedbranch.pyf")
    square = nestedbranch.Square(5)
    print(square.area())

if __name__ == '__main__':
    main()