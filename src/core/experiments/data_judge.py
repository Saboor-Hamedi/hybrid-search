# ============================================================
# CELL 1: Imports & Style
# ============================================================
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from IPython.display import display
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

warnings.filterwarnings('ignore')

sns.set_theme(style="whitegrid", context="talk")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 11

# ============================================================
# CELL 2: Load and Prepare Data
# ============================================================
# Load the data
df = pd.read_csv('data_judge.csv')

print("="*80)
print("DATA LOADING")
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

# Convert score columns to numeric and handle N/A
for prefix in METHODS.values():
    score_col = f'{prefix}_score'
    if score_col in df.columns:
        df[score_col] = pd.to_numeric(df[score_col], errors='coerce').fillna(0)

    # Also convert latency if exists
    latency_col = f'{prefix}_latency'
    if latency_col in df.columns:
        df[latency_col] = pd.to_numeric(df[latency_col], errors='coerce').fillna(0)

# ============================================================
# CELL 3: Aggregate per Query (Get best document per query per algorithm)
# ============================================================
print("\n" + "="*80)
print("AGGREGATING RESULTS PER QUERY")
print("="*80)

# For each query, get the best score per algorithm
query_results = []
for query in df['query'].unique():
    query_df = df[df['query'] == query]
    row = {'query': query}

    for label, prefix in METHODS.items():
        score_col = f'{prefix}_score'
        if score_col in query_df.columns:
            # Get max score for this query (best document)
            max_score = query_df[score_col].max()
            row[label] = max_score if max_score > 0 else 0

            # Also get latency (use min latency for this query)
            latency_col = f'{prefix}_latency'
            if latency_col in query_df.columns:
                latencies = query_df[query_df[score_col] > 0][latency_col]
                row[f'{label}_latency'] = latencies.mean() if len(latencies) > 0 else 0

    query_results.append(row)

df_queries = pd.DataFrame(query_results)
print(f"✅ Aggregated to {len(df_queries)} unique queries")
print(f"\nSample aggregated data:")
print(df_queries.head())

# ============================================================
# CELL 4: Winner Distribution (Per Query - Which Algorithm Wins Most?)
# ============================================================
print("\n" + "="*80)
print("WINNER DISTRIBUTION ANALYSIS")
print("="*80)

# Determine winner for each query
winners = []
winner_scores = []
for idx, row in df_queries.iterrows():
    scores = {label: row[label] for label in METHODS.keys()}
    if max(scores.values()) > 0:  # Only if at least one algorithm found something
        winner = max(scores, key=scores.get)
        winners.append(winner)
        winner_scores.append(scores)

win_counts = pd.Series(winners).value_counts().reset_index()
win_counts.columns = ['Algorithm', 'Wins']
win_counts['Percentage'] = (win_counts['Wins'] / len(winners) * 100).round(1)
win_counts = win_counts.sort_values('Wins', ascending=False)

# Ensure all algorithms appear (even with 0 wins)
for algo in METHODS.keys():
    if algo not in win_counts['Algorithm'].values:
        win_counts = pd.concat([win_counts, pd.DataFrame({'Algorithm': [algo], 'Wins': [0], 'Percentage': [0]})], ignore_index=True)

win_counts = win_counts.sort_values('Wins', ascending=False)

print(f"Total queries evaluated: {len(winners)}")
print("\n🏆 WINNER TABLE:")
print(win_counts.to_string(index=False))
print("\n" + "-"*80)

# Create winner distribution chart
fig, ax = plt.subplots(figsize=(10, 6))
colors = sns.color_palette('viridis', len(win_counts))
bars = ax.bar(win_counts['Algorithm'], win_counts['Wins'], color=colors, edgecolor='black', linewidth=1.5)

# Add percentage labels on top of bars
for bar, win, pct in zip(bars, win_counts['Wins'], win_counts['Percentage']):
    if win > 0:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{win} wins\n({pct:.1f}%)',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

ax.set_title('🏆 Which Algorithm Wins Most Often?\n(Best score per query)',
             fontsize=16, fontweight='bold', pad=20)
ax.set_ylabel('Number of Queries Won', fontsize=13, fontweight='bold')
ax.set_xlabel('Search Algorithm', fontsize=13, fontweight='bold')
ax.set_ylim(0, win_counts['Wins'].max() * 1.2 if win_counts['Wins'].max() > 0 else 10)
plt.xticks(rotation=15, ha='right')
sns.despine()
plt.tight_layout()
plt.show()

# ============================================================
# CELL 5: Classification Metrics
# ============================================================
print("\n" + "="*80)
print("CLASSIFICATION METRICS")
print("="*80)

# Create ground truth based on Hybrid Linear (best performing reference)
threshold_percentile = 70
threshold = df_queries['Hybrid (Linear)'].quantile(threshold_percentile/100)
df_queries['ground_truth'] = df_queries['Hybrid (Linear)'] >= threshold

