"""
Lightweight debug: checks each cell for syntax errors and
runs non-plotting cells to find the exact failure point.
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import json, ast, traceback

nb = json.load(open('01_goal_classifier.ipynb', encoding='utf-8'))
code_cells = [(i, ''.join(c['source'])) for i, c in enumerate(nb['cells']) if c['cell_type'] == 'code']

print(f"=== STEP 1: Syntax check all {len(code_cells)} code cells ===\n")
syntax_ok = True
for idx, (cell_num, src) in enumerate(code_cells):
    try:
        ast.parse(src)
        print(f"  Cell [{cell_num}] #{idx+1}: SYNTAX OK  | {src.splitlines()[0][:60]}")
    except SyntaxError as e:
        print(f"  Cell [{cell_num}] #{idx+1}: SYNTAX ERROR at line {e.lineno}: {e.msg}")
        print(f"    -> {e.text}")
        syntax_ok = False

print()
print("=== STEP 2: Check Python version & key imports ===\n")
print(f"  Python: {sys.version}")

imports_to_check = [
    "import pandas as pd",
    "import numpy as np",
    "import joblib",
    "from sklearn.linear_model import LogisticRegression",
    "from sklearn.pipeline import Pipeline",
    "from sklearn.feature_extraction.text import TfidfVectorizer",
    "from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold",
    "from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix, ConfusionMatrixDisplay",
    "import matplotlib",
    "from sentence_transformers import SentenceTransformer",
]

for imp in imports_to_check:
    try:
        exec(imp)
        mod = imp.split()[-1].split('.')[0]
        print(f"  OK  : {imp}")
    except ImportError as e:
        print(f"  FAIL: {imp}")
        print(f"        -> {e}")
    except Exception as e:
        print(f"  ERR : {imp} -> {e}")

print()
print("=== STEP 3: Check data file ===\n")
try:
    import pandas as pd
    df = pd.read_csv('../data/goal_texts.csv')
    print(f"  goal_texts.csv: {len(df)} rows, columns={list(df.columns)}")
    print(f"  Career counts:\n{df['career'].value_counts().to_string()}")
except Exception as e:
    print(f"  ERROR reading data: {e}")

print()
print("=== STEP 4: Quick TF-IDF pipeline smoke test ===\n")
try:
    import pandas as pd, numpy as np
    from sklearn.pipeline import Pipeline
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, f1_score, classification_report

    df = pd.read_csv('../data/goal_texts.csv')
    X, y = df['text'].values, df['career'].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    pipe = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1,2), max_features=5000, sublinear_tf=True, min_df=1)),
        ('clf', LogisticRegression(max_iter=500, C=1.0, random_state=42))
    ])
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1  = f1_score(y_test, y_pred, average='weighted')
    print(f"  TF-IDF LR Accuracy : {acc:.4f}")
    print(f"  TF-IDF LR F1       : {f1:.4f}")
    print(f"\n  Classification Report:")
    print(classification_report(y_test, y_pred))

    import joblib, os
    os.makedirs('models', exist_ok=True)
    joblib.dump(pipe, 'models/goal_classifier.joblib')
    joblib.dump(pipe.named_steps['tfidf'], 'models/tfidf_vectorizer.joblib')
    joblib.dump(pipe.named_steps['clf'],   'models/goal_clf_lr.joblib')
    print("  Models saved to ml/models/ !")

except Exception as e:
    print(f"  PIPELINE ERROR: {type(e).__name__}: {e}")
    traceback.print_exc()
