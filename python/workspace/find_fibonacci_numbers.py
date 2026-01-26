# Python script to find the first 10 Fibonacci numbers

def generate_fibonacci(n):
    fib_sequence = []
    a, b = 0, 1
    for _ in range(n):
        fib_sequence.append(a)
        a, b = b, a + b
    return fib_sequence

# Find the first 10 Fibonacci numbers
first_10_fibonacci = generate_fibonacci(10)

# Print the result
print("The first 10 Fibonacci numbers are:", first_10_fibonacci)