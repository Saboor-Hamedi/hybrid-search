# ============================================================
# CELL 1: Imports & Style
# ============================================================
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from IPython.display import display
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

warnings.filterwarnings('ignore')

sns.set_theme(style="whitegrid", context="talk")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 11

# ============================================================
# CELL 2: Load and Prepare Data
# ============================================================
df = pd.read_csv('ai_judge.csv')

print("="*80)
print("DATA LOADING - AI JUDGED VERSION")
print("="*80)
print(f"✅ Loaded {len(df)} rows")
print(f"📊 Columns: {list(df.columns)}")
print(f"📊 Unique queries: {df['query'].nunique()}")

# Define methods
METHODS = {
    'Hybrid (Linear)': 'hybrid_linear',
    'Hybrid (RRF)': 'rrf',
    'Semantic (Dense)': 'semantic_only',
    'Keyword (BM25)': 'keyword_refined',
}

# Convert score columns to numeric
for prefix in METHODS.values():
    score_col = f'{prefix}_score'
    if score_col in df.columns:
        df[score_col] = pd.to_numeric(df[score_col], errors='coerce').fillna(0)

    latency_col = f'{prefix}_latency'
    if latency_col in df.columns:
        df[latency_col] = pd.to_numeric(df[latency_col], errors='coerce').fillna(0)

# Convert AI relevance to boolean
df['ai_relevant'] = df['ai_relevant'].astype(str).str.lower() == 'true'
print(f"📊 AI Relevance distribution:")
print(f"   Relevant documents: {df['ai_relevant'].sum()}/{len(df)} ({df['ai_relevant'].mean()*100:.1f}%)")

# ============================================================
# CELL 3: Aggregate per Query (Get best document per query)
# ============================================================
print("\n" + "="*80)
print("AGGREGATING RESULTS PER QUERY")
print("="*80)

query_results = []
for query in df['query'].unique():
    query_df = df[df['query'] == query]
    row = {'query': query}

    for label, prefix in METHODS.items():
        score_col = f'{prefix}_score'
        if score_col in query_df.columns:
            max_score = query_df[score_col].max()
            row[label] = max_score if max_score > 0 else 0

            latency_col = f'{prefix}_latency'
            if latency_col in query_df.columns:
                latencies = query_df[query_df[score_col] > 0][latency_col]
                row[f'{label}_latency'] = latencies.mean() if len(latencies) > 0 else 0

    # Get AI ground truth for this query (if any document is relevant)
    row['ai_ground_truth'] = query_df['ai_relevant'].any()
    row['ai_max_score'] = query_df['ai_score'].max() if 'ai_score' in query_df.columns else 0

    query_results.append(row)

df_queries = pd.DataFrame(query_results)
print(f"✅ Aggregated to {len(df_queries)} unique queries")
print(f"📊 Queries with relevant documents (by AI): {df_queries['ai_ground_truth'].sum()}/{len(df_queries)}")

# ============================================================
# CELL 4: Winner Distribution (AI Ground Truth)
# ============================================================
print("\n" + "="*80)
print("WINNER DISTRIBUTION (Based on AI Relevance)")
print("="*80)

# Determine winner for each query based on which algorithm found relevant documents
winners = []
for idx, row in df_queries.iterrows():
    # Check which algorithms found relevant documents for this query
    query_df = df[df['query'] == row['query']]
    algo_found_relevant = {}

    for label, prefix in METHODS.items():
        score_col = f'{prefix}_score'
        if score_col in df.columns:
            # Get documents with scores > 0 for this query
            query_docs = query_df[query_df[score_col] > 0]
            # Check if any of these documents are relevant according to AI
            relevant_found = query_docs['ai_relevant'].any() if len(query_docs) > 0 else False
            algo_found_relevant[label] = relevant_found

    # Winner is algorithm that found relevant docs
    if any(algo_found_relevant.values()):
        # If multiple found relevant, choose one with highest score for relevant docs
        best_algo = max([label for label, found in algo_found_relevant.items() if found],
                       key=lambda x: query_df[query_df['ai_relevant']][f'{METHODS[x]}_score'].max()
                       if len(query_df[query_df['ai_relevant']]) > 0 else 0)
        winners.append(best_algo)
    else:
        winners.append('None')

win_counts = pd.Series([w for w in winners if w != 'None']).value_counts().reset_index()
if len(win_counts) > 0:
    win_counts.columns = ['Algorithm', 'Wins']
    win_counts['Percentage'] = (win_counts['Wins'] / len([w for w in winners if w != 'None']) * 100).round(1)
else:
    win_counts = pd.DataFrame(columns=['Algorithm', 'Wins', 'Percentage'])

# Ensure all algorithms appear
for algo in METHODS.keys():
    if algo not in win_counts['Algorithm'].values:
        win_counts = pd.concat([win_counts, pd.DataFrame({'Algorithm': [algo], 'Wins': [0], 'Percentage': [0]})], ignore_index=True)

win_counts = win_counts.sort_values('Wins', ascending=False)

print(f"Total queries where relevant documents exist: {df_queries['ai_ground_truth'].sum()}")
print(f"Queries where algorithms found relevant docs: {len([w for w in winners if w != 'None'])}")
print("\n🏆 WINNER TABLE (Best at finding AI-relevant documents):")
print(win_counts.to_string(index=False))

# Create winner chart
fig, ax = plt.subplots(figsize=(10, 6))
colors = sns.color_palette('viridis', len(win_counts))
bars = ax.bar(win_counts['Algorithm'], win_counts['Wins'], color=colors, edgecolor='black', linewidth=1.5)

for bar, win, pct in zip(bars, win_counts['Wins'], win_counts['Percentage']):
    if win > 0:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{win} wins\n({pct:.1f}%)',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

ax.set_title('🏆 Algorithm Performance: Finding AI-Relevant Documents',
             fontsize=16, fontweight='bold', pad=20)
ax.set_ylabel('Number of Queries Where Relevant Docs Found', fontsize=13, fontweight='bold')
ax.set_xlabel('Search Algorithm', fontsize=13, fontweight='bold')
plt.xticks(rotation=15, ha='right')
sns.despine()
plt.tight_layout()
plt.show()

# ============================================================
# CELL 5: Classification Metrics (Against AI Ground Truth)
# ============================================================
print("\n" + "="*80)
print("CLASSIFICATION METRICS (vs AI Judge)")
print("="*80)

# For each algorithm, predict relevance based on score > 0
metrics_results = []
for label, prefix in METHODS.items():
    score_col = f'{prefix}_score'
    if score_col in df.columns:
        df[f'{label}_pred'] = df[score_col] > 0

        y_true = df['ai_relevant']
        y_pred = df[f'{label}_pred']

        metrics_results.append({
            'Algorithm': label,
            'Accuracy': accuracy_score(y_true, y_pred),
            'Precision': precision_score(y_true, y_pred, zero_division=0),
            'Recall': recall_score(y_true, y_pred, zero_division=0),
            'F1-Score': f1_score(y_true, y_pred, zero_division=0),
        })

df_metrics = pd.DataFrame(metrics_results)
df_metrics = df_metrics.sort_values('F1-Score', ascending=False)

print("\n📊 CLASSIFICATION METRICS TABLE (Compared to AI Judgments):")
print(df_metrics.to_string(index=False))
print("\n" + "-"*80)
display(df_metrics.style.background_gradient(cmap='Blues').format({
    'Accuracy': '{:.2%}', 'Precision': '{:.2%}', 'Recall': '{:.2%}', 'F1-Score': '{:.2%}'
}))

# ============================================================
# CELL 6: Metrics Comparison Bar Chart
# ============================================================
fig, ax = plt.subplots(figsize=(14, 7))
df_melted = df_metrics.melt(id_vars='Algorithm',
                             value_vars=['Accuracy', 'Precision', 'F1-Score'],
                             var_name='Metric', value_name='Score')

sns.barplot(x='Algorithm', y='Score', hue='Metric', data=df_melted,
            palette='Set2', edgecolor='black', linewidth=1.5, ax=ax)

for container in ax.containers:
    for bar in container:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{height:.1%}',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')

ax.set_title('📊 Algorithm Performance vs AI Judge\n(Accuracy, Precision & F1-Score)',
             fontsize=18, fontweight='bold', pad=20)
ax.set_ylabel('Score', fontsize=14, fontweight='bold')
ax.set_xlabel('Search Algorithm', fontsize=14, fontweight='bold')
ax.set_ylim(0, 1.15)
ax.legend(title='Metric', fontsize=11, title_fontsize=12, loc='upper right')
ax.grid(axis='y', linestyle='--', alpha=0.3)
plt.xticks(rotation=15, ha='right')
sns.despine()
plt.tight_layout()
plt.show()

# ============================================================
# CELL 7: Confusion Matrices for Each Algorithm
# ============================================================
print("\n" + "="*80)
print("CONFUSION MATRICES")
print("="*80)

fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes = axes.flatten()

for idx, (label, prefix) in enumerate(METHODS.items()):
    if idx < 4:
        y_true = df['ai_relevant']
        y_pred = df[f'{label}_pred']
        cm = confusion_matrix(y_true, y_pred)

        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx],
                   xticklabels=['Not Relevant', 'Relevant'],
                   yticklabels=['Not Relevant', 'Relevant'],
                   annot_kws={'size': 14, 'weight': 'bold'})
        axes[idx].set_title(f'{label}\nAccuracy: {accuracy_score(y_true, y_pred):.1%}',
                           fontsize=12, fontweight='bold')
        axes[idx].set_xlabel('Predicted', fontsize=11)
        axes[idx].set_ylabel('Actual (AI Judge)', fontsize=11)

plt.suptitle('Confusion Matrices: Algorithm Predictions vs AI Judge',
             fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.show()

# ============================================================
# CELL 8: Coherency Matrix (Agreement between algorithms)
# ============================================================
print("\n" + "="*80)
print("COHERENCY MATRIX (Algorithm Agreement)")
print("="*80)

algorithms = list(METHODS.keys())
n = len(algorithms)
coh_matrix = pd.DataFrame(index=algorithms, columns=algorithms, dtype=float)

for i, algo1 in enumerate(algorithms):
    for j, algo2 in enumerate(algorithms):
        pred1 = df[f'{algo1}_pred']
        pred2 = df[f'{algo2}_pred']
        coh_matrix.iloc[i, j] = accuracy_score(pred1, pred2)

print("\n🔄 COHERENCY MATRIX (% agreement between algorithms):")
print(coh_matrix.to_string())
print("\n" + "-"*80)

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(coh_matrix.astype(float), annot=True, fmt='.1%', cmap='Purples',
            linewidths=2, linecolor='white', square=True,
            cbar_kws={'label': 'Agreement Percentage', 'shrink': 0.8},
            annot_kws={"size": 12, "weight": "bold"}, ax=ax)

ax.set_title("🔄 Algorithm Coherency Matrix\nHow Often Do Algorithms Agree?",
             fontsize=16, fontweight='bold', pad=20)
ax.set_xlabel('Algorithm', fontsize=13, fontweight='bold')
ax.set_ylabel('Algorithm', fontsize=13, fontweight='bold')
plt.xticks(rotation=45, ha='right', fontsize=11)
plt.yticks(rotation=0, fontsize=11)
plt.tight_layout()
plt.show()

# ============================================================
# CELL 9: Average Scores Analysis
# ============================================================
print("\n" + "="*80)
print("AVERAGE SCORES ANALYSIS")
print("="*80)

avg_scores = []
for label in METHODS.keys():
    scores = df[df[f'{label}_pred']][label] if len(df[df[f'{label}_pred']]) > 0 else df[label]
    if len(scores) > 0:
        avg_scores.append({
            'Algorithm': label,
            'Average Score': scores.mean(),
            'Median Score': scores.median(),
            'Std Dev': scores.std(),
            'Queries with Results': len(df[df[label] > 0]),
            'Coverage %': (len(df[df[label] > 0]) / len(df)) * 100
        })

df_avg_scores = pd.DataFrame(avg_scores).sort_values('Average Score', ascending=False)

print("\n📈 AVERAGE SCORES TABLE:")
print(df_avg_scores.to_string(index=False))

fig, ax = plt.subplots(figsize=(10, 6))
colors = sns.color_palette('coolwarm', len(df_avg_scores))
bars = ax.bar(df_avg_scores['Algorithm'], df_avg_scores['Average Score'],
              color=colors, edgecolor='black', linewidth=1.5)

for bar, score in zip(bars, df_avg_scores['Average Score']):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
            f'{score:.3f}',
            ha='center', va='bottom', fontsize=11, fontweight='bold')

ax.set_title('📈 Average Relevance Scores by Algorithm',
             fontsize=16, fontweight='bold', pad=20)
ax.set_ylabel('Average Score (0-1 scale)', fontsize=13, fontweight='bold')
ax.set_xlabel('Search Algorithm', fontsize=13, fontweight='bold')
plt.xticks(rotation=15, ha='right')
sns.despine()
plt.tight_layout()
plt.show()

# ============================================================
# CELL 10: Latency Analysis
# ============================================================
print("\n" + "="*80)
print("LATENCY ANALYSIS")
print("="*80)

latency_data = []
for label in METHODS.keys():
    latency_col = f'{label}_latency'
    if latency_col in df.columns:
        latencies = df[df[latency_col] > 0][latency_col]
        if len(latencies) > 0:
            latency_data.append({
                'Algorithm': label,
                'Avg Latency (ms)': latencies.mean(),
                'Median Latency (ms)': latencies.median(),
                'Min Latency (ms)': latencies.min(),
                'Max Latency (ms)': latencies.max()
            })

if latency_data:
    df_latency = pd.DataFrame(latency_data).sort_values('Avg Latency (ms)', ascending=True)

    print("\n⏱️ LATENCY TABLE (Lower is better):")
    print(df_latency.to_string(index=False))

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = sns.color_palette('RdYlGn_r', len(df_latency))
    bars = ax.barh(df_latency['Algorithm'], df_latency['Avg Latency (ms)'],
                   color=colors, edgecolor='black', linewidth=1.5)

    for bar, val in zip(bars, df_latency['Avg Latency (ms)']):
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
                f'{val:.0f} ms', va='center', fontsize=11, fontweight='bold')

    ax.set_title('⏱️ Average Search Latency by Algorithm\n(Lower is Better)',
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Milliseconds (ms)', fontsize=13, fontweight='bold')
    ax.set_ylabel('')
    ax.set_xlim(0, df_latency['Avg Latency (ms)'].max() * 1.15)
    sns.despine()
    plt.tight_layout()
    plt.show()

# ============================================================
# CELL 11: Precision-Recall Tradeoff Analysis
# ============================================================
print("\n" + "="*80)
print("PRECISION-RECALL ANALYSIS")
print("="*80)

# Calculate precision and recall at different thresholds
thresholds = np.arange(0.1, 1.0, 0.1)
pr_data = []

for label in METHODS.keys():
    scores = df[label].values
    y_true = df['ai_relevant'].values

    for thresh in thresholds:
        y_pred = scores > thresh
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        pr_data.append({
            'Algorithm': label,
            'Threshold': thresh,
            'Precision': prec,
            'Recall': rec
        })

df_pr = pd.DataFrame(pr_data)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Precision-Recall Curve
for label in METHODS.keys():
    subset = df_pr[df_pr['Algorithm'] == label]
    axes[0].plot(subset['Recall'], subset['Precision'], 'o-', linewidth=2,
                markersize=8, label=label)
axes[0].set_xlabel('Recall', fontsize=13, fontweight='bold')
axes[0].set_ylabel('Precision', fontsize=13, fontweight='bold')
axes[0].set_title('Precision-Recall Tradeoff', fontsize=14, fontweight='bold')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Precision vs Threshold
for label in METHODS.keys():
    subset = df_pr[df_pr['Algorithm'] == label]
    axes[1].plot(subset['Threshold'], subset['Precision'], 'o-', linewidth=2,
                markersize=8, label=f'{label} (Precision)')
    axes[1].plot(subset['Threshold'], subset['Recall'], 's--', linewidth=2,
                markersize=8, label=f'{label} (Recall)')
axes[1].set_xlabel('Score Threshold', fontsize=13, fontweight='bold')
axes[1].set_ylabel('Score', fontsize=13, fontweight='bold')
axes[1].set_title('Precision & Recall vs Threshold', fontsize=14, fontweight='bold')
axes[1].legend(loc='center left', bbox_to_anchor=(1, 0.5))
axes[1].grid(True, alpha=0.3)

plt.suptitle('Precision-Recall Analysis by Algorithm', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.show()

# ============================================================
# CELL 12: Final Summary Dashboard
# ============================================================
print("\n" + "="*80)
print("FINAL SUMMARY DASHBOARD (AI Judge Ground Truth)")
print("="*80)

# Create summary DataFrame
summary = df_metrics[['Algorithm', 'Accuracy', 'Precision', 'Recall', 'F1-Score']].copy()
summary = summary.merge(df_avg_scores[['Algorithm', 'Average Score', 'Coverage %']], on='Algorithm', how='left')
summary = summary.merge(win_counts[['Algorithm', 'Wins', 'Percentage']], on='Algorithm', how='left')
summary = summary.fillna(0)

# Calculate overall score
max_f1 = summary['F1-Score'].max() if summary['F1-Score'].max() > 0 else 1
max_avg = summary['Average Score'].max() if summary['Average Score'].max() > 0 else 1

summary['Overall Score'] = (summary['F1-Score'] / max_f1) * 0.4 + \
                           (summary['Average Score'] / max_avg) * 0.3 + \
                           (summary['Percentage'] / 100) * 0.3
summary = summary.sort_values('Overall Score', ascending=False)

print("\n🏆 ALGORITHM RANKING (by Overall Performance vs AI Judge):")
for idx, row in summary.iterrows():
    print(f"\n{idx+1}. {row['Algorithm']}:")
    print(f"   • Accuracy: {row['Accuracy']:.2%}")
    print(f"   • Precision: {row['Precision']:.2%}")
    print(f"   • Recall: {row['Recall']:.2%}")
    print(f"   • F1-Score: {row['F1-Score']:.2%}")
    print(f"   • Avg Score: {row['Average Score']:.4f}")
    print(f"   • Win Rate (finding relevant docs): {row['Percentage']:.1f}% ({int(row['Wins'])} wins)")
    print(f"   • Coverage: {row['Coverage %']:.1f}%")
    print(f"   • Overall Score: {row['Overall Score']:.4f}")

print("\n" + "="*80)
print("COMPLETE METRICS SUMMARY")
print("="*80)
display(summary.style.background_gradient(cmap='RdYlGn', subset=['Overall Score', 'F1-Score']).format({
    'Accuracy': '{:.2%}',
    'Precision': '{:.2%}',
    'Recall': '{:.2%}',
    'F1-Score': '{:.2%}',
    'Average Score': '{:.4f}',
    'Coverage %': '{:.1f}%',
    'Percentage': '{:.1f}%',
    'Wins': '{:.0f}',
    'Overall Score': '{:.4f}'
}))

# ============================================================
# CELL 13: Per-Query Detailed Results
# ============================================================
print("\n" + "="*80)
print("PER-QUERY DETAILED RESULTS")
print("="*80)

for idx, row in df_queries.iterrows():
    print(f"\n📋 Query: {row['query']}")
    print(f"   AI Ground Truth: {'RELEVANT DOCUMENTS EXIST' if row['ai_ground_truth'] else 'NO RELEVANT DOCS'}")
    print(f"   AI Max Score: {row['ai_max_score']}")
    print("\n   Algorithm Performance:")

    for label in METHODS.keys():
        # Get documents for this query
        query_df = df[df['query'] == row['query']]
        score_col = METHODS[label]

        # Check if algorithm found any relevant docs
        docs_with_results = query_df[query_df[score_col] > 0]
        relevant_found = docs_with_results['ai_relevant'].any() if len(docs_with_results) > 0 else False

        max_score = row[label]
        print(f"   • {label}: Max Score={max_score:.4f}, Found Relevant={relevant_found}")

    print(f"   Winner: {winners[idx] if idx < len(winners) else 'Unknown'}")

# ============================================================
# CELL 14: Key Insights & Recommendations
# ============================================================
print("\n" + "="*80)
print("KEY INSIGHTS & RECOMMENDATIONS")
print("="*80)

# Calculate key metrics for insights
best_algorithm = summary.iloc[0]['Algorithm']
best_f1 = summary.iloc[0]['F1-Score']
best_precision = summary.iloc[0]['Precision']
best_recall = summary.iloc[0]['Recall']

print(f"""
📊 ANALYSIS SUMMARY:

1. BEST OVERALL ALGORITHM: {best_algorithm}
   - F1-Score: {best_f1:.2%}
   - Precision: {best_precision:.2%}
   - Recall: {best_recall:.2%}

2. KEY FINDINGS:
   - The AI judge provides ground truth labels for document relevance
   - {summary.iloc[0]['Algorithm']} performs best at finding AI-relevant documents
   - Semantic search shows {df_metrics[df_metrics['Algorithm']=='Semantic (Dense)']['Precision'].values[0]:.1%} precision
   - Keyword search has {df_metrics[df_metrics['Algorithm']=='Keyword (BM25)']['Coverage %'].values[0]:.1f}% coverage

3. RECOMMENDATIONS:
   - Use {best_algorithm} as primary search algorithm
   - Adjust score thresholds based on precision/recall tradeoff needs
   - For high precision applications, increase threshold
   - For high recall applications, lower threshold or use hybrid approaches

4. NEXT STEPS:
   - Fine-tune semantic search to improve precision
   - Investigate why some algorithms miss relevant documents
   - Consider ensemble methods combining multiple algorithms
""")

print("\n" + "="*80)
print("✅ Analysis Complete!")
print("="*80)
