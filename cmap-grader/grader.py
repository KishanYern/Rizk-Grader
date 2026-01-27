import os
import csv
import zipfile
import xml.etree.ElementTree as ET
import re
import argparse
from typing import Dict
from collections import deque

# Configuration
OUTPUT_FILE = 'graded_canvas_import.csv'
SUBMISSIONS_ZIP = 'submissions.zip'

# Section Mapping
SECTIONS = {
    'DS1': 'COSC3337 18978 - Data Science I',
    'DS2': 'COSC4337 20367 - Data Science II'
}

def normalize_text(text: str) -> str:
    """Normalize text by stripping whitespace and converting to lowercase."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip().lower()

def analyze_cxl_structure(content: bytes) -> Dict:
    """
    Parses CXL content and calculates the 'Simple Score'.
    Formula: NC + 5 * HH
    NC: Number of Concepts
    HH: Highest Hierarchy (Max depth from the single root)
    """
    try:
        root = ET.fromstring(content)
        def local_tag(tag): return tag.split('}')[-1] if '}' in tag else tag

        concept_labels = {} # id -> label
        phrase_ids = set()
        raw_adj = {} # id -> list of ids
        
        for elem in root.iter():
            tag = local_tag(elem.tag)
            if tag == 'concept':
                concept_labels[elem.get('id')] = normalize_text(elem.get('label'))
            elif tag == 'linking-phrase':
                phrase_ids.add(elem.get('id'))
            elif tag == 'connection':
                f, t = elem.get('from-id'), elem.get('to-id')
                if f and t:
                    if f not in raw_adj: raw_adj[f] = []
                    raw_adj[f].append(t)

        # Build Concept Graph
        adj = {c: [] for c in concept_labels}
        in_degree = {c: 0 for c in concept_labels}
        
        for cid in concept_labels:
            if cid in raw_adj:
                for mid in raw_adj[cid]:
                    if mid in phrase_ids:
                        if mid in raw_adj:
                            for dest in raw_adj[mid]:
                                if dest in concept_labels:
                                    adj[cid].append(dest)
                                    in_degree[dest] += 1
        
        # Detect Roots
        roots = [cid for cid, deg in in_degree.items() if deg == 0]
        
        nc = len(concept_labels)
        hh = 0
        
        if len(roots) != 1:
            root_labels = [concept_labels[r] for r in roots]
            return {
                'score': 0,
                'nc': nc,
                'hh': 0,
                'error': f"Nodes without TO links: {', '.join(root_labels)}"
            }
        
        # Calculate Hierarchy (BFS for max depth)
        start_node = roots[0]
        max_depth = 0
        visited = {start_node: 1}
        q = deque([(start_node, 1)])
        
        while q:
            curr, depth = q.popleft()
            max_depth = max(max_depth, depth)
            
            for neighbor in adj[curr]:
                if neighbor not in visited:
                    visited[neighbor] = depth + 1
                    q.append((neighbor, depth + 1))

        hh = max_depth
        score = nc + 5 * hh
        
        return {
            'score': score,
            'nc': nc,
            'hh': hh,
            'error': None
        }

    except Exception as e:
         return {'score': 0, 'nc': 0, 'hh': 0, 'error': f"Parsing Exception: {e}"}



def scan_submissions_zip(zip_path: str) -> Dict[str, Dict]:
    """
    Scans the submissions zip and groups files by student Canvas ID.
    Extracts student name from the filename.
    """
    students = {}
    # Pattern: studentname_canvasid_submissionid_originalfilename.ext
    pattern = re.compile(r'^(.*?)_(\d+)_(\d+)_(.*)$')

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for filename in zf.namelist():
                if filename.endswith('/'): continue
                
                match = pattern.match(filename)
                if match:
                    name_part, canvas_id, submission_id, original_name = match.groups()
                    
                    if canvas_id not in students:
                        students[canvas_id] = {
                            'name': name_part,
                            'cxl_content': None,
                            'image_file': None,
                            'error': None,
                            'score': 0,
                            'grade_data': None,
                            'uploaded_cmap': False
                        }
                    
                    student = students[canvas_id]
                    ext = os.path.splitext(filename)[1].lower()
                    
                    if ext == '.cxl':
                        content = zf.read(filename)
                        student['cxl_content'] = content
                        result = analyze_cxl_structure(content)
                        student['grade_data'] = result
                        if result['error']:
                            student['error'] = result['error']
                        else:
                            student['score'] = result['score']
                    
                    elif ext == '.cmap':
                        # .cmap files are not supported (Java binary format)
                        student['uploaded_cmap'] = True
                    
                    elif ext in ['.pdf', '.jpg', '.jpeg', '.png']:
                        student['image_file'] = filename
                        
    except zipfile.BadZipFile:
        print(f"Error: {zip_path} is not a valid zip file.")
        
    return students

def main():
    parser = argparse.ArgumentParser(description='Grade CXL Concept Maps')
    parser.add_argument('assignment', type=str, help='Assignment name (column header in Canvas CSV)')
    parser.add_argument('section', type=str, choices=['DS1', 'DS2'], help='Section: DS1 (Data Science I) or DS2 (Data Science II)')
    parser.add_argument('--zip', type=str, default=SUBMISSIONS_ZIP, help='Path to submissions zip')
    parser.add_argument('--output', type=str, default=OUTPUT_FILE, help='Output CSV filename')
    args = parser.parse_args()

    assignment_name = args.assignment
    section_code = args.section  # DS1 or DS2
    section_name = SECTIONS[section_code]
    zip_path = args.zip
    
    # Generate dynamic filenames
    output_file = f"{assignment_name}_{section_code}_grades.csv"
    report_file = f"{assignment_name}_{section_code}_report.csv"

    if not os.path.exists(zip_path):
        print(f"Error: {zip_path} not found.")
        return

    # 1. Scan and Grade
    print("Scanning and Grading Submissions...")
    students_data = scan_submissions_zip(zip_path)
    
    results = []
    
    print("\n--- Grading Summary ---")
    
    for canvas_id, data in students_data.items():
        name = data['name']
        cxl_present = data['cxl_content'] is not None
        img_present = data['image_file'] is not None
        
        penalty_deduction = 0
        penalty_reasons = []
        
        if not cxl_present:
            penalty_reasons.append("Missing .cxl file")
        if not img_present:
            penalty_reasons.append("Missing image file")
            
        if penalty_reasons:
            penalty_deduction = 20
            
        base_score = 0
        error_msg = data.get('error')
        
        # Check for .cmap uploads (invalid format)
        if data.get('uploaded_cmap') and not cxl_present:
            penalty_reasons.append("Uploaded .cmap file instead of .cxl")
        
        if cxl_present and data['grade_data']:
             if not error_msg:
                 base_score = data['score']
             else:
                 base_score = 0
                 penalty_reasons.append(f"Structure Error: {error_msg}")
        
        final_score = min(100, max(0, base_score - penalty_deduction))
        
        if error_msg or penalty_deduction > 0 or data.get('uploaded_cmap'):
            print(f"Student: {name} | Score: {final_score} | Comments: {', '.join(penalty_reasons)}")
        
        results.append({
            'canvas_id': canvas_id,
            'name': name,
            'final_score': final_score,
            'comments': '; '.join(penalty_reasons)
        })

    # 2. Write Output (Minimal CSV for Canvas Upload)
    # Format: Student,ID,SIS User ID,SIS Login ID,Section,<Assignment>
    
    header = ['Student', 'ID', 'SIS User ID', 'SIS Login ID', 'Section', assignment_name]
    
    rows = []
    # Add "Points Possible" row (Canvas expects this)
    rows.append(['Points Possible', '', '', '', '', 100])
    
    for res in results:
        # We only have: name, canvas_id, score
        # Canvas uses ID (canvas_id) to match. 
        # We set Student name from filename, ID from canvas_id.
        # SIS User ID & SIS Login ID are often the same as ID or unknown from zip.
        # Section is unknown from zip, leave blank.
        # Canvas will match by ID column.
        
        student_name = res['name']
        canvas_id = res['canvas_id']
        score = res['final_score']
        
        # Note: Canvas import primarily uses ID to match students.
        # If SIS User ID/Login ID are needed, they need to match exactly.
        # Since we don't have them, we leave them blank. Canvas should still match by ID.
        
        rows.append([student_name, canvas_id, '', '', section_name, score])

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
        
    print(f"\nGrading Complete. Output written to {output_file}")

    # 3. Generate Comments Report (for instructor reference)
    report_header = ['Student Name', 'Canvas ID', 'Score', 'Comments']
    report_rows = []
    
    for res in results:
        # Only include students with comments (issues)
        if res['comments']:
            report_rows.append([res['name'], res['canvas_id'], res['final_score'], res['comments']])
    
    if report_rows:
        with open(report_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(report_header)
            writer.writerows(report_rows)
        print(f"Comments report written to {report_file} ({len(report_rows)} students with issues)")

    # 4. Statistics Summary
    scores = [res['final_score'] for res in results]
    if scores:
        scores_sorted = sorted(scores)
        n = len(scores)
        mean = sum(scores) / n
        
        # Standard deviation
        variance = sum((x - mean) ** 2 for x in scores) / n
        std = variance ** 0.5
        
        # Quartiles
        def percentile(data, p):
            k = (len(data) - 1) * p / 100
            f = int(k)
            c = f + 1 if f + 1 < len(data) else f
            return data[f] + (k - f) * (data[c] - data[f])
        
        q1 = percentile(scores_sorted, 25)
        median = percentile(scores_sorted, 50)
        q3 = percentile(scores_sorted, 75)
        
        print("\n" + "=" * 40)
        print("GRADE STATISTICS")
        print("=" * 40)
        print(f"  Count:    {n}")
        print(f"  Mean:     {mean:.2f}")
        print(f"  Std Dev:  {std:.2f}")
        print(f"  Min:      {min(scores)}")
        print(f"  Q1:       {q1:.2f}")
        print(f"  Median:   {median:.2f}")
        print(f"  Q3:       {q3:.2f}")
        print(f"  Max:      {max(scores)}")
        print("=" * 40)

if __name__ == '__main__':
    main()
