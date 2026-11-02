
def _make_step(array, action, message, active=None, sorted_indices=None):
    """Create a consistent step for the Streamlit visualizer."""
    return {
        "array": list(array),
        "action": action,
        "message": message,
        "active": list(active or []),
        "sorted": list(sorted_indices or []),
    }


def bubble_sort_steps(numbers):
    arr = list(numbers)
    steps = [_make_step(arr, "start", "Starting Bubble Sort.")]

    n = len(arr)
    for i in range(n):
        swapped = False

        for j in range(0, n - i - 1):
            steps.append(_make_step(
                arr, "compare",
                f"Compare {arr[j]} and {arr[j + 1]}.",
                [j, j + 1]
            ))

            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
                steps.append(_make_step(
                    arr, "swap",
                    f"Swap them. The array is now {arr}.",
                    [j, j + 1]
                ))

        steps.append(_make_step(
            arr, "pass",
            f"Pass {i + 1} completed.",
            sorted_indices=list(range(n - i - 1, n))
        ))

        if not swapped:
            break

    steps.append(_make_step(
        arr, "complete", f"Sorted result: {arr}.",
        sorted_indices=list(range(n))
    ))
    return steps


def selection_sort_steps(numbers):
    arr = list(numbers)
    n = len(arr)
    steps = [_make_step(arr, "start", "Starting Selection Sort.")]

    for i in range(n):
        min_index = i

        for j in range(i + 1, n):
            steps.append(_make_step(
                arr, "compare",
                f"Compare current minimum {arr[min_index]} with {arr[j]}.",
                [min_index, j],
                list(range(i))
            ))

            if arr[j] < arr[min_index]:
                min_index = j
                steps.append(_make_step(
                    arr, "new_minimum",
                    f"New minimum found: {arr[min_index]}.",
                    [min_index],
                    list(range(i))
                ))

        if min_index != i:
            arr[i], arr[min_index] = arr[min_index], arr[i]
            steps.append(_make_step(
                arr, "swap",
                f"Place {arr[i]} in its correct position.",
                [i, min_index],
                list(range(i))
            ))

        steps.append(_make_step(
            arr, "pass", f"Position {i} is fixed.",
            sorted_indices=list(range(i + 1))
        ))

    steps.append(_make_step(
        arr, "complete", f"Sorted result: {arr}.",
        sorted_indices=list(range(n))
    ))
    return steps


def insertion_sort_steps(numbers):
    arr = list(numbers)
    n = len(arr)
    steps = [_make_step(arr, "start", "Starting Insertion Sort.")]

    for i in range(1, n):
        key = arr[i]
        j = i - 1

        steps.append(_make_step(
            arr, "select", f"Take {key} as the value to insert.",
            [i], list(range(i))
        ))

        while j >= 0 and arr[j] > key:
            steps.append(_make_step(
                arr, "compare", f"Compare {arr[j]} with {key}.",
                [j, j + 1], list(range(i))
            ))
            arr[j + 1] = arr[j]
            steps.append(_make_step(
                arr, "shift", f"Shift {arr[j]} one position to the right.",
                [j, j + 1]
            ))
            j -= 1

        arr[j + 1] = key
        steps.append(_make_step(
            arr, "insert", f"Insert {key} at position {j + 1}.",
            [j + 1], list(range(i + 1))
        ))

    steps.append(_make_step(
        arr, "complete", f"Sorted result: {arr}.",
        sorted_indices=list(range(n))
    ))
    return steps


def merge_sort_steps(numbers):
    arr = list(numbers)
    steps = [_make_step(arr, "start", "Starting Merge Sort.")]

    def merge(left, mid, right):
        left_values = arr[left:mid + 1]
        right_values = arr[mid + 1:right + 1]
        i = j = 0
        k = left

        steps.append(_make_step(
            arr, "split",
            f"Merge the sections {left_values} and {right_values}.",
            list(range(left, right + 1))
        ))

        while i < len(left_values) and j < len(right_values):
            if left_values[i] <= right_values[j]:
                arr[k] = left_values[i]
                i += 1
            else:
                arr[k] = right_values[j]
                j += 1
            steps.append(_make_step(
                arr, "merge", f"Write {arr[k]} into position {k}.", [k]
            ))
            k += 1

        while i < len(left_values):
            arr[k] = left_values[i]
            steps.append(_make_step(
                arr, "merge", f"Write remaining value {arr[k]} into position {k}.",
                [k]
            ))
            i += 1
            k += 1

        while j < len(right_values):
            arr[k] = right_values[j]
            steps.append(_make_step(
                arr, "merge", f"Write remaining value {arr[k]} into position {k}.",
                [k]
            ))
            j += 1
            k += 1

    def divide(left, right):
        if left >= right:
            return
        mid = (left + right) // 2
        steps.append(_make_step(
            arr, "divide",
            f"Divide positions {left}–{right} into two sections.",
            list(range(left, right + 1))
        ))
        divide(left, mid)
        divide(mid + 1, right)
        merge(left, mid, right)

    if arr:
        divide(0, len(arr) - 1)

    steps.append(_make_step(
        arr, "complete", f"Sorted result: {arr}.",
        sorted_indices=list(range(len(arr)))
    ))
    return steps


def quick_sort_steps(numbers):
    arr = list(numbers)
    steps = [_make_step(arr, "start", "Starting Quick Sort.")]

    def quick_sort(low, high):
        if low >= high:
            return

        pivot = arr[high]
        steps.append(_make_step(
            arr, "pivot", f"Choose {pivot} as the pivot.",
            [high]
        ))

        i = low
        for j in range(low, high):
            steps.append(_make_step(
                arr, "compare",
                f"Compare {arr[j]} with pivot {pivot}.",
                [j, high]
            ))
            if arr[j] <= pivot:
                arr[i], arr[j] = arr[j], arr[i]
                steps.append(_make_step(
                    arr, "partition",
                    f"Move a value less than or equal to the pivot to the left.",
                    [i, j]
                ))
                i += 1

        arr[i], arr[high] = arr[high], arr[i]
        steps.append(_make_step(
            arr, "pivot_placed",
            f"Place pivot {arr[i]} in its final position.",
            [i]
        ))

        quick_sort(low, i - 1)
        quick_sort(i + 1, high)

    if arr:
        quick_sort(0, len(arr) - 1)

    steps.append(_make_step(
        arr, "complete", f"Sorted result: {arr}.",
        sorted_indices=list(range(len(arr)))
    ))
    return steps


def heap_sort_steps(numbers):
    arr = list(numbers)
    n = len(arr)
    steps = [_make_step(arr, "start", "Starting Heap Sort.")]

    def heapify(size, root):
        largest = root
        left = 2 * root + 1
        right = 2 * root + 2

        if left < size:
            steps.append(_make_step(
                arr, "compare", "Compare the root with its left child.",
                [root, left]
            ))
            if arr[left] > arr[largest]:
                largest = left

        if right < size:
            steps.append(_make_step(
                arr, "compare", "Compare the largest value with its right child.",
                [largest, right]
            ))
            if arr[right] > arr[largest]:
                largest = right

        if largest != root:
            arr[root], arr[largest] = arr[largest], arr[root]
            steps.append(_make_step(
                arr, "swap", "Swap to maintain the max heap.",
                [root, largest]
            ))
            heapify(size, largest)

    for i in range(n // 2 - 1, -1, -1):
        heapify(n, i)

    for end in range(n - 1, 0, -1):
        arr[0], arr[end] = arr[end], arr[0]
        steps.append(_make_step(
            arr, "extract", f"Move the largest remaining value to position {end}.",
            [0, end], list(range(end, n))
        ))
        heapify(end, 0)

    steps.append(_make_step(
        arr, "complete", f"Sorted result: {arr}.",
        sorted_indices=list(range(n))
    ))
    return steps


def shell_sort_steps(numbers):
    arr = list(numbers)
    n = len(arr)
    steps = [_make_step(arr, "start", "Starting Shell Sort.")]

    gap = n // 2
    while gap > 0:
        steps.append(_make_step(
            arr, "gap", f"Use a gap of {gap}."
        ))

        for i in range(gap, n):
            temp = arr[i]
            j = i

            while j >= gap and arr[j - gap] > temp:
                steps.append(_make_step(
                    arr, "compare",
                    f"Compare {arr[j - gap]} and {temp} using gap {gap}.",
                    [j - gap, j]
                ))
                arr[j] = arr[j - gap]
                steps.append(_make_step(
                    arr, "shift", "Shift the larger value forward.",
                    [j - gap, j]
                ))
                j -= gap

            arr[j] = temp
            steps.append(_make_step(
                arr, "insert", f"Place {temp} at position {j}.", [j]
            ))

        gap //= 2

    steps.append(_make_step(
        arr, "complete", f"Sorted result: {arr}.",
        sorted_indices=list(range(n))
    ))
    return steps


def counting_sort_steps(numbers):
    arr = list(numbers)
    steps = [_make_step(arr, "start", "Starting Counting Sort.")]

    if not arr:
        steps.append(_make_step(arr, "complete", "The array is empty."))
        return steps

    minimum, maximum = min(arr), max(arr)
    span = maximum - minimum + 1

    if span > 10000:
        raise ValueError(
            "Counting Sort is unsuitable for this value range. "
            "Please use values with a range of 10,000 or less."
        )

    counts = [0] * span
    for value in arr:
        counts[value - minimum] += 1
        steps.append(_make_step(
            arr, "count", f"Count one occurrence of {value}."
        ))

    output = []
    for offset, count in enumerate(counts):
        value = offset + minimum
        for _ in range(count):
            output.append(value)
            steps.append(_make_step(
                output + arr[len(output):],
                "place", f"Place {value} into the sorted output."
            ))

    steps.append(_make_step(
        output, "complete", f"Sorted result: {output}.",
        sorted_indices=list(range(len(output)))
    ))
    return steps


def radix_sort_steps(numbers):
    arr = list(numbers)
    steps = [_make_step(arr, "start", "Starting Radix Sort.")]

    if not arr:
        steps.append(_make_step(arr, "complete", "The array is empty."))
        return steps

    # Offset all values so the digit-based sort can handle negative integers.
    offset = -min(arr) if min(arr) < 0 else 0
    shifted = [value + offset for value in arr]
    max_value = max(shifted)
    place = 1

    while max_value // place > 0:
        buckets = [[] for _ in range(10)]

        for value in shifted:
            digit = (value // place) % 10
            buckets[digit].append(value)
            steps.append(_make_step(
                arr, "digit",
                f"Put value {value - offset} into digit bucket {digit}."
            ))

        shifted = [value for bucket in buckets for value in bucket]
        arr = [value - offset for value in shifted]
        steps.append(_make_step(
            arr, "pass",
            f"Complete the digit pass for place value {place}."
        ))
        place *= 10

    steps.append(_make_step(
        arr, "complete", f"Sorted result: {arr}.",
        sorted_indices=list(range(len(arr)))
    ))
    return steps


def bucket_sort_steps(numbers):
    arr = list(numbers)
    steps = [_make_step(arr, "start", "Starting Bucket Sort.")]

    if len(arr) < 2:
        steps.append(_make_step(
            arr, "complete", f"Sorted result: {arr}.",
            sorted_indices=list(range(len(arr)))
        ))
        return steps

    minimum, maximum = min(arr), max(arr)
    if minimum == maximum:
        steps.append(_make_step(
            arr, "complete", f"All values are equal: {arr}.",
            sorted_indices=list(range(len(arr)))
        ))
        return steps

    bucket_count = min(len(arr), 10)
    buckets = [[] for _ in range(bucket_count)]

    for value in arr:
        index = int((value - minimum) * bucket_count / (maximum - minimum + 1))
        index = min(index, bucket_count - 1)
        buckets[index].append(value)
        steps.append(_make_step(
            arr, "bucket", f"Place {value} into bucket {index}.",
        ))

    result = []
    for index, bucket in enumerate(buckets):
        bucket.sort()
        steps.append(_make_step(
            result + bucket + arr[len(result) + len(bucket):],
            "sort_bucket", f"Sort bucket {index}: {bucket}."
        ))
        result.extend(bucket)

    arr = result
    steps.append(_make_step(
        arr, "complete", f"Sorted result: {arr}.",
        sorted_indices=list(range(len(arr)))
    ))
    return steps


def linear_search_steps(numbers, target):
    arr = list(numbers)
    steps = [_make_step(arr, "start", f"Searching for {target}.")]

    for i, value in enumerate(arr):
        steps.append(_make_step(
            arr, "compare", f"Check position {i}: {value}.", [i]
        ))
        if value == target:
            steps.append(_make_step(
                arr, "found", f"Found {target} at position {i}.", [i]
            ))
            return steps

    steps.append(_make_step(
        arr, "not_found", f"{target} was not found."
    ))
    return steps


def binary_search_steps(numbers, target):
    arr = list(numbers)
    steps = [_make_step(arr, "start", "Starting Binary Search.")]

    if arr != sorted(arr):
        raise ValueError("Binary Search requires the numbers to be sorted.")

    low, high = 0, len(arr) - 1

    while low <= high:
        mid = (low + high) // 2
        steps.append(_make_step(
            arr, "compare",
            f"Check middle position {mid}: value {arr[mid]}.",
            [mid]
        ))

        if arr[mid] == target:
            steps.append(_make_step(
                arr, "found", f"Found {target} at position {mid}.", [mid]
            ))
            return steps
        if arr[mid] < target:
            low = mid + 1
            steps.append(_make_step(
                arr, "search_right", "Search the right half."
            ))
        else:
            high = mid - 1
            steps.append(_make_step(
                arr, "search_left", "Search the left half."
            ))

    steps.append(_make_step(
        arr, "not_found", f"{target} was not found."
    ))
    return steps


SORTING_ALGORITHMS = {
    "Bubble Sort": bubble_sort_steps,
    "Selection Sort": selection_sort_steps,
    "Insertion Sort": insertion_sort_steps,
    "Merge Sort": merge_sort_steps,
    "Quick Sort": quick_sort_steps,
    "Heap Sort": heap_sort_steps,
    "Shell Sort": shell_sort_steps,
    "Counting Sort": counting_sort_steps,
    "Radix Sort": radix_sort_steps,
    "Bucket Sort": bucket_sort_steps,
}

SEARCHING_ALGORITHMS = {
    "Linear Search": linear_search_steps,
    "Binary Search": binary_search_steps,
}


def generate_algorithm_steps(algorithm, numbers, target=None):
    """Generate steps for a supported algorithm."""
    if len(numbers) > 30:
        raise ValueError("Please enter no more than 30 numbers.")

    if algorithm in SORTING_ALGORITHMS:
        return SORTING_ALGORITHMS[algorithm](numbers)

    if algorithm in SEARCHING_ALGORITHMS:
        if target is None:
            raise ValueError("Please enter a target value for searching.")
        return SEARCHING_ALGORITHMS[algorithm](numbers, target)

    supported = list(SORTING_ALGORITHMS) + list(SEARCHING_ALGORITHMS)
    raise ValueError(
        f"Unsupported algorithm: {algorithm}. "
        f"Choose from: {', '.join(supported)}"
    )
