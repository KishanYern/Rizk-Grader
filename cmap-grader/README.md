# CXL Concept Map Grader

Automated grading tool for CXL concept map submissions from Canvas LMS.

## Requirements

-   **Python 3.x**
-   **Input File**: `submissions.zip` (Canvas mass download)

## Usage

```powershell
python grader.py <ASSIGNMENT_NAME> <SECTION>
```

### Arguments

| Argument          | Description                           | Options                          |
| ----------------- | ------------------------------------- | -------------------------------- |
| `ASSIGNMENT_NAME` | **Exact** assignment name from Canvas | e.g., `CMAP0`, `"Concept Map 1"` |
| `SECTION`         | Course section                        | `DS1` or `DS2`                   |

> **Note**: The assignment name must match the Canvas assignment name exactly. For multi-word names, wrap in quotes.

### Examples

```powershell
# Single word assignment
python grader.py CMAP0 DS1

# Multi-word assignment name (use quotes)
python grader.py "Concept Map 1" DS1
```

## Input

### `submissions.zip`

Download directly from Canvas:

1. Go to the assignment page in Canvas
2. Click **Download Submissions**
3. Save as `submissions.zip` in this folder

Expected filename pattern inside zip:

```
studentname_canvasid_submissionid_originalfilename.ext
```

**Required student files:**

-   `.cxl` file (preferred) or `.cmap` file (concept map data)
-   Image file (`.pdf`, `.jpg`, `.png`)

> **Note**: Both `.cxl` and `.cmap` files are accepted, but `.cxl` is preferred. Students who upload `.cmap` files will receive a warning in the report.

## Output

### 1. `<ASSIGNMENT>_<SECTION>_grades.csv`

Canvas-compatible CSV for grade import:

```csv
Student,ID,SIS User ID,SIS Login ID,Section,CMAP0
Points Possible,,,,,100
studentname,12345,,,COSC3337 18978 - Data Science I,42
```

### 2. `<ASSIGNMENT>_<SECTION>_report.csv`

Reference file for students with issues:

```csv
Student Name,Canvas ID,Score,Comments
studentname,12345,0,"Missing .cxl file"
```

## Grading Criteria

### Simple Score Formula

```
Score = NC + 5 × HH
```

-   **NC**: Number of Concepts
-   **HH**: Highest Hierarchy (max depth from root)

### Error Check

-   Exactly one root concept required
-   Multiple roots/orphans → Score = 0

### Penalties

| Issue               | Penalty |
| ------------------- | ------- |
| Missing `.cxl` file | -20     |
| Missing image file  | -20     |

### Score Bounds

-   **Minimum**: 0
-   **Maximum**: 100

## Sections

| Code  | Full Name                        |
| ----- | -------------------------------- |
| `DS1` | COSC3337 18978 - Data Science I  |
| `DS2` | COSC4337 20367 - Data Science II |

> **Note**: Section codes change each semester. Update the `SECTIONS` dictionary in `grader.py` if these are incorrect for your current semester.
