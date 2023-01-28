import compiler


def main():
    test = compiler.import_file("test.pyf")
    print(test.add(1, 2))
    print(test.sub(1, 2))

if __name__ == '__main__':
    main()