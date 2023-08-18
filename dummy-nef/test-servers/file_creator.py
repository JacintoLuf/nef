def create_text_file(filename, size_in_bytes):
    with open(filename, 'wb') as f:
        f.write(b' ' * (size_in_bytes-1))
        f.write(b'!')

if __name__ == "__main__":
    filename = "small_file.txt"
    size_in_bytes = 1024 * 100

    create_text_file(filename, size_in_bytes)
    print(f"File '{filename}' created with size {size_in_bytes} bytes.")

    filename = "medium_file.txt"
    size_in_bytes = 1024 * 1024 * 10

    create_text_file(filename, size_in_bytes)
    print(f"File '{filename}' created with size {size_in_bytes} bytes.")

    filename = "big_file.txt"
    size_in_bytes = 1024 * 1024 * 1024

    create_text_file(filename, size_in_bytes)
    print(f"File '{filename}' created with size {size_in_bytes} bytes.")