"""
Fixed Goal Classifier — All cells as a runnable Python script.
Fixes Python 3.14 + pandas Arrow backend compatibility with sklearn.
Run from: career-mentor/ml/
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import joblib
import json
import warnings
warnings.filterwarnings('ignore')

import matplotlib
matplotlib.use('Agg')  # non-interactive backend — no popup windows
import matplotlib.pyplot as plt

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, f1_score, classification_report,
    confusion_matrix, ConfusionMatrixDisplay
)

DATA_DIR   = '../data'
MODEL_DIR  = 'models'
REPORT_DIR = 'reports'
os.makedirs(MODEL_DIR,  exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# ── 1. Load Data ──────────────────────────────────────────────────────────────
print("=" * 55)
print("  STEP 1: Data Loading")
print("=" * 55)

df = pd.read_csv(f'{DATA_DIR}/goal_texts.csv')
print(f"Total samples : {len(df)}")
print(f"Columns       : {list(df.columns)}")
print(f"\nClass distribution:")
print(df['career'].value_counts().to_string())

# ── 2. Train/Test Split ───────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  STEP 2: Train / Test Split")
print("=" * 55)

# FIX: Use .to_numpy() instead of .values to avoid Arrow backend issue
X = df['text'].to_numpy()
y = df['career'].to_numpy()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Train size : {len(X_train)}")
print(f"Test  size : {len(X_test)}")
print(f"Train counts: { dict(zip(*np.unique(y_train, return_counts=True))) }")
print(f"Test  counts: { dict(zip(*np.unique(y_test,  return_counts=True))) }")

# ── 3. TF-IDF + Logistic Regression ──────────────────────────────────────────
print("\n" + "=" * 55)
print("  STEP 3: TF-IDF + Logistic Regression")
print("=" * 55)

tfidf_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=5000,
        sublinear_tf=True,
        min_df=1
    )),
    ('clf', LogisticRegression(max_iter=500, C=1.0, random_state=42))
])

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(tfidf_pipeline, X_train, y_train, cv=cv, scoring='accuracy')
print(f"TF-IDF CV Accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

tfidf_pipeline.fit(X_train, y_train)
y_pred_tfidf = tfidf_pipeline.predict(X_test)
acc_tfidf = accuracy_score(y_test, y_pred_tfidf)
f1_tfidf  = f1_score(y_test, y_pred_tfidf, average='weighted')

print(f"\n[TF-IDF LR] Test Accuracy    : {acc_tfidf:.4f}")
print(f"[TF-IDF LR] Test F1 (weighted): {f1_tfidf:.4f}")
print()
print(classification_report(y_test, y_pred_tfidf))

# Confusion matrix plot
fig, ax = plt.subplots(figsize=(7, 5))
cm = confusion_matrix(y_test, y_pred_tfidf, labels=tfidf_pipeline.classes_)
ConfusionMatrixDisplay(cm, display_labels=tfidf_pipeline.classes_).plot(ax=ax, colorbar=False, cmap='Blues')
ax.set_title('Confusion Matrix - TF-IDF + LR')
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig(f'{REPORT_DIR}/cm_tfidf.png', bbox_inches='tight', dpi=120)
plt.close()
print(f"Confusion matrix saved: {REPORT_DIR}/cm_tfidf.png")

# ── 4. Sentence Embeddings + LR ───────────────────────────────────────────────
print("\n" + "=" * 55)
print("  STEP 4: Sentence Embeddings + Logistic Regression")
print("=" * 55)

from sentence_transformers import SentenceTransformer
print("Loading all-MiniLM-L6-v2 (first time ~90MB download)...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded!")

print("Encoding train set...")
X_train_emb = embedder.encode(X_train.tolist(), show_progress_bar=True, batch_size=32)
print("Encoding test set...")
X_test_emb  = embedder.encode(X_test.tolist(),  show_progress_bar=True, batch_size=32)
print(f"Embedding shape: {X_train_emb.shape}")

emb_clf = LogisticRegression(max_iter=500, C=5.0, random_state=42)
cv_emb  = cross_val_score(emb_clf, X_train_emb, y_train, cv=cv, scoring='accuracy')
print(f"\nEmbedding CV Accuracy: {cv_emb.mean():.4f} ± {cv_emb.std():.4f}")

emb_clf.fit(X_train_emb, y_train)
y_pred_emb = emb_clf.predict(X_test_emb)
acc_emb = accuracy_score(y_test, y_pred_emb)
f1_emb  = f1_score(y_test, y_pred_emb, average='weighted')

print(f"\n[Embedding LR] Test Accuracy    : {acc_emb:.4f}")
print(f"[Embedding LR] Test F1 (weighted): {f1_emb:.4f}")
print()
print(classification_report(y_test, y_pred_emb))

# Confusion matrix
fig, ax = plt.subplots(figsize=(7, 5))
cm2 = confusion_matrix(y_test, y_pred_emb, labels=emb_clf.classes_)
ConfusionMatrixDisplay(cm2, display_labels=emb_clf.classes_).plot(ax=ax, colorbar=False, cmap='Purples')
ax.set_title('Confusion Matrix - Embedding + LR')
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig(f'{REPORT_DIR}/cm_embedding.png', bbox_inches='tight', dpi=120)
plt.close()
print(f"Confusion matrix saved: {REPORT_DIR}/cm_embedding.png")

# ── 5. Model Comparison ───────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  STEP 5: Model Comparison")
print("=" * 55)

results = {
    'TF-IDF + LR': {
        'accuracy': acc_tfidf, 'f1_weighted': f1_tfidf,
        'cv_mean': float(cv_scores.mean()), 'cv_std': float(cv_scores.std())
    },
    'Embedding + LR': {
        'accuracy': acc_emb, 'f1_weighted': f1_emb,
        'cv_mean': float(cv_emb.mean()), 'cv_std': float(cv_emb.std())
    }
}

print(f"{'Model':<20} {'Accuracy':>10} {'F1(wt)':>10} {'CV Mean':>10}")
print("-" * 55)
for name, m in results.items():
    print(f"{name:<20} {m['accuracy']:>10.4f} {m['f1_weighted']:>10.4f} {m['cv_mean']:>10.4f}")

# Bar chart
fig, ax = plt.subplots(figsize=(8, 4))
metrics = ['accuracy', 'f1_weighted']
x = np.arange(len(metrics))
w = 0.35
b1 = ax.bar(x - w/2, [results['TF-IDF + LR'][m] for m in metrics],  w, label='TF-IDF + LR', color='#4f46e5')
b2 = ax.bar(x + w/2, [results['Embedding + LR'][m] for m in metrics], w, label='Embedding + LR', color='#a855f7')
ax.set_xticks(x)
ax.set_xticklabels(['Accuracy', 'F1 (Weighted)'])
ax.set_ylim(0, 1.15)
ax.set_title('Goal Classifier - Model Comparison')
ax.legend()
for bar in list(b1) + list(b2):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.savefig(f'{REPORT_DIR}/model_comparison.png', bbox_inches='tight', dpi=120)
plt.close()
print(f"\nComparison chart saved: {REPORT_DIR}/model_comparison.png")

with open(f'{REPORT_DIR}/goal_classifier_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f"Results JSON saved: {REPORT_DIR}/goal_classifier_results.json")

# ── 6. Save Best Model ────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  STEP 6: Save Best Model")
print("=" * 55)

best_name = max(results, key=lambda k: results[k]['f1_weighted'])
print(f"Best model: {best_name}")

# Always save TF-IDF pipeline (lightweight, no GPU needed)
joblib.dump(tfidf_pipeline, f'{MODEL_DIR}/goal_classifier.joblib')
joblib.dump(tfidf_pipeline.named_steps['tfidf'], f'{MODEL_DIR}/tfidf_vectorizer.joblib')
joblib.dump(tfidf_pipeline.named_steps['clf'],   f'{MODEL_DIR}/goal_clf_lr.joblib')
print(f"Saved: {MODEL_DIR}/goal_classifier.joblib")
print(f"Saved: {MODEL_DIR}/tfidf_vectorizer.joblib")
print(f"Saved: {MODEL_DIR}/goal_clf_lr.joblib")

if best_name == 'Embedding + LR':
    joblib.dump(emb_clf, f'{MODEL_DIR}/goal_classifier_emb.joblib')
    joblib.dump(embedder, f'{MODEL_DIR}/sentence_embedder.joblib')
    print(f"Saved: {MODEL_DIR}/goal_classifier_emb.joblib")
    print(f"Saved: {MODEL_DIR}/sentence_embedder.joblib")

# ── 7. Inference Test ─────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  STEP 7: Quick Inference Test")
print("=" * 55)

test_sentences = [
    'mujhe data science seekhna hai',
    'I want to build websites with React',
    'main MERN stack developer banna chahta hoon',
    'machine learning mein career banana hai',
    'mujhe frontend aur backend dono seekhne hain',
    'CSS aur HTML se website banana chahta hoon',
    'deep learning aur NLP mein interest hai',
    'complete web application banana chahta hoon',
]

loaded_pipe = joblib.load(f'{MODEL_DIR}/goal_classifier.joblib')
preds  = loaded_pipe.predict(test_sentences)
probas = loaded_pipe.predict_proba(test_sentences)
classes = loaded_pipe.classes_

for sent, pred, prob in zip(test_sentences, preds, probas):
    conf = prob.max()
    print(f"\n  Input  : \"{sent}\"")
    print(f"  Predict: {pred}  (conf: {conf:.1%})")

print("\n" + "=" * 55)
print("  ALL DONE! Phase 2 - Goal Classifier Complete")
print("=" * 55)
print(f"\n  Models in  : ml/models/")
print(f"  Reports in : ml/reports/")
