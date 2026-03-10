"""
Management command to enrich unenriched problems with:
  1.  A full Markdown-style description (constraints, examples, approach hints)
  2.  Proper input/output test cases

Matching is done via keyword patterns on the normalised problem title.
Problems whose title doesn't match any known pattern are given a
sensible generic description derived from the raw title text.

Usage:
    python manage.py enrich_problems            # only enriches problems with empty test_cases
    python manage.py enrich_problems --force    # re-processes ALL problems
"""

import re
from django.core.management.base import BaseCommand
from learning.models import Problem


# ---------------------------------------------------------------------------
#  Pattern catalogue  –  (regex pattern, enrichment dict)
#  enrichment dict keys:
#    description : full markdown problem description (shown on left panel)
#    test_cases  : list of {"input": ..., "output": ...}
#    difficulty  : "EASY" / "MEDIUM" / "HARD"  (optional, keeps existing if absent)
# ---------------------------------------------------------------------------
PATTERNS = [

    # ── Leap Year ────────────────────────────────────────────────────────────
    (r'leap year', {
        "difficulty": "EASY",
        "description": """## Leap Year Checker

A **leap year** occurs:
- Every year **divisible by 4**
- **Except** century years (divisible by 100)
- **Unless** it is also divisible by 400

### Rules
| Condition | Leap Year? |
|-----------|-----------|
| Divisible by 400 | ✅ Yes |
| Divisible by 100 (but not 400) | ❌ No |
| Divisible by 4 (but not 100) | ✅ Yes |
| None of the above | ❌ No |

### Input Format
A single integer `year`.

### Output Format
Print `Leap Year` or `Not a Leap Year`.

### Constraints
- 1 ≤ year ≤ 9999

### Examples
```
Input:  2000
Output: Leap Year

Input:  1900
Output: Not a Leap Year

Input:  2024
Output: Leap Year
```""",
        "test_cases": [
            {"input": "2000", "output": "Leap Year"},
            {"input": "1900", "output": "Not a Leap Year"},
            {"input": "2024", "output": "Leap Year"},
            {"input": "2023", "output": "Not a Leap Year"},
        ]
    }),

    # ── Sum of Two Numbers ────────────────────────────────────────────────────
    (r'sum of (two|both|2)', {
        "difficulty": "EASY",
        "description": """## Sum of Two Numbers

Given two integers, compute and print their sum.

### Input Format
Two space-separated integers `a` and `b`.

### Output Format
Print the integer `a + b`.

### Constraints
- -10⁹ ≤ a, b ≤ 10⁹

### Examples
```
Input:  3 5
Output: 8

Input:  -4 10
Output: 6
```""",
        "test_cases": [
            {"input": "3 5",   "output": "8"},
            {"input": "-4 10", "output": "6"},
            {"input": "0 0",   "output": "0"},
        ]
    }),

    # ── Multiplication Table ──────────────────────────────────────────────────
    (r'multiplication table', {
        "difficulty": "EASY",
        "description": """## Multiplication Table

Print the multiplication table for a given number `n` from 1 to 10.

### Input Format
A single integer `n`.

### Output Format
Print 10 lines in the format: `n x i = result`

### Examples
```
Input: 5

Output:
5 x 1 = 5
5 x 2 = 10
...
5 x 10 = 50
```""",
        "test_cases": [
            {"input": "5",  "output": "5 x 1 = 5\n5 x 2 = 10\n5 x 3 = 15\n5 x 4 = 20\n5 x 5 = 25\n5 x 6 = 30\n5 x 7 = 35\n5 x 8 = 40\n5 x 9 = 45\n5 x 10 = 50"},
            {"input": "3",  "output": "3 x 1 = 3\n3 x 2 = 6\n3 x 3 = 9\n3 x 4 = 12\n3 x 5 = 15\n3 x 6 = 18\n3 x 7 = 21\n3 x 8 = 24\n3 x 9 = 27\n3 x 10 = 30"},
        ]
    }),

    # ── HCF / LCM ────────────────────────────────────────────────────────────
    (r'hcf|lcm', {
        "difficulty": "EASY",
        "description": """## HCF and LCM

Given two positive integers `a` and `b`:
- **HCF** (Highest Common Factor) is the largest number that divides both.
- **LCM** (Least Common Multiple) is the smallest number divisible by both.

**Formula:** `LCM(a, b) = (a × b) / HCF(a, b)`

### Input Format
Two space-separated integers `a b`.

### Output Format
```
HCF: <value>
LCM: <value>
```

### Examples
```
Input:  12 18
Output:
HCF: 6
LCM: 36
```""",
        "test_cases": [
            {"input": "12 18", "output": "HCF: 6\nLCM: 36"},
            {"input": "5 7",   "output": "HCF: 1\nLCM: 35"},
            {"input": "8 12",  "output": "HCF: 4\nLCM: 24"},
        ]
    }),

    # ── Even / Odd ────────────────────────────────────────────────────────────
    (r'even|odd', {
        "difficulty": "EASY",
        "description": """## Even or Odd

Determine whether a given integer is **even** or **odd**.

An integer is **even** if it is divisible by 2, and **odd** otherwise.

### Input Format
A single integer `n`.

### Output Format
Print either `Even` or `Odd`.

### Examples
```
Input:  4
Output: Even

Input:  7
Output: Odd
```""",
        "test_cases": [
            {"input": "4",  "output": "Even"},
            {"input": "7",  "output": "Odd"},
            {"input": "0",  "output": "Even"},
            {"input": "-3", "output": "Odd"},
        ]
    }),

    # ── Fibonacci ────────────────────────────────────────────────────────────
    (r'fibonacci', {
        "difficulty": "EASY",
        "description": """## Fibonacci Series

The **Fibonacci sequence** is a series where each number is the sum of the two preceding ones:

```
0, 1, 1, 2, 3, 5, 8, 13, 21, ...
```

### Input Format
A single integer `n` (number of terms to print).

### Output Format
Print the first `n` Fibonacci numbers separated by spaces.

### Constraints
- 1 ≤ n ≤ 50

### Examples
```
Input:  7
Output: 0 1 1 2 3 5 8

Input:  1
Output: 0
```""",
        "test_cases": [
            {"input": "7", "output": "0 1 1 2 3 5 8"},
            {"input": "1", "output": "0"},
            {"input": "5", "output": "0 1 1 2 3"},
        ]
    }),

    # ── Palindrome (string) ───────────────────────────────────────────────────
    (r'palindrome.*string|string.*palindrome', {
        "difficulty": "EASY",
        "description": """## String Palindrome

A **palindrome** is a string that reads the same forwards and backwards.

### Examples of Palindromes
- `racecar`  →  Palindrome ✅
- `madam`    →  Palindrome ✅
- `hello`    →  Not a Palindrome ❌

### Input Format
A single string `s` (no spaces).

### Output Format
Print `Palindrome` or `Not a Palindrome`.

### Constraints
- 1 ≤ |s| ≤ 1000
- String consists of lowercase English letters.

### Approach
Compare `s` with `reverse(s)`. If equal → Palindrome.
""",
        "test_cases": [
            {"input": "racecar", "output": "Palindrome"},
            {"input": "hello",   "output": "Not a Palindrome"},
            {"input": "madam",   "output": "Palindrome"},
            {"input": "a",       "output": "Palindrome"},
        ]
    }),

    # ── Armstrong Number ──────────────────────────────────────────────────────
    (r'armstrong', {
        "difficulty": "EASY",
        "description": """## Armstrong Number

An **Armstrong number** (also called narcissistic number) is a number that equals the sum of its own digits each raised to the power of the number of digits.

### Examples
- `153` → 1³ + 5³ + 3³ = 1 + 125 + 27 = **153** ✅
- `370` → 3³ + 7³ + 0³ = 27 + 343 + 0 = **370** ✅
- `123` → 1³ + 2³ + 3³ = 1 + 8 + 27 = 36 ≠ 123 ❌

### Input Format
Two integers `a b` (find Armstrong numbers from `a` to `b`).

### Output Format
Print all Armstrong numbers in range, one per line.

### Examples
```
Input:  100 500
Output:
153
370
371
407
```""",
        "test_cases": [
            {"input": "100 500", "output": "153\n370\n371\n407"},
            {"input": "1 9",     "output": "1\n2\n3\n4\n5\n6\n7\n8\n9"},
        ]
    }),

    # ── Area of Circle ────────────────────────────────────────────────────────
    (r'area of circle', {
        "difficulty": "EASY",
        "description": """## Area of Circle

Calculate the **area of a circle** given its radius `r`.

**Formula:** `Area = π × r²`

Use `π = 3.14159265358979` or `Math.PI`.

### Input Format
A single floating-point number `r` (radius).

### Output Format
Print the area rounded to **2 decimal places**.

### Examples
```
Input:  7
Output: 153.94

Input:  5
Output: 78.54
```""",
        "test_cases": [
            {"input": "7", "output": "153.94"},
            {"input": "5", "output": "78.54"},
            {"input": "1", "output": "3.14"},
        ]
    }),

    # ── Area of Triangle ──────────────────────────────────────────────────────
    (r'area of (triangle|isosceles)', {
        "difficulty": "EASY",
        "description": """## Area of Triangle

Calculate the **area of a triangle** using the base and height.

**Formula:** `Area = 0.5 × base × height`

### Input Format
Two floating-point numbers: `base height`.

### Output Format
Print the area rounded to **2 decimal places**.

### Examples
```
Input:  10 5
Output: 25.0

Input:  6 3
Output: 9.0
```""",
        "test_cases": [
            {"input": "10 5", "output": "25.0"},
            {"input": "6 3",  "output": "9.0"},
            {"input": "4 8",  "output": "16.0"},
        ]
    }),

    # ── Area of Rectangle ─────────────────────────────────────────────────────
    (r'area of rectangle', {
        "difficulty": "EASY",
        "description": """## Area of Rectangle

Calculate the **area** and **perimeter** of a rectangle given its length and width.

**Formulas:**
- `Area = length × width`
- `Perimeter = 2 × (length + width)`

### Input Format
Two floating-point numbers: `length width`.

### Output Format
```
Area: <value>
Perimeter: <value>
```

### Examples
```
Input:  5 3
Output:
Area: 15.0
Perimeter: 16.0
```""",
        "test_cases": [
            {"input": "5 3",   "output": "Area: 15.0\nPerimeter: 16.0"},
            {"input": "10 4",  "output": "Area: 40.0\nPerimeter: 28.0"},
        ]
    }),

    # ── Simple Interest ───────────────────────────────────────────────────────
    (r'simple interest|principal.*time.*rate', {
        "difficulty": "EASY",
        "description": """## Simple Interest Calculator

Calculate **Simple Interest (SI)** given Principal, Time, and Rate.

**Formula:** `SI = (P × T × R) / 100`

### Input Format
Three numbers on separate lines:
```
P (Principal)
T (Time in years)
R (Rate of interest %)
```

### Output Format
Print `Simple Interest = <value>` (2 decimal places).

### Examples
```
Input:
1000
2
5

Output: Simple Interest = 100.00
```""",
        "test_cases": [
            {"input": "1000\n2\n5",   "output": "Simple Interest = 100.00"},
            {"input": "5000\n3\n8",   "output": "Simple Interest = 1200.00"},
            {"input": "10000\n1\n10", "output": "Simple Interest = 1000.00"},
        ]
    }),

    # ── Calculator / Operator ────────────────────────────────────────────────
    (r'calculator|operator.*\+.*-|\+.*-.*\*', {
        "difficulty": "EASY",
        "description": """## Simple Calculator

Build a simple calculator that takes two numbers and an operator (+, -, *, /) and prints the result.

### Input Format
```
num1 operator num2
```

### Output Format
Print the computed result (2 decimal places for division).

### Constraints
- Division by zero → print `Error: Division by zero`

### Examples
```
Input:  10 + 5
Output: 15

Input:  10 / 4
Output: 2.5

Input:  8 / 0
Output: Error: Division by zero
```""",
        "test_cases": [
            {"input": "10 + 5", "output": "15"},
            {"input": "10 / 4", "output": "2.5"},
            {"input": "6 * 7",  "output": "42"},
            {"input": "8 / 0",  "output": "Error: Division by zero"},
        ]
    }),

    # ── Largest of Two / Two numbers ─────────────────────────────────────────
    (r'largest.*number|greatest.*number|maximum.*number', {
        "difficulty": "EASY",
        "description": """## Largest Number

Given `n` numbers, find the **maximum** (largest) among them.

### Input Format
First line: integer `n` (count of numbers).
Second line: `n` space-separated integers.

### Output Format
Print the largest number.

### Examples
```
Input:
5
3 9 1 7 5
Output: 9

Input:
3
-1 -5 -3
Output: -1
```""",
        "test_cases": [
            {"input": "5\n3 9 1 7 5",   "output": "9"},
            {"input": "3\n-1 -5 -3",    "output": "-1"},
            {"input": "4\n100 200 50 75","output": "200"},
        ]
    }),

    # ── Currency Conversion ───────────────────────────────────────────────────
    (r'currency|rupee|usd', {
        "difficulty": "EASY",
        "description": """## Currency Converter (INR → USD)

Convert Indian Rupees (INR) to US Dollars (USD).

**Exchange Rate:** 1 USD = 83.5 INR (fixed for this problem)

### Input Format
A single floating-point number representing the amount in **rupees**.

### Output Format
Print the equivalent in USD rounded to **2 decimal places**.

### Examples
```
Input:  835
Output: 10.00

Input:  1000
Output: 11.98
```""",
        "test_cases": [
            {"input": "835",   "output": "10.00"},
            {"input": "8350",  "output": "100.00"},
            {"input": "1670",  "output": "20.00"},
        ]
    }),

    # ── Prime Number ──────────────────────────────────────────────────────────
    (r'prime', {
        "difficulty": "EASY",
        "description": """## Prime Number

A **prime number** is a natural number greater than 1 that has no divisors other than **1** and **itself**.

### Examples
- `17` → Prime ✅
- `15` → Not Prime (divisible by 3 and 5) ❌

### Approach
Check divisibility from 2 to √n. If any factor is found, it's not prime.

### Input Format
A single integer `n`.

### Output Format
Print `Prime` or `Not Prime`.

### Examples
```
Input:  17
Output: Prime

Input:  15
Output: Not Prime
```""",
        "test_cases": [
            {"input": "17", "output": "Prime"},
            {"input": "15", "output": "Not Prime"},
            {"input": "2",  "output": "Prime"},
            {"input": "1",  "output": "Not Prime"},
        ]
    }),

    # ── Factorial ────────────────────────────────────────────────────────────
    (r'factorial', {
        "difficulty": "EASY",
        "description": """## Factorial

The **factorial** of a non-negative integer `n` (written as `n!`) is the product of all positive integers ≤ n.

```
n! = n × (n-1) × (n-2) × ... × 2 × 1
0! = 1
```

### Input Format
A single non-negative integer `n`.

### Output Format
Print `n!`.

### Constraints
- 0 ≤ n ≤ 20

### Examples
```
Input:  5
Output: 120

Input:  0
Output: 1
```""",
        "test_cases": [
            {"input": "5",  "output": "120"},
            {"input": "0",  "output": "1"},
            {"input": "10", "output": "3628800"},
        ]
    }),

    # ── Reverse Number ────────────────────────────────────────────────────────
    (r'reverse.*number|number.*reverse', {
        "difficulty": "EASY",
        "description": """## Reverse a Number

Given an integer `n`, reverse its digits and print the result.

### Notes
- Leading zeros in the reversed number should be dropped.
- Negative numbers: reverse the digits, keep the minus sign.

### Input Format
A single integer `n`.

### Output Format
Print the reversed integer.

### Examples
```
Input:  12345
Output: 54321

Input:  -900
Output: -9

Input:  100
Output: 1
```""",
        "test_cases": [
            {"input": "12345", "output": "54321"},
            {"input": "-900",  "output": "-9"},
            {"input": "100",   "output": "1"},
        ]
    }),

    # ── Pyramid / Pattern ────────────────────────────────────────────────────
    (r'pyramid|pattern|triangle.*star|star.*triangle', {
        "difficulty": "EASY",
        "description": """## Star Pattern / Pyramid

Print a star (`*`) pyramid pattern of height `n`.

### Input Format
A single integer `n` (number of rows).

### Output Format
Print a half-pyramid (right-aligned stars growing).

### Example
```
Input: 5

Output:
*
**
***
****
*****
```""",
        "test_cases": [
            {"input": "5", "output": "*\n**\n***\n****\n*****"},
            {"input": "3", "output": "*\n**\n***"},
        ]
    }),

    # ── Greeting / Name ───────────────────────────────────────────────────────
    (r'greeting|print.*name|name.*greeting', {
        "difficulty": "EASY",
        "description": """## Greeting Program

Read a name as input and print a personalized greeting.

### Input Format
A single string `name`.

### Output Format
Print: `Hello, <name>! Welcome to the program.`

### Examples
```
Input:  Alice
Output: Hello, Alice! Welcome to the program.

Input:  Snehitha
Output: Hello, Snehitha! Welcome to the program.
```""",
        "test_cases": [
            {"input": "Alice",    "output": "Hello, Alice! Welcome to the program."},
            {"input": "Snehitha", "output": "Hello, Snehitha! Welcome to the program."},
        ]
    }),

    # ── Area of Parallelogram ────────────────────────────────────────────────
    (r'area of parallelogram', {
        "difficulty": "EASY",
        "description": """## Area of Parallelogram

Calculate the **area of a parallelogram** given its base and height.

**Formula:** `Area = base × height`

### Input Format
Two floating-point numbers: `base height`.

### Output Format
Print the area.

### Examples
```
Input:  6 4
Output: 24.0

Input:  8 5
Output: 40.0
```""",
        "test_cases": [
            {"input": "6 4", "output": "24.0"},
            {"input": "8 5", "output": "40.0"},
        ]
    }),

    # ── Area of Rhombus ───────────────────────────────────────────────────────
    (r'area of rhombus', {
        "difficulty": "EASY",
        "description": """## Area of Rhombus

Calculate the **area of a rhombus** given its two diagonals.

**Formula:** `Area = (d1 × d2) / 2`

### Input Format
Two floating-point numbers: `d1 d2` (diagonals).

### Output Format
Print the area.

### Examples
```
Input:  6 8
Output: 24.0

Input:  5 10
Output: 25.0
```""",
        "test_cases": [
            {"input": "6 8",  "output": "24.0"},
            {"input": "5 10", "output": "25.0"},
        ]
    }),

    # ── Linear Search ─────────────────────────────────────────────────────────
    (r'linear search', {
        "difficulty": "EASY",
        "description": """## Linear Search

**Linear Search** is the simplest searching algorithm. It checks every element in the array sequentially until the target is found.

### Algorithm
1. Start from index 0.
2. Compare each element with `target`.
3. If found, return the **index**.
4. If not found after the entire array, return `-1`.

### Time Complexity
- **Best Case:** O(1) — target at first position
- **Worst Case:** O(n) — target at last or not present

### Input Format
```
n               (array size)
arr[0] ... arr[n-1]  (space-separated)
target
```

### Output Format
Print the **0-based index** of target, or `-1` if not found.

### Examples
```
Input:
5
4 2 6 1 9
6
Output: 2

Input:
4
1 2 3 4
7
Output: -1
```""",
        "test_cases": [
            {"input": "5\n4 2 6 1 9\n6", "output": "2"},
            {"input": "4\n1 2 3 4\n7",   "output": "-1"},
            {"input": "3\n10 20 30\n10", "output": "0"},
        ]
    }),

    # ── Binary Search ─────────────────────────────────────────────────────────
    (r'binary search', {
        "difficulty": "MEDIUM",
        "description": """## Binary Search

**Binary Search** is an efficient algorithm for finding an element in a **sorted** array by repeatedly halving the search interval.

### Algorithm
1. Set `low = 0`, `high = n - 1`.
2. Compute `mid = (low + high) / 2`.
3. If `arr[mid] == target` → return `mid`.
4. If `arr[mid] < target` → search right half (`low = mid + 1`).
5. Else → search left half (`high = mid - 1`).
6. If `low > high` → return `-1`.

### Time Complexity
- **O(log n)** — significantly faster than linear search

### Input Format
```
n
arr[0] ... arr[n-1]   (sorted, space-separated)
target
```

### Output Format
Print the **0-based index** of target, or `-1` if not found.

### Examples
```
Input:
6
-1 0 3 5 9 12
9
Output: 4

Input:
6
-1 0 3 5 9 12
2
Output: -1
```""",
        "test_cases": [
            {"input": "6\n-1 0 3 5 9 12\n9",  "output": "4"},
            {"input": "6\n-1 0 3 5 9 12\n2",  "output": "-1"},
            {"input": "5\n1 3 5 7 9\n1",       "output": "0"},
        ]
    }),

    # ── Bubble Sort ───────────────────────────────────────────────────────────
    (r'bubble sort', {
        "difficulty": "MEDIUM",
        "description": """## Bubble Sort

**Bubble Sort** repeatedly steps through the array, compares adjacent elements and swaps them if they are in the wrong order.

### Algorithm
```
for i in 0 to n-1:
    for j in 0 to n-i-2:
        if arr[j] > arr[j+1]:
            swap(arr[j], arr[j+1])
```

### Time Complexity
| Case | Complexity |
|------|-----------|
| Best | O(n) — already sorted |
| Average | O(n²) |
| Worst | O(n²) |

### Input Format
```
n
arr[0] ... arr[n-1]
```

### Output Format
Print the sorted array (space-separated).

### Examples
```
Input:
5
64 34 25 12 22
Output: 12 22 25 34 64

Input:
4
5 1 4 2
Output: 1 2 4 5
```""",
        "test_cases": [
            {"input": "5\n64 34 25 12 22", "output": "12 22 25 34 64"},
            {"input": "4\n5 1 4 2",        "output": "1 2 4 5"},
            {"input": "3\n3 2 1",          "output": "1 2 3"},
        ]
    }),

    # ── Selection Sort ────────────────────────────────────────────────────────
    (r'selection sort', {
        "difficulty": "MEDIUM",
        "description": """## Selection Sort

**Selection Sort** divides the array into sorted and unsorted parts. It repeatedly selects the minimum element from the unsorted part and moves it to the beginning.

### Algorithm
```
for i in 0 to n-1:
    min_idx = i
    for j in i+1 to n:
        if arr[j] < arr[min_idx]:
            min_idx = j
    swap(arr[i], arr[min_idx])
```

### Time Complexity: O(n²) — all cases

### Input Format
```
n
arr[0] ... arr[n-1]
```

### Output Format
Print the sorted array (space-separated).

### Examples
```
Input:
5
64 25 12 22 11
Output: 11 12 22 25 64
```""",
        "test_cases": [
            {"input": "5\n64 25 12 22 11", "output": "11 12 22 25 64"},
            {"input": "4\n9 7 5 3",        "output": "3 5 7 9"},
            {"input": "3\n1 2 3",          "output": "1 2 3"},
        ]
    }),

    # ── Insertion Sort ────────────────────────────────────────────────────────
    (r'insertion sort', {
        "difficulty": "MEDIUM",
        "description": """## Insertion Sort

**Insertion Sort** builds the sorted array one item at a time by inserting each element into its correct position.

### Algorithm
```
for i in 1 to n:
    key = arr[i]
    j = i - 1
    while j >= 0 and arr[j] > key:
        arr[j+1] = arr[j]
        j -= 1
    arr[j+1] = key
```

### Time Complexity
| Case | Complexity |
|------|-----------|
| Best | O(n) |
| Average/Worst | O(n²) |

### Input Format
```
n
arr[0] ... arr[n-1]
```

### Output Format
Print the sorted array (space-separated).

### Examples
```
Input:
5
12 11 13 5 6
Output: 5 6 11 12 13
```""",
        "test_cases": [
            {"input": "5\n12 11 13 5 6", "output": "5 6 11 12 13"},
            {"input": "4\n4 3 2 1",      "output": "1 2 3 4"},
        ]
    }),

    # ── Merge Sort ─────────────────────────────────────────────────────────────
    (r'merge sort', {
        "difficulty": "MEDIUM",
        "description": """## Merge Sort

**Merge Sort** is a divide-and-conquer algorithm that splits the array in half, recursively sorts each half, then merges them.

### Time Complexity: O(n log n) — all cases
### Space Complexity: O(n)

### Algorithm
```
mergeSort(arr, l, r):
    if l < r:
        mid = (l + r) / 2
        mergeSort(arr, l, mid)
        mergeSort(arr, mid+1, r)
        merge(arr, l, mid, r)
```

### Input Format
```
n
arr[0] ... arr[n-1]
```

### Output Format
Print the sorted array (space-separated).

### Examples
```
Input:
6
38 27 43 3 9 82
Output: 3 9 27 38 43 82
```""",
        "test_cases": [
            {"input": "6\n38 27 43 3 9 82", "output": "3 9 27 38 43 82"},
            {"input": "4\n5 3 1 4",         "output": "1 3 4 5"},
        ]
    }),

    # ── Quick Sort ────────────────────────────────────────────────────────────
    (r'quick sort', {
        "difficulty": "MEDIUM",
        "description": """## Quick Sort

**Quick Sort** selects a **pivot** element and partitions the array so that elements less than the pivot go left and greater go right, then recursively sorts each partition.

### Time Complexity
| Case | Complexity |
|------|-----------|
| Best/Average | O(n log n) |
| Worst | O(n²) — when pivot is always min/max |

### Input Format
```
n
arr[0] ... arr[n-1]
```

### Output Format
Print the sorted array (space-separated).

### Examples
```
Input:
6
10 7 8 9 1 5
Output: 1 5 7 8 9 10
```""",
        "test_cases": [
            {"input": "6\n10 7 8 9 1 5", "output": "1 5 7 8 9 10"},
            {"input": "5\n3 6 8 10 1",   "output": "1 3 6 8 10"},
        ]
    }),

    # ── Power / Exponent ──────────────────────────────────────────────────────
    (r'power|exponent', {
        "difficulty": "EASY",
        "description": """## Power of a Number

Calculate `base^exponent` (base raised to the power of exponent).

### Input Format
Two integers: `base exponent`.

### Output Format
Print `base^exponent`.

### Constraints
- 0 ≤ exponent ≤ 30

### Examples
```
Input:  2 10
Output: 1024

Input:  3 4
Output: 81
```""",
        "test_cases": [
            {"input": "2 10", "output": "1024"},
            {"input": "3 4",  "output": "81"},
            {"input": "5 0",  "output": "1"},
        ]
    }),

    # ── Swap Two Numbers ──────────────────────────────────────────────────────
    (r'swap', {
        "difficulty": "EASY",
        "description": """## Swap Two Numbers

Swap two integers **without using a temporary variable**.

**Approach using arithmetic:**
```
a = a + b
b = a - b
a = a - b
```

### Input Format
Two integers `a b`.

### Output Format
Print the swapped values: `a b` (space-separated).

### Examples
```
Input:  5 10
Output: 10 5

Input:  -3 7
Output: 7 -3
```""",
        "test_cases": [
            {"input": "5 10", "output": "10 5"},
            {"input": "-3 7", "output": "7 -3"},
            {"input": "0 0",  "output": "0 0"},
        ]
    }),
]


