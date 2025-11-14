import base64
import io

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

# === ADD THIS FUNCTION ===
# def generate_comparison_graph(cursor):
#     # === FETCH FRESH DATA ===
#     cursor.execute("""
#         SELECT search_type, AVG(latency_ms), AVG(results_count)
#         FROM search_logs
#         GROUP BY search_type
#         ORDER BY search_type ASC
#     """)
#     rows = cursor.fetchall()

#     modes = ['keyword', 'semantic', 'hybrid']
#     latency = {}
#     recall = {}

#     for mode, lat, rec in rows:
#         if mode in modes:
#             latency[mode] = float(lat) if lat else 0
#             recall[mode] = float(rec) if rec else 0

#     active_modes = [m for m in modes if m in latency]
#     if not active_modes:
#         return None

#     lat_vals = [latency[m] for m in active_modes]
#     rec_vals = [recall[m] for m in active_modes]

#     print(f"PLOTTING: {active_modes} | Latency: {lat_vals} | Recall: {rec_vals}")

#     # === FORCE NEW FIGURE ===
#     plt.clf()  # Clear current
#     plt.close('all')  # Kill old
#     fig = plt.figure(figsize=(9, 6))  # Fresh fig
#     ax1 = fig.add_subplot(111)

#     # === BARS ===
#     bars = ax1.bar(active_modes, lat_vals,
#                    color=['#ff6b6b', '#4ecdc4', '#45b7d1'][:len(active_modes)],
#                    alpha=0.8)
#     ax1.set_ylabel('Latency (ms)', color='tab:blue')
#     ax1.set_ylim(0, max(lat_vals) * 1.25)

#     for bar in bars:
#         h = bar.get_height()
#         ax1.text(bar.get_x() + bar.get_width()/2, h + max(lat_vals)*0.01,
#                  f'{h:.0f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

#     # === LINE ===
#     ax2 = ax1.twinx()
#     ax2.plot(active_modes, rec_vals, 'o-', color='orange', linewidth=4, markersize=12)
#     ax2.set_ylabel('Recall@10', color='orange')

#     for i, v in enumerate(rec_vals):
#         ax2.text(i, v + 1, f'{v:.1f}', color='orange', ha='center', fontsize=11, fontweight='bold')

#     plt.title(f"Live Search Stats — {len(rows)} Queries", fontsize=14, pad=20)

#     # === SAVE FRESH ===
#     buf = io.BytesIO()
#     plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
#     buf.seek(0)
#     img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

#     # === CLEAN UP ===
#     plt.close(fig)
#     buf.close()

#     return img_base64
def generate_query_graph(mode, latency_ms, results_count, semantic_count=0, bm25_count=0):
    modes = ['keyword', 'semantic', 'hybrid']
    latency = {'keyword': 0, 'semantic': 0, 'hybrid': 0}
    results = {'keyword': 0, 'semantic': 0, 'hybrid': 0}

    # Fill current mode
    latency[mode] = latency_ms
    results[mode] = results_count

    # If hybrid → show both
    if mode == 'hybrid':
        latency['semantic'] = latency_ms * 0.6  # estimate
        latency['bm25'] = latency_ms * 0.4
        results['semantic'] = semantic_count
        results['bm25'] = bm25_count

    active_modes = [m for m in modes if latency[m] > 0]
    lat_vals = [latency[m] for m in active_modes]
    res_vals = [results[m] for m in active_modes]

    plt.clf()
    plt.close('all')
    fig, ax1 = plt.subplots(figsize=(8, 5))

    bars = ax1.bar(active_modes, lat_vals, color='#4ecdc4', alpha=0.8)
    ax1.set_ylabel('Latency (ms)', color='tab:blue')
    ax1.set_ylim(0, max(lat_vals) * 1.3)

    for bar in bars:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, h + max(lat_vals)*0.02,
                 f'{h:.0f}ms', ha='center', va='bottom', fontsize=10)

    ax2 = ax1.twinx()
    ax2.plot(active_modes, res_vals, 'o-', color='orange', linewidth=3, markersize=10)
    ax2.set_ylabel('Results', color='orange')

    plt.title(f"Query Performance: {mode.capitalize()}")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    buf.close()

    return img_base64
