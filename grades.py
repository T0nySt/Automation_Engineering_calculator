import csv
import json
import os
from datetime import datetime

# ─────────────────────────────────────────────
#  CONFIGURATION THRESHOLDS.
# ─────────────────────────────────────────────
DEFAULT_CONFIG = {
    "gpa_threshold": 2.0,
    "grade_threshold": 70.0
}

GRADE_SCALE = [
    (93, "A",  4.0),
    (90, "A-", 3.7),
    (87, "B+", 3.3),
    (83, "B",  3.0),
    (80, "B-", 2.7),
    (77, "C+", 2.3),
    (73, "C",  2.0),
    (70, "C-", 1.7),
    (67, "D+", 1.3),
    (63, "D",  1.0),
    (60, "D-", 0.7),
    (0,  "F",  0.0),
]

# ─────────────────────────────────────────────
#  HELPERS.
# ─────────────────────────────────────────────
def get_letter_grade(avg):
    # Compares the numeric average against the grade scale and returns
    # the matching letter grade and GPA points (e.g. 85 -> "B", 3.0)
    for minimum, letter, points in GRADE_SCALE:
        if avg >= minimum:
            return letter, points
    return "F", 0.0


def load_config(path="config.json"):
    # Reads the config.json file for alert thresholds (GPA and grade minimums).
    # If the file is missing, falls back to the default values defined above.
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return DEFAULT_CONFIG


def parse_weight(raw):
    # Converts a weight entry into a decimal float.
    # Accepts "30%", "0.30", or blank (defaults to 1.0 for equal weighting).
    # Returns None if the value can't be parsed, which causes the row to be skipped.
    """
    Accept weight as: blank (equal weight), "30%", or "0.30"
    Returns a float, or None if invalid.
    """
    raw = raw.strip()
    if not raw:
        return 1.0
    try:
        if "%" in raw:
            return float(raw.replace("%", "").strip()) / 100.0
        return float(raw)
    except ValueError:
        return None


# ─────────────────────────────────────────────
#  INPUT: ADD GRADES MANUALLY.
# ─────────────────────────────────────────────
def add_grades_manually(courses):
    # Prompts the user to type in a course name and assignment details one by one.
    # Validates each entry (score can't exceed max, weight must be a valid number)
    # and appends valid assignments to the in-memory courses dictionary.
    print("\n── Add Grades ──────────────────────────────")
    course = input("Course name (e.g. MATH101): ").strip()
    if not course:
        print("No course name entered. Cancelled.")
        return

    if course not in courses:
        courses[course] = []

    print(f"Entering grades for {course}. Type 'done' when finished.")
    print("  Tip: Leave weight blank to count all assignments equally.")
    print("       You can enter weight as 30% or 0.30 — both work.\n")

    while True:
        name = input("  Assignment name (or 'done'): ").strip()
        if name.lower() == "done":
            break
        if not name:
            continue
        try:
            score = float(input("  Your score:               "))
            max_s = float(input("  Max score:                "))

            if max_s <= 0:
                print("  Max score must be greater than 0. Skipping.\n")
                continue
            if score > max_s:
                print("  Warning: score exceeds max score. Skipping.\n")
                continue

            w_raw  = input("  Weight (optional, e.g. 30% or 0.30): ")
            weight = parse_weight(w_raw)
            if weight is None:
                print("  Invalid weight — skipping this assignment.\n")
                continue

            courses[course].append({
                "name": name, "score": score,
                "max_score": max_s, "weight": weight
            })
            print(f"  Added '{name}'\n")

        except ValueError:
            print("  Invalid input — enter numbers only. Skipping.\n")