print(f"Ground Truth: Using Hybrid Linear scores >= {threshold_percentile}th percentile ({threshold:.3f})")
print(f"Relevant queries: {df_queries['ground_truth'].sum()}/{len(df_queries)} ({df_queries['ground_truth'].mean()*100:.1f}%)")

metrics_results = []
for label in METHODS.keys():
    algo_scores = df_queries[label]
    if algo_scores.max() > 0:
        # Use algorithm's own median as threshold
        algo_threshold = algo_scores[algo_scores > 0].median() if len(algo_scores[algo_scores > 0]) > 0 else 0
        df_queries[f'{label}_pred'] = algo_scores > algo_threshold

        y_true = df_queries['ground_truth']
        y_pred = df_queries[f'{label}_pred']

        metrics_results.append({
            'Algorithm': label,
            'Accuracy': accuracy_score(y_true, y_pred),
            'Precision': precision_score(y_true, y_pred, zero_division=0),
            'Recall': recall_score(y_true, y_pred, zero_division=0),
            'F1-Score': f1_score(y_true, y_pred, zero_division=0),
        })

df_metrics = pd.DataFrame(metrics_results)
df_metrics = df_metrics.sort_values('F1-Score', ascending=False)

print("\n📊 CLASSIFICATION METRICS TABLE:")
print(df_metrics.to_string(index=False))
print("\n" + "-"*80)
display(df_metrics.style.background_gradient(cmap='Blues').format({
    'Accuracy': '{:.2%}', 'Precision': '{:.2%}', 'Recall': '{:.2%}', 'F1-Score': '{:.2%}'
}))

# ============================================================
# CELL 6: Metrics Comparison Bar Chart (with percentages)
# ============================================================
fig, ax = plt.subplots(figsize=(14, 7))
df_melted = df_metrics.melt(id_vars='Algorithm',
                             value_vars=['Accuracy', 'Precision', 'F1-Score'],
                             var_name='Metric', value_name='Score')

# Create barplot
sns.barplot(x='Algorithm', y='Score', hue='Metric', data=df_melted,
            palette='Set2', edgecolor='black', linewidth=1.5, ax=ax)

# Add percentage labels on top of each bar
for container in ax.containers:
    for bar in container:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{height:.1%}',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')

ax.set_title('📊 Algorithm Performance Metrics\n(Accuracy, Precision & F1-Score)',
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
# CELL 7: Coherency Matrix (Agreement between algorithms)
# ============================================================
print("\n" + "="*80)
print("COHERENCY MATRIX (Agreement between algorithms)")
print("="*80)

algorithms = list(METHODS.keys())
n = len(algorithms)
coh_matrix = pd.DataFrame(index=algorithms, columns=algorithms, dtype=float)

for i, algo1 in enumerate(algorithms):
    for j, algo2 in enumerate(algorithms):
        pred1 = df_queries[f'{algo1}_pred'] if f'{algo1}_pred' in df_queries.columns else df_queries[algo1] > 0
        pred2 = df_queries[f'{algo2}_pred'] if f'{algo2}_pred' in df_queries.columns else df_queries[algo2] > 0
        coh_matrix.iloc[i, j] = accuracy_score(pred1, pred2)

print("\n🔄 COHERENCY MATRIX (% agreement):")
print(coh_matrix.to_string())
print("\n" + "-"*80)
display(coh_matrix.style.background_gradient(cmap='Purples').format("{:.1%}"))

# Create heatmap with percentages
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
# CELL 8: Average Score Bar Chart
# ============================================================
print("\n" + "="*80)
print("AVERAGE SCORES ANALYSIS")
print("="*80)

avg_scores = []
for label in METHODS.keys():
    scores = df_queries[df_queries[label] > 0][label]
    if len(scores) > 0:
        avg_scores.append({
            'Algorithm': label,
            'Average Score': scores.mean(),
            'Median Score': scores.median(),
            'Std Dev': scores.std(),
            'Min Score': scores.min(),
            'Max Score': scores.max(),
            'Queries with Results': len(scores),
            'Coverage %': (len(scores) / len(df_queries)) * 100
        })

df_avg_scores = pd.DataFrame(avg_scores).sort_values('Average Score', ascending=False)

print("\n📈 AVERAGE SCORES TABLE:")
print(df_avg_scores.to_string(index=False))
print("\n" + "-"*80)

fig, ax = plt.subplots(figsize=(10, 6))
colors = sns.color_palette('coolwarm', len(df_avg_scores))
bars = ax.bar(df_avg_scores['Algorithm'], df_avg_scores['Average Score'],
              color=colors, edgecolor='black', linewidth=1.5)

# Add value labels on top of bars
for bar, score in zip(bars, df_avg_scores['Average Score']):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
            f'{score:.3f}',
            ha='center', va='bottom', fontsize=11, fontweight='bold')

ax.set_title('📈 Average Relevance Scores by Algorithm',
             fontsize=16, fontweight='bold', pad=20)
