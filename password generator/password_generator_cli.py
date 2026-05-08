"""
Random Password Generator - CLI Version
========================================
A command-line password generator with input validation,
strong password rules, and password strength indicator.
"""

import random
import string


# ──────────────────────────────────────────────
#  CHARACTER SETS
# ──────────────────────────────────────────────
SIMILAR_CHARS = set("0Ol1I|")          # visually ambiguous characters

LETTERS_UPPER = string.ascii_uppercase
LETTERS_LOWER = string.ascii_lowercase
NUMBERS       = string.digits
SYMBOLS       = string.punctuation


# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────
def filter_similar(chars: str) -> str:
    """Remove characters that look alike (0, O, l, 1, …)."""
    return "".join(c for c in chars if c not in SIMILAR_CHARS)


def get_character_pool(use_letters: bool,
                       use_numbers: bool,
                       use_symbols: bool,
                       exclude_similar: bool) -> tuple[str, list[str]]:
    """
    Build the full character pool and a list of guaranteed characters
    (one per selected category) to satisfy strength requirements.

    Returns:
        pool       – all eligible characters as a string
        guaranteed – one character per active category
    """
    pool      = ""
    guaranteed = []

    if use_letters:
        upper = LETTERS_UPPER
        lower = LETTERS_LOWER
        if exclude_similar:
            upper = filter_similar(upper)
            lower = filter_similar(lower)
        pool += upper + lower
        guaranteed.append(random.choice(upper))
        guaranteed.append(random.choice(lower))

    if use_numbers:
        nums = NUMBERS
        if exclude_similar:
            nums = filter_similar(nums)
        pool += nums
        guaranteed.append(random.choice(nums))

    if use_symbols:
        syms = SYMBOLS
        if exclude_similar:
            syms = filter_similar(syms)
        pool += syms
        guaranteed.append(random.choice(syms))

    return pool, guaranteed


def generate_password(length: int,
                      use_letters: bool,
                      use_numbers: bool,
                      use_symbols: bool,
                      exclude_similar: bool) -> str:
    """
    Generate a random password that satisfies the selected criteria
    and strong-password rules (at least one char from each active group).
    """
    pool, guaranteed = get_character_pool(
        use_letters, use_numbers, use_symbols, exclude_similar
    )

    # Fill the remaining positions from the full pool
    remaining_length = length - len(guaranteed)
    remaining_chars  = [random.choice(pool) for _ in range(remaining_length)]

    # Combine guaranteed + random, then shuffle for unpredictability
    all_chars = guaranteed + remaining_chars
    random.shuffle(all_chars)

    return "".join(all_chars)


def evaluate_strength(password: str) -> tuple[str, str]:
    """
    Rate password strength as Weak / Medium / Strong.

    Criteria checked:
      • Length ≥ 8, ≥ 12
      • Contains uppercase, lowercase, digit, symbol
    Returns (label, coloured_label).
    """
    score = 0

    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.islower() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in string.punctuation for c in password):
        score += 1

    if score <= 2:
        return "Weak",   "\033[91mWeak\033[0m"      # red
    elif score <= 4:
        return "Medium", "\033[93mMedium\033[0m"    # yellow
    else:
        return "Strong", "\033[92mStrong\033[0m"    # green


# ──────────────────────────────────────────────
#  INPUT HELPERS
# ──────────────────────────────────────────────
def ask_yes_no(prompt: str) -> bool:
    """Repeatedly ask until the user answers 'yes' or 'no'."""
    while True:
        answer = input(prompt).strip().lower()
        if answer in ("yes", "y"):
            return True
        if answer in ("no", "n"):
            return False
        print("  ⚠  Please enter 'yes' or 'no'.")


def ask_positive_int(prompt: str) -> int:
    """Repeatedly ask until the user enters a positive integer."""
    while True:
        raw = input(prompt).strip()
        if raw.isdigit() and int(raw) > 0:
            return int(raw)
        print("  ⚠  Please enter a positive whole number.")


# ──────────────────────────────────────────────
#  MAIN FLOW
# ──────────────────────────────────────────────
def main() -> None:
    print("\n" + "=" * 50)
    print("       🔐  RANDOM PASSWORD GENERATOR  🔐")
    print("=" * 50)

    while True:                            # allow multiple generations
        print()

        # ── 1. Password length ──
        length = ask_positive_int("Enter desired password length: ")
        if length < 4:
            print("  ⚠  Minimum length is 4 to satisfy strength rules.")
            length = 4

        # ── 2. Character types ──
        use_letters = ask_yes_no("Include letters?  (yes/no): ")
        use_numbers = ask_yes_no("Include numbers?  (yes/no): ")
        use_symbols = ask_yes_no("Include symbols?  (yes/no): ")

        # Ensure at least one type is selected
        if not any([use_letters, use_numbers, use_symbols]):
            print("\n  ⚠  You must select at least one character type.\n")
            continue

        # ── 3. Extra options ──
        exclude_similar = ask_yes_no(
            "Exclude similar characters (0, O, l, 1)?  (yes/no): "
        )

        # ── 4. Generate ──
        password        = generate_password(
            length, use_letters, use_numbers, use_symbols, exclude_similar
        )
        strength, coloured = evaluate_strength(password)

        # ── 5. Display ──
        print("\n" + "-" * 50)
        print(f"  Generated Password : \033[1m{password}\033[0m")
        print(f"  Password Strength  : {coloured}")
        print("-" * 50)

        # ── 6. Generate another? ──
        again = ask_yes_no("\nGenerate another password?  (yes/no): ")
        if not again:
            break

    print("\n✅  Thank you for using the Password Generator. Stay secure!\n")


if __name__ == "__main__":
    main()