# ─────────────────────────────────────────────
#  INPUT: LOAD FROM CSV.
# ─────────────────────────────────────────────
def load_from_csv(courses, path="grades.csv"):
    # Reads grade records from a CSV file and loads them into the courses dictionary.
    # Skips any row that has missing columns, non-numeric values, or a score
    # exceeding the max, and prints a summary of how many rows loaded vs. skipped.
    if not os.path.exists(path):
        print(f"  File '{path}' not found.")
        return

    skipped = 0
    loaded  = 0
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                course = row["Course"].strip()
                name   = row["Assignment"].strip()
                score  = float(row["Score"])
                max_s  = float(row["Max_Score"])
                w_raw  = row.get("Weight", "").strip()
                weight = parse_weight(w_raw)
                if weight is None:
                    weight = 1.0

                if max_s <= 0 or score > max_s:
                    skipped += 1
                    continue

                if course not in courses:
                    courses[course] = []
                courses[course].append({
                    "name": name, "score": score,
                    "max_score": max_s, "weight": weight
                })
                loaded += 1
            except (KeyError, ValueError):
                skipped += 1

    print(f"  Loaded {loaded} records. Skipped {skipped} invalid rows.")


# ─────────────────────────────────────────────
#  CALCULATION.
# ─────────────────────────────────────────────
def calculate_results(courses):
    # For each course, computes the weighted average across all assignments,
    # then maps that average to a letter grade and GPA points using get_letter_grade().
    results = {}
    for course, assignments in courses.items():
        if not assignments:
            continue
        total_weight = sum(a["weight"] for a in assignments)
        weighted_sum = sum((a["score"] / a["max_score"]) * a["weight"] for a in assignments)
        avg = (weighted_sum / total_weight) * 100 if total_weight > 0 else 0
        letter, pts  = get_letter_grade(avg)
        results[course] = {
            "average": round(avg, 2),
            "letter":  letter,
            "gpa_pts": pts,
            "count":   len(assignments)
        }
    return results


def calculate_gpa(results):
    # Averages the GPA points across all courses to produce the cumulative GPA.
    if not results:
        return 0.0
    return round(sum(r["gpa_pts"] for r in results.values()) / len(results), 2)


# ─────────────────────────────────────────────
#  DISPLAY REPORT.
# ─────────────────────────────────────────────
def print_report(results, gpa, config):
    # Prints a formatted table to the console showing each course's average,
    # letter grade, GPA points, and status. Collects any at-risk courses and
    # prints an ALERTS block at the bottom if thresholds are breached.
    grade_thresh = config.get("grade_threshold", 70.0)
    gpa_thresh   = config.get("gpa_threshold",   2.0)

    print("\n" + "=" * 58)
    print("  GRADE REPORT  --  " + datetime.now().strftime("%B %d, %Y"))
    print("=" * 58)
    print(f"  {'Course':<14} {'Avg':>6}  {'Grade':>5}  {'GPA Pts':>7}  Status")
    print("  " + "-" * 54)

    alerts = []
    for course, r in results.items():
        status = "OK"
        if r["average"] < grade_thresh:
            status = "AT RISK"
            alerts.append(f"  {course} average is {r['average']}% (below {grade_thresh}%)")
        print(f"  {course:<14} {r['average']:>5.1f}%  {r['letter']:>5}  {r['gpa_pts']:>7.1f}  {status}")

    print("  " + "-" * 54)
    gpa_status = "LOW GPA" if gpa < gpa_thresh else "OK"
    print(f"  {'CUMULATIVE GPA':<14} {'':>6}  {'':>5}  {gpa:>7.2f}  {gpa_status}")
    print("=" * 58)

    if alerts or gpa < gpa_thresh:
        print("\n  ALERTS:")
        for a in alerts:
            print(a)
        if gpa < gpa_thresh:
            print(f"  Cumulative GPA {gpa} is below minimum of {gpa_thresh}")
    else:
        print("\n  All grades are above thresholds. Keep it up!")
    print()


# ─────────────────────────────────────────────
#  SAVE REPORT TO CSV.
# ─────────────────────────────────────────────
def save_report(results, gpa, filename=None):
    # Writes the current results to a CSV file in the /output folder.
    # If a filename is provided (overwrite mode), it saves to that exact path.
    # Otherwise it generates a new timestamped filename automatically.
    os.makedirs("output", exist_ok=True)
    if filename is None:
        filename = f"output/grade_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Course", "Average", "Letter Grade", "GPA Points"])
        for course, r in results.items():
            writer.writerow([course, r["average"], r["letter"], r["gpa_pts"]])
        writer.writerow([])
        writer.writerow(["Cumulative GPA", gpa])
    print(f"  Report saved to {filename}")
    return filename


def load_courses_from_report(path, courses):
    # Reads an existing report CSV to identify which courses were previously saved.
    # Used to inform the user what's already in the file before they overwrite it.
    """Read an existing grade_report CSV and reload its raw course names so
    the user can add more grades on top of what was already saved."""
    if not os.path.exists(path):
        print(f"  File '{path}' not found.")
        return False
    with open(path, newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Report format: header row, then one row per course, blank row, GPA row
    # We only need the course names — actual assignment data must come from
    # grades.csv or manual input, so we just warn the user if courses are new.
    loaded_courses = []
    for row in rows[1:]:           # skip header
        if not row or row[0].strip() in ("", "Cumulative GPA"):
            break
        loaded_courses.append(row[0].strip())

    if not loaded_courses:
        print("  No course data found in that file.")
        return False

    print(f"  Found courses in report: {', '.join(loaded_courses)}")
    print("  Note: to update grades, load your grades.csv or add manually,")
    print("  then save — this report file will be overwritten with all courses.")
    return True


# ─────────────────────────────────────────────
#  MAIN MENU FEATURE.
# ─────────────────────────────────────────────
def main():
    # Entry point — loads config and runs the main menu loop.
    # Each menu option calls the appropriate function to add, view, or save grades.
    config  = load_config()
    courses = {}

    while True:
        print("\n╔══════════════════════════════════╗")
        print("║    GRADE CALCULATOR & ALERTS     ║")
        print("╠══════════════════════════════════╣")
        print("║  1. Add grades manually          ║")
        print("║  2. Load grades from CSV file    ║")
        print("║  3. View grade report            ║")
        print("║  4. Save report to file          ║")
        print("║  5. Clear all grades             ║")
        print("║  6. Exit                         ║")
        print("╚══════════════════════════════════╝")

        total = sum(len(v) for v in courses.values())
        if total:
            print(f"  ({total} grade(s) loaded across {len(courses)} course(s))")

        choice = input("\nChoose an option (1-6): ").strip()

        if choice == "1":
            add_grades_manually(courses)
        elif choice == "2":
            path = input("CSV filename (press Enter for 'grades.csv'): ").strip()
            load_from_csv(courses, path or "grades.csv")
        elif choice == "3":
            if not courses:
                print("\n  No grades loaded yet. Add some first!")
            else:
                results = calculate_results(courses)
                gpa     = calculate_gpa(results)
                print_report(results, gpa, config)
        elif choice == "4":
            if not courses:
                print("\n  No grades to save yet.")
            else:
                results = calculate_results(courses)
                gpa     = calculate_gpa(results)
                print("\n  Save options:")
                print("    1. Create a new report file (default)")
                print("    2. Overwrite an existing report file")
                save_choice = input("  Choose (1 or 2): ").strip()
                if save_choice == "2":
                    existing = input("  Enter the filename to overwrite (e.g. output/grade_report_20260410_120606.csv): ").strip()
                    if not existing:
                        print("  No filename entered. Creating new file instead.")
                        save_report(results, gpa)
                    else:
                        save_report(results, gpa, filename=existing)
                else:
                    save_report(results, gpa)
        elif choice == "5":
            courses = {}
            print("\n  All grades cleared.")
        elif choice == "6":
            print("\n  Goodbye!\n")
            break
        else:
            print("\n  Invalid option. Enter a number from 1 to 6.")


if __name__ == "__main__":
    main()