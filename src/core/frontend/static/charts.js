const Charts = (function () {

  const _charts = {}
  const COLORS = {
    semantic: { bg: 'rgba(56, 189, 248, 0.6)', border: 'rgb(56, 189, 248)' },
    keyword: { bg: 'rgba(251, 191, 36, 0.6)', border: 'rgb(251, 191, 36)' },
    hybrid: { bg: 'rgba(34, 197, 94, 0.7)', border: 'rgb(34, 197, 94)' },
    rrf: { bg: 'rgba(168, 85, 247, 0.6)', border: 'rgb(168, 85, 247)' },
    ltr: { bg: 'rgba(239, 68, 68, 0.6)', border: 'rgb(239, 68, 68)' },
    fusion: { bg: 'rgba(14, 165, 233, 0.6)', border: 'rgb(14, 165, 233)' },
  }

  function _ctx(id) {
    const el = document.getElementById(id)
    return el ? el.getContext('2d') : null
  }

  function _destroy(id) {
    if (_charts[id]) { _charts[id].destroy(); delete _charts[id] }
  }

  // --------------------------------------------------------------- //
  //  PERCENTAGE LABEL PLUGIN — draws pct on bars / doughnut center   //
  //  Skips radar / line / scatter — those use native ticks + tooltip //
  // --------------------------------------------------------------- //
  const _pctPlugin = {
    id: 'pctLabels',
    afterDatasetsDraw(chart) {
      const type = chart.config.type
      if (type === 'radar' || type === 'line' || type === 'scatter') return

      const { ctx, data, chartArea } = chart
      if (!chartArea) return
      ctx.save()
      const meta = chart.getDatasetMeta(0)
      if (!meta || !meta.data) { ctx.restore(); return }

      if (type === 'doughnut') {
        const total = data.datasets[0].data.reduce((a, b) => a + b, 0)
        if (!total) { ctx.restore(); return }
        const first = meta.data[0]
        const cx = first.x, cy = first.y
        const seg = data.datasets[0].data
        const maxVal = Math.max(...seg)
        const maxIdx = seg.indexOf(maxVal)
        const maxPct = ((maxVal / total) * 100).toFixed(1)
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.font = 'bold 18px sans-serif'
        ctx.fillStyle = '#0f172a'
        ctx.fillText(maxPct + '%', cx, cy - 8)
        ctx.font = 'bold 9px sans-serif'
        ctx.fillStyle = ['#38bdf8', '#fbbf24', '#22c55e', '#a855f7'][maxIdx] || '#64748b'
        ctx.fillText(data.labels[maxIdx] || 'Method', cx, cy + 10)
        ctx.restore()
        return
      }

      if (type === 'bar') {
        const stacked = chart.options.scales?.y?.stacked || chart.options.scales?.x?.stacked
        const isHoriz = chart.options.indexAxis === 'y'

        data.datasets.forEach((ds, di) => {
          const m = chart.getDatasetMeta(di)
          if (!m || !m.data) return
          ds.data.forEach((val, vi) => {
            const bar = m.data[vi]
            if (val === undefined || val === null || val === 0) return
            const isFloat = val < 1
            let display
            if (stacked && di === data.datasets.length - 1) {
              let total = 0
              for (let j = 0; j <= di; j++) total += data.datasets[j].data[vi] || 0
              if (!total) return
              const pct = ((data.datasets[di].data[vi] || 0) / total * 100).toFixed(1)
              display = `${pct}%`
            } else if (isFloat && val < 1) {
              display = (val * 100).toFixed(1) + '%'
            } else if (isFloat) {
              display = val.toFixed(0) + 'ms'
            } else {
              display = Number.isInteger(val) ? val : val.toFixed(2)
            }
            ctx.fillStyle = '#0f172a'
            ctx.font = 'bold 10px sans-serif'
            ctx.textAlign = 'center'
            ctx.textBaseline = 'bottom'
            if (isHoriz) {
              ctx.textAlign = 'left'
              ctx.fillText(display, bar.x + 4, bar.y + 4)
            } else {
              ctx.fillText(display, bar.x, bar.y - 4)
            }
          })
        })
        ctx.restore()
        return
      }
      ctx.restore()
    }
  }

  function _makeConfig(type, data, opts) {
    const plugins = opts?.plugins || {}
    return {
      type,
      data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { boxWidth: 10, font: { size: 9 } } }, ...plugins },
        ...opts,
      },
      plugins: [_pctPlugin],
    }
  }

  function _create(id, type, data, opts) {
    _destroy(id)
    const ctx = _ctx(id)
    if (!ctx) return null
    _charts[id] = new Chart(ctx, _makeConfig(type, data, opts))
    return _charts[id]
  }

  // --------------------------------------------------------------- //
  //  RADAR — doc score profile                                       //
  // --------------------------------------------------------------- //
  function radar(id) {
    const init = [0.01, 0.01, 0.01, 0.01, 0.01]
    return _create(id, 'radar', {
      labels: ['Semantic', 'Keyword', 'Date', 'Language', 'Popularity'],
      datasets: [{
        label: 'Score Profile',
        data: init,
        fill: true,
        backgroundColor: 'rgba(56, 189, 248, 0.12)',
        borderColor: 'rgb(56, 189, 248)',
        pointBackgroundColor: 'rgb(56, 189, 248)',
        pointBorderColor: '#fff',
        pointRadius: 4,
        pointHoverRadius: 7,
      }],
    }, {
      elements: { line: { tension: 0.3, borderWidth: 2 } },
      scales: {
        r: {
          beginAtZero: true, max: 1,
          ticks: {
            display: true,
            font: { size: 8, weight: 'bold' },
            color: '#64748b',
            backdropColor: 'transparent',
            callback: v => (v * 100).toFixed(0) + '%'
          },
          grid: { color: '#e2e8f0' },
          angleLines: { color: '#e2e8f0' },
          pointLabels: {
            font: { size: 11, weight: 'bold' },
            color: '#1e293b',
          }
        }
      },
      plugins: { legend: { display: false } },
      layout: { padding: { top: 20, bottom: 20 } },
    })
  }

  function updateRadar(sem, key, dateRel, lang, pop) {
    const c = _charts['scoreRadarChart']
    if (!c) return
    c.data.datasets[0].data = [
      Math.min(1, Math.max(0, sem)),
      Math.min(1, Math.max(0, key)),
      Math.min(1, Math.max(0, dateRel)),
      Math.min(1, Math.max(0, lang)),
      Math.min(1, Math.max(0, pop)),
    ]
    c.update('none')
  }

  // --------------------------------------------------------------- //
  //  HORIZONTAL BAR — NDCG method comparison                         //
  // --------------------------------------------------------------- //
  function comparisonChart(id) {
    return _create(id, 'bar', {
      labels: ['Semantic', 'Keyword', 'Hybrid'],
      datasets: [{
        label: 'NDCG@10',
        data: [0, 0, 0],
        backgroundColor: [COLORS.semantic.bg, COLORS.keyword.bg, COLORS.hybrid.bg],
        borderColor: [COLORS.semantic.border, COLORS.keyword.border, COLORS.hybrid.border],
        borderWidth: 1,
        borderRadius: 4,
      }],
    }, {
      indexAxis: 'y',
      scales: {
        x: {
          beginAtZero: true, max: 1,
          title: { display: true, text: 'NDCG@10', font: { size: 9 } },
          ticks: { callback: v => (v * 100).toFixed(0) + '%' }
        },
        y: { ticks: { font: { size: 10, weight: 'bold' } } }
      },
      plugins: { legend: { display: false } },
    })
  }

  function updateComparisonChart(sem, key, hybrid) {
    const c = _charts['strategyComparisonChart']
    if (!c) return
    c.data.datasets[0].data = [sem, key, hybrid]
    c.update()
  }

  // --------------------------------------------------------------- //
  //  GROUPED BAR — all 5 methods comparison                          //
  // --------------------------------------------------------------- //
  function methodChart(id) {
    return _create(id, 'bar', {
      labels: ['NDCG@10', 'Precision@5', 'MRR'],
      datasets: [
        { label: 'Semantic', data: [0, 0, 0], backgroundColor: COLORS.semantic.bg, borderColor: COLORS.semantic.border, borderWidth: 1, borderRadius: 3 },
        { label: 'Keyword', data: [0, 0, 0], backgroundColor: COLORS.keyword.bg, borderColor: COLORS.keyword.border, borderWidth: 1, borderRadius: 3 },
        { label: 'Hybrid', data: [0, 0, 0], backgroundColor: COLORS.hybrid.bg, borderColor: COLORS.hybrid.border, borderWidth: 1, borderRadius: 3 },
        { label: 'RRF', data: [0, 0, 0], backgroundColor: COLORS.rrf.bg, borderColor: COLORS.rrf.border, borderWidth: 1, borderRadius: 3 },
      ],
    }, {
      scales: {
        y: {
          beginAtZero: true, max: 1,
          ticks: { callback: v => (v * 100).toFixed(0) + '%', font: { size: 8 } },
          title: { display: true, text: 'Score', font: { size: 8 } }
        },
        x: { ticks: { font: { size: 9, weight: 'bold' } } }
      },
      plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 9 }, padding: 8 } } },
      layout: { padding: { bottom: 10 } },
    })
  }

  function updateMethodChart(data) {
    const c = _charts['methodChart']
    if (!c) return
    const metrics = ['ndcg', 'precision', 'mrr']
    metrics.forEach((m, i) => {
      c.data.datasets.forEach((ds, j) => {
        ds.data[i] = (data[j] && data[j][m]) || 0
      })
    })
    c.update()
  }

  // --------------------------------------------------------------- //
  //  PR CURVE — line chart                                          //
  // --------------------------------------------------------------- //
  function prCurve(id) {
    return _create(id, 'line', {
      datasets: [{
        label: 'PR Curve',
        data: [],
        borderColor: 'rgb(13, 202, 240)',
        backgroundColor: 'rgba(13, 202, 240, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
      }],
    }, {
      scales: {
        x: {
          min: 0, max: 1,
          title: { display: true, text: 'Recall', font: { size: 9 } },
          ticks: { callback: v => (v * 100).toFixed(0) + '%' }
        },
        y: {
          min: 0, max: 1,
          title: { display: true, text: 'Precision', font: { size: 9 } },
          ticks: { callback: v => (v * 100).toFixed(0) + '%' }
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => `P: ${(ctx.parsed.y * 100).toFixed(1)}%  R: ${(ctx.parsed.x * 100).toFixed(1)}%`
          }
        }
      },
    })
  }

  function updatePRCurve(points) {
    const c = _charts['prCurveChart']
    if (!c) return
    c.data.datasets[0].data = points || []
    c.update('none')
  }

  // --------------------------------------------------------------- //
  //  SCATTER — semantic vs bm25 score correlation                   //
  // --------------------------------------------------------------- //
  function scatter(id) {
    return _create(id, 'scatter', {
      datasets: [{
        label: 'Doc Scores',
        data: [],
        backgroundColor: 'rgba(56, 189, 248, 0.5)',
        borderColor: 'rgb(56, 189, 248)',
        pointRadius: 5,
        pointHoverRadius: 8,
      }],
    }, {
      scales: {
        x: {
          title: { display: true, text: 'Semantic Score', font: { size: 9 } },
          beginAtZero: true, max: 1,
          ticks: { callback: v => (v * 100).toFixed(0) + '%' }
        },
        y: {
          title: { display: true, text: 'BM25 Score', font: { size: 9 } },
          beginAtZero: true, max: 1,
          ticks: { callback: v => (v * 100).toFixed(0) + '%' }
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function (ctx) {
              return `Doc #${ctx.raw.label || ''}  Sem: ${(ctx.parsed.x * 100).toFixed(1)}%  BM25: ${(ctx.parsed.y * 100).toFixed(1)}%`
            },
          },
        },
      },
    })
  }

  function updateScatter(points) {
    const c = _charts['scatterChart']
    if (!c) return
    c.data.datasets[0].data = points || []
    c.update('none')
  }

  // --------------------------------------------------------------- //
  //  STACKED BAR — latency breakdown                                 //
  // --------------------------------------------------------------- //
  function latencyChart(id) {
    return _create(id, 'bar', {
      labels: ['Latency (ms)'],
      datasets: [
        { label: 'Semantic', data: [0], backgroundColor: COLORS.semantic.bg, borderColor: COLORS.semantic.border, borderWidth: 1 },
        { label: 'Keyword', data: [0], backgroundColor: COLORS.keyword.bg, borderColor: COLORS.keyword.border, borderWidth: 1 },
        { label: 'Fusion', data: [0], backgroundColor: COLORS.fusion.bg, borderColor: COLORS.fusion.border, borderWidth: 1 },
      ],
    }, {
      scales: {
        x: { stacked: true, ticks: { font: { size: 10, weight: 'bold' } } },
        y: { stacked: true, title: { display: true, text: 'ms', font: { size: 9 } } },
      },
      plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 9 }, padding: 8 } } },
      layout: { padding: { bottom: 10 } },
    })
  }

  function updateLatencyChart(sem, key, fusion) {
    const c = _charts['latencyChart']
    if (!c) return
    c.data.datasets[0].data = [sem || 0]
    c.data.datasets[1].data = [key || 0]
    c.data.datasets[2].data = [fusion || 0]
    c.update()
  }

  // --------------------------------------------------------------- //
  //  HISTOGRAM — score distribution                                  //
  // --------------------------------------------------------------- //
  function histogram(id) {
    return _create(id, 'bar', {
      labels: ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'],
      datasets: [{
        label: 'Documents',
        data: [0, 0, 0, 0, 0],
        backgroundColor: 'rgba(56, 189, 248, 0.5)',
        borderColor: 'rgb(56, 189, 248)',
        borderWidth: 1,
        borderRadius: 4,
      }],
    }, {
      scales: {
        y: {
          beginAtZero: true,
          ticks: { precision: 0, font: { size: 8 } },
          title: { display: true, text: 'Count', font: { size: 9 } }
        },
        x: {
          title: { display: true, text: 'Score Range', font: { size: 9 } },
          ticks: { font: { size: 9 } }
        },
      },
      plugins: { legend: { display: false } },
    })
  }

  function updateHistogram(scores) {
    const c = _charts['histogramChart']
    if (!c || !scores) return
    const bins = [0, 0, 0, 0, 0]
    scores.forEach(s => {
      const idx = Math.min(4, Math.floor(s / 0.2))
      bins[idx]++
    })
    c.data.datasets[0].data = bins
    c.update('none')
  }

  // --------------------------------------------------------------- //
  //  DOUGHNUT — winner distribution                                  //
  // --------------------------------------------------------------- //
  function doughnut(id) {
    return _create(id, 'doughnut', {
      labels: ['Semantic', 'Keyword', 'Hybrid', 'RRF'],
      datasets: [{
        data: [0, 0, 0, 0],
        backgroundColor: [COLORS.semantic.bg, COLORS.keyword.bg, COLORS.hybrid.bg, COLORS.rrf.bg],
        borderColor: [COLORS.semantic.border, COLORS.keyword.border, COLORS.hybrid.border, COLORS.rrf.border],
        borderWidth: 2,
        hoverOffset: 8,
      }],
    }, {
      cutout: '55%',
      layout: { padding: { bottom: 10 } },
      plugins: {
        legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 9 }, padding: 8 } },
        tooltip: {
          callbacks: {
            label: ctx => {
              const total = ctx.dataset.data.reduce((a, b) => a + b, 0)
              const pct = total ? ((ctx.parsed / total) * 100).toFixed(1) : 0
              return `${ctx.label}: ${ctx.parsed} pts (${pct}%)`
            }
          }
        },
      },
    })
  }

  function updateDoughnut(values) {
    const c = _charts['doughnutChart']
    if (!c) return
    c.data.datasets[0].data = values || [0, 0, 0, 0]
    c.update()
  }

  // --------------------------------------------------------------- //
  //  ELBOW CURVE — NDCG@K line chart for K=1..10                    //
  // --------------------------------------------------------------- //
  function elbowChart(id) {
    return _create(id, 'line', {
      labels: ['@1', '@2', '@3', '@4', '@5', '@6', '@7', '@8', '@9', '@10'],
      datasets: [
        { label: 'Semantic', data: [], borderColor: COLORS.semantic.border, backgroundColor: 'transparent', borderWidth: 2, pointRadius: 3, tension: 0.3 },
        { label: 'Keyword', data: [], borderColor: COLORS.keyword.border, backgroundColor: 'transparent', borderWidth: 2, pointRadius: 3, tension: 0.3, borderDash: [4, 2] },
        { label: 'Hybrid', data: [], borderColor: COLORS.hybrid.border, backgroundColor: 'transparent', borderWidth: 2.5, pointRadius: 4, tension: 0.3 },
        { label: 'RRF', data: [], borderColor: COLORS.rrf.border, backgroundColor: 'transparent', borderWidth: 2, pointRadius: 3, tension: 0.3, borderDash: [2, 2] },
      ],
    }, {
      scales: {
        x: { title: { display: true, text: 'K', font: { size: 9 } }, ticks: { font: { size: 8 } } },
        y: {
          beginAtZero: true, max: 1,
          title: { display: true, text: 'NDCG', font: { size: 9 } },
          ticks: { callback: v => (v * 100).toFixed(0) + '%', font: { size: 8 } }
        },
      },
      plugins: {
        legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 8 }, padding: 6 } },
        tooltip: {
          callbacks: {
            label: ctx => `${ctx.dataset.label}: ${(ctx.parsed.y * 100).toFixed(1)}%`
          }
        }
      },
      layout: { padding: { bottom: 6 } },
    })
  }

  function updateElbowChart(series) {
    const c = _charts['elbowChart']
    if (!c || !series) return
    const labels = ['Semantic', 'Keyword', 'Hybrid', 'RRF']
    labels.forEach((name, i) => {
      c.data.datasets[i].data = (series[i] && series[i].length >= 10) ? series[i].slice(0, 10) : []
    })
    c.update('none')
  }

  // --------------------------------------------------------------- //
  //  BULK INIT — call once on DOMContentLoaded                       //
  // --------------------------------------------------------------- //
  function initAll() {
    radar('scoreRadarChart')
    comparisonChart('strategyComparisonChart')
    prCurve('prCurveChart')
    scatter('scatterChart')
    latencyChart('latencyChart')
    histogram('histogramChart')
    methodChart('methodChart')
    doughnut('doughnutChart')
    elbowChart('elbowChart')
  }

  function resizeAll() {
    Object.values(_charts).forEach(c => { c.resize(); c.update('none') })
  }

  // --------------------------------------------------------------- //
  //  PUBLIC API                                                      //
  // --------------------------------------------------------------- //
  return {
    initAll,
    resizeAll,
    updateRadar,
    updateComparisonChart,
    updatePRCurve,
    updateScatter,
    updateLatencyChart,
    updateHistogram,
    updateMethodChart,
    updateDoughnut,
    updateElbowChart,
    get: id => _charts[id],
  }

})()