ax.set_ylabel('Average Score (0-1 scale)', fontsize=13, fontweight='bold')
ax.set_xlabel('Search Algorithm', fontsize=13, fontweight='bold')
ax.set_ylim(0, df_avg_scores['Average Score'].max() * 1.15)
plt.xticks(rotation=15, ha='right')
sns.despine()
plt.tight_layout()
plt.show()

# ============================================================
# CELL 9: Latency Analysis
# ============================================================
print("\n" + "="*80)
print("LATENCY ANALYSIS")
print("="*80)

latency_data = []
for label in METHODS.keys():
    latency_col = f'{label}_latency'
    if latency_col in df_queries.columns:
        latencies = df_queries[df_queries[latency_col] > 0][latency_col]
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
    print("\n" + "-"*80)

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
# CELL 10: Final Summary Dashboard
# ============================================================
print("\n" + "="*80)
print("FINAL SUMMARY DASHBOARD")
print("="*80)

# Create summary DataFrame
summary = df_metrics[['Algorithm', 'Accuracy', 'Precision', 'Recall', 'F1-Score']].copy()
summary = summary.merge(df_avg_scores[['Algorithm', 'Average Score', 'Coverage %']], on='Algorithm', how='left')
summary = summary.merge(win_counts[['Algorithm', 'Wins', 'Percentage']], on='Algorithm', how='left')

# Fill NaN values
summary = summary.fillna(0)

# Calculate overall score (composite metric)
max_avg_score = summary['Average Score'].max() if summary['Average Score'].max() > 0 else 1
summary['Overall Score'] = (summary['F1-Score'] * 0.4 +
                            (summary['Average Score'] / max_avg_score) * 0.3 +
                            summary['Percentage'] / 100 * 0.3)
summary = summary.sort_values('Overall Score', ascending=False)

print("\n🏆 ALGORITHM RANKING (by Overall Performance):")
for idx, row in summary.iterrows():
    print(f"\n{idx+1}. {row['Algorithm']}:")
    print(f"   • Accuracy: {row['Accuracy']:.2%}")
    print(f"   • Precision: {row['Precision']:.2%}")
    print(f"   • Recall: {row['Recall']:.2%}")
    print(f"   • F1-Score: {row['F1-Score']:.2%}")
    print(f"   • Avg Score: {row['Average Score']:.4f}")
    print(f"   • Win Rate: {row['Percentage']:.1f}% ({int(row['Wins'])} wins)")
    print(f"   • Coverage: {row['Coverage %']:.1f}%")
    print(f"   • Overall Score: {row['Overall Score']:.4f}")

print("\n" + "="*80)
print("COMPLETE METRICS SUMMARY TABLE")
print("="*80)
display(summary.style.background_gradient(cmap='RdYlGn', subset=['Overall Score', 'F1-Score', 'Average Score']).format({
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

# Create radar chart for final comparison
from math import pi

fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(projection='polar'))

metrics_to_plot = ['F1-Score', 'Precision', 'Recall', 'Average Score', 'Coverage %']
categories = metrics_to_plot
N = len(categories)

# Calculate angles for each metric
angles = [n / float(N) * 2 * pi for n in range(N)]
angles += angles[:1]

# Normalize values for radar chart
max_f1 = summary['F1-Score'].max()
max_precision = summary['Precision'].max()
max_recall = summary['Recall'].max()
max_avg = summary['Average Score'].max()
max_coverage = summary['Coverage %'].max() / 100

# Plot each algorithm
for idx, row in summary.iterrows():
    values = [
        row['F1-Score'] / max_f1 if max_f1 > 0 else 0,
        row['Precision'] / max_precision if max_precision > 0 else 0,
        row['Recall'] / max_recall if max_recall > 0 else 0,
        row['Average Score'] / max_avg if max_avg > 0 else 0,
        (row['Coverage %'] / 100) / max_coverage if max_coverage > 0 else 0
    ]
    values += values[:1]
    ax.plot(angles, values, 'o-', linewidth=2, label=row['Algorithm'])
    ax.fill(angles, values, alpha=0.1)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=11)
ax.set_ylim(0, 1)
ax.set_title('📊 Algorithm Performance Radar Chart\n(Relative Comparison - Higher is Better)',
             fontsize=16, fontweight='bold', pad=30)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
ax.grid(True)
plt.tight_layout()
plt.show()

# ============================================================
# CELL 11: Print all scores for your analysis
# ============================================================
print("\n" + "="*80)
print("ALL SCORES FOR YOUR ANALYSIS")
print("="*80)

print("\n📊 PER-QUERY SCORES:")
print("-"*80)
for idx, row in df_queries.iterrows():
    print(f"\nQuery: {row['query']}")
    for label in METHODS.keys():
        print(f"  {label}: {row[label]:.4f}")
    print(f"  Winner: {winners[idx] if idx < len(winners) else 'N/A'}")

print("\n" + "="*80)
print("✅ Analysis Complete!")
print("="*80)