def normalise(s: str) -> str:
    return re.sub(r'[^a-z0-9 ]', '', s.lower()).strip()


def match_pattern(title_norm: str):
    for pattern, enrichment in PATTERNS:
        if re.search(pattern, title_norm):
            return enrichment
    return None


def build_generic_description(title: str) -> str:
    """Return a decent generic description when no pattern matches."""
    return f"""## {title}

Solve the following problem step by step.

### Problem Statement
{title}

### Approach
1. Carefully read the input format below.
2. Think through the edge cases.
3. Implement a clean, efficient solution.
4. Test your code using the sample inputs.

### Tips
- Start by understanding what the output should look like.
- Handle edge cases (empty input, negative numbers, zero) before submitting.
- Consider time and space complexity as you optimise.
"""


class Command(BaseCommand):
    help = "Enrich problems with proper descriptions and test cases using keyword patterns."

    def add_arguments(self, parser):
        parser.add_argument(
            '--force', action='store_true',
            help='Re-process ALL problems, not just those without test cases.'
        )

    def handle(self, *args, **options):
        force = options['force']

        qs = Problem.objects.all()
        if not force:
            qs = qs.filter(test_cases=[])

        total    = qs.count()
        enriched = 0
        generic  = 0

        self.stdout.write(f"Processing {total} problems …\n")

        for problem in qs:
            norm  = normalise(problem.title)
            match = match_pattern(norm)

            if match:
                problem.test_cases  = match.get("test_cases",  problem.test_cases)
                problem.description = match.get("description", problem.description)
                if "difficulty" in match:
                    problem.difficulty = match["difficulty"]
                problem.save(update_fields=["test_cases", "description", "difficulty"])
                enriched += 1
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ [PATTERN] {problem.title[:60]}"
                ))
            else:
                # At minimum give a good description
                if not problem.description or len(problem.description) < 60:
                    problem.description = build_generic_description(problem.title)
                    problem.save(update_fields=["description"])
                generic += 1
                self.stdout.write(
                    f"  · [GENERIC] {problem.title[:60]}"
                )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done! {enriched} problems pattern-matched & enriched, "
            f"{generic} given generic descriptions."
        ))
