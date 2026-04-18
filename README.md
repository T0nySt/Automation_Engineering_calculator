# Grade Calculator & Alert System.

- A beginner Python automation project that tracks your grades, calculates your GPA, and warns you when you're at risk.

---

## How to Run

1. Make sure Python 3 is installed.
2. Open this folder in VS Code
3. Open the terminal (View → Terminal)
4. Run:

```
python grades.py

```

---

## Features

- Add grades manually through a menu.
- Load grades from a CSV file.
- See your average, letter grade, and GPA per course.
- Get warnings if any course or your overall GPA is below the threshold.
- Automtes a file where you can save your report to a CSV file.

---

## Using the CSV File

The included `grades.csv` has sample data. Format:

| Course  | Assignment | Score | Max_Score | Weight |
| ------- | ---------- | ----- | --------- | ------ |
| MATH101 | Midterm    | 78    | 100       | 0.30   |

- **Weight** is a decimal (0.30 = 30% of your grade)
- All weights for a course should add up to 1.0

---

## Changing the Thresholds

Edit `config.json` to change when alerts trigger:

```json
{
  "gpa_threshold": 2.0,
  "grade_threshold": 70.0
}
```

- `grade_threshold`: minimum course average before a warning (default 70%)
- `gpa_threshold`: minimum cumulative GPA before a warning (default 2.0)

---

## Files

| File        | What it does                         |
| ----------- | ------------------------------------ |
| grades.py   | Main program — run this              |
| grades.csv  | Sample grade data                    |
| config.json | Alert threshold settings             |
| output/     | Saved reports go here (auto-created) |
