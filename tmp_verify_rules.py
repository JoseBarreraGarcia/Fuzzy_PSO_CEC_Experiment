"""Verify and compare 3L vs 5L rule sets - consistency analysis."""
from FUZZY.fuzzy_controller_w_3L import FuzzyInertiaController_3L
from FUZZY.fuzzy_controller_w_5L import FuzzyInertiaController_5L

div3 = ['low', 'medium', 'high']
prog3 = ['early', 'mid', 'late']
m3 = {'low': 'L', 'medium': 'M', 'high': 'H'}

div5 = ['very_low', 'low', 'medium', 'high', 'very_high']
prog5 = ['very_early', 'early', 'mid', 'late', 'very_late']
m5 = {'very_low': 'VL', 'low': 'L', 'medium': 'M', 'high': 'H', 'very_high': 'VH'}

# Numeric mapping for monotonicity checks
num3 = {'low': 0, 'medium': 1, 'high': 2}
num5 = {'very_low': 0, 'low': 1, 'medium': 2, 'high': 3, 'very_high': 4}

print("=" * 95)
print("3L RULE SETS (rows=diversity, cols=progress)")
print("=" * 95)

for rs in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8']:
    ctrl = FuzzyInertiaController_3L('O1', rule_set=rs)
    print(f"\n--- {rs} ---")
    print(f"{'':>10} {'early':>8} {'mid':>8} {'late':>8}")
    for d in div3:
        vals = [m3[ctrl.rules[(d, p)]] for p in prog3]
        print(f"{d:>10} {vals[0]:>8} {vals[1]:>8} {vals[2]:>8}")

    # Check monotonicity
    issues = []
    # Progress should decrease (left to right) for each row
    for d in div3:
        nums = [num3[ctrl.rules[(d, p)]] for p in prog3]
        for i in range(len(nums) - 1):
            if nums[i] < nums[i + 1]:
                issues.append(f"  [WARN] Row {d}: w INCREASES from {prog3[i]}={m3[ctrl.rules[(d, prog3[i])]]} to {prog3[i+1]}={m3[ctrl.rules[(d, prog3[i+1])]]}")

    # Diversity: check direction per column
    for j, p in enumerate(prog3):
        nums = [num3[ctrl.rules[(d, p)]] for d in div3]
        increasing = all(nums[i] <= nums[i + 1] for i in range(len(nums) - 1))
        decreasing = all(nums[i] >= nums[i + 1] for i in range(len(nums) - 1))
        if increasing and not decreasing:
            direction = "diversity-FOLLOWING (low_div->low_w, high_div->high_w)"
        elif decreasing and not increasing:
            direction = "diversity-COMPENSATING (low_div->high_w, high_div->low_w)"
        elif increasing and decreasing:
            direction = "FLAT"
        else:
            direction = "NON-MONOTONE"
        print(f"  Col {p}: {direction}")

    if issues:
        for i in issues:
            print(i)


print("\n\n" + "=" * 95)
print("5L RULE SETS (rows=diversity, cols=progress)")
print("=" * 95)

for rs in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8']:
    ctrl = FuzzyInertiaController_5L('O1', rule_set=rs)
    print(f"\n--- {rs} ---")
    header = f"{'':>12}" + "".join(f"{p:>12}" for p in prog5)
    print(header)
    for d in div5:
        vals = [m5[ctrl.rules[(d, p)]] for p in prog5]
        print(f"{d:>12}" + "".join(f"{v:>12}" for v in vals))

    # Check monotonicity
    issues = []
    # Progress should decrease (left to right) for each row
    for d in div5:
        nums = [num5[ctrl.rules[(d, p)]] for p in prog5]
        for i in range(len(nums) - 1):
            if nums[i] < nums[i + 1]:
                issues.append(f"  [WARN] Row {d}: w INCREASES {prog5[i]}={m5[ctrl.rules[(d, prog5[i])]]} -> {prog5[i+1]}={m5[ctrl.rules[(d, prog5[i+1])]]}")

    # Diversity direction per column
    for j, p in enumerate(prog5):
        nums = [num5[ctrl.rules[(d, p)]] for d in div5]
        increasing = all(nums[i] <= nums[i + 1] for i in range(len(nums) - 1))
        decreasing = all(nums[i] >= nums[i + 1] for i in range(len(nums) - 1))
        if increasing and not decreasing:
            direction = "diversity-FOLLOWING"
        elif decreasing and not increasing:
            direction = "diversity-COMPENSATING"
        elif increasing and decreasing:
            direction = "FLAT"
        else:
            direction = "NON-MONOTONE"
        print(f"  Col {p}: {direction}")

    if issues:
        for i in issues:
            print(i)


print("\n\n" + "=" * 95)
print("CONSISTENCY CHECK: 3L vs 5L diversity direction")
print("=" * 95)

for rs in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8']:
    ctrl3 = FuzzyInertiaController_3L('O1', rule_set=rs)
    ctrl5 = FuzzyInertiaController_5L('O1', rule_set=rs)

    # 3L diversity direction
    dirs_3L = []
    for p in prog3:
        nums = [num3[ctrl3.rules[(d, p)]] for d in div3]
        inc = all(nums[i] <= nums[i + 1] for i in range(len(nums) - 1))
        dec = all(nums[i] >= nums[i + 1] for i in range(len(nums) - 1))
        if inc and not dec:
            dirs_3L.append("FOLLOW")
        elif dec and not inc:
            dirs_3L.append("COMP")
        elif inc and dec:
            dirs_3L.append("FLAT")
        else:
            dirs_3L.append("MIX")

    # 5L diversity direction
    dirs_5L = []
    for p in prog5:
        nums = [num5[ctrl5.rules[(d, p)]] for d in div5]
        inc = all(nums[i] <= nums[i + 1] for i in range(len(nums) - 1))
        dec = all(nums[i] >= nums[i + 1] for i in range(len(nums) - 1))
        if inc and not dec:
            dirs_5L.append("FOLLOW")
        elif dec and not inc:
            dirs_5L.append("COMP")
        elif inc and dec:
            dirs_5L.append("FLAT")
        else:
            dirs_5L.append("MIX")

    match = "OK" if all(d3 == d5 or d3 == "FLAT" or d5 == "FLAT"
                        for d3, d5 in zip(dirs_3L[:3], dirs_5L[1:4])) else "MISMATCH!"
    print(f"\n{rs}: 3L={dirs_3L}  5L={dirs_5L}  -> {match}")
    if match == "MISMATCH!":
        print(f"  *** 3L and 5L have OPPOSITE diversity philosophies! ***")
