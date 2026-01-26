#!/usr/bin/env python3

def find_fibonacci_numbers(count):
    """
    Finds the first 'count' Fibonacci numbers.

    Args:
        count (int): The number of Fibonacci numbers to generate.

    Returns:
        list: A list containing the first 'count' Fibonacci numbers.
    """
    if count <= 0:
        return []
    elif count == 1:
        return [0]

    fib_numbers = []
    a, b = 0, 1

    for _ in range(count):
        fib_numbers.append(a)
        next_fib = a + b
        a, b = b, next_fib

    return fib_numbers

# --- Main execution ---
if __name__ == "__main__":
    num_to_find = 10
    result = find_fibonacci_numbers(num_to_find)
    print(f"The first {num_to_find} Fibonacci numbers are: {result}")