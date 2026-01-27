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

| Argument          | Description                       | Options                |
| ----------------- | --------------------------------- | ---------------------- |
| `ASSIGNMENT_NAME` | Assignment column name for Canvas | e.g., `CMAP0`, `CMAP1` |
| `SECTION`         | Course section                    | `DS1` or `DS2`         |

### Example

```powershell
python grader.py CMAP0 DS1
```

## Input

### `submissions.zip`

Canvas mass download containing student files. Expected filename pattern:

```
studentname_canvasid_submissionid_originalfilename.ext
```

**Required student files:**

-   `.cxl` file (concept map data)
-   Image file (`.pdf`, `.jpg`, `.png`)

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
