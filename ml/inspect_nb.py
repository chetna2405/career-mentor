import json, sys
sys.stdout.reconfigure(encoding='utf-8')

nb = json.load(open('01_goal_classifier.ipynb', encoding='utf-8'))
print(f"Total cells: {len(nb['cells'])}\n")
for i, c in enumerate(nb['cells']):
    src = ''.join(c['source'])
    # strip emoji for safe printing
    preview = src[:120].replace('\n', ' | ')
    preview = preview.encode('ascii', errors='replace').decode('ascii')
    print(f"[{i:02d}] {c['cell_type']:8s} | {preview}")
