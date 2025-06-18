/**
 * 価格推移グラフ表示コンポーネント
 * Chart.jsを使用して価格履歴をグラフ表示
 */

class PriceChart {
  constructor(containerId, options = {}) {
    this.containerId = containerId;
    this.container = document.getElementById(containerId);
    this.chart = null;
    this.options = {
      days: options.days || 14,
      height: options.height || 300,
      ...options,
    };

    this.init();
  }

  init() {
    if (!this.container) {
      console.error(`Container with id '${this.containerId}' not found`);
      return;
    }

    // グラフ用のcanvas要素を作成
    this.container.innerHTML = `
            <div class="price-chart-container">
                <div class="chart-header">
                    <h3>価格推移（過去${this.options.days}日間）</h3>
                    <div class="chart-controls">
                        <select id="chart-capacity-select" class="form-select form-select-sm">
                            <option value="128GB">128GB</option>
                            <option value="256GB">256GB</option>
                            <option value="512GB">512GB</option>
                            <option value="1TB">1TB</option>
                        </select>
                    </div>
                </div>
                <div class="chart-wrapper">
                    <canvas id="price-chart-canvas"></canvas>
                </div>
                <div class="chart-legend">
                    <div class="legend-item">
                        <span class="legend-color" style="background-color: #4CAF50;"></span>
                        <span>平均価格</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-color" style="background-color: #FF9800;"></span>
                        <span>最高価格</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-color" style="background-color: #F44336;"></span>
                        <span>最低価格</span>
                    </div>
                </div>
            </div>
        `;

    // Chart.jsの読み込み確認
    if (typeof Chart === 'undefined') {
      this.loadChartJS();
    } else {
      this.setupChart();
    }
  }

  loadChartJS() {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
    script.onload = () => this.setupChart();
    document.head.appendChild(script);
  }

  setupChart() {
    const canvas = document.getElementById('price-chart-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // 初期データ（空）
    this.chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: '平均価格',
            data: [],
            borderColor: '#4CAF50',
            backgroundColor: 'rgba(76, 175, 80, 0.1)',
            borderWidth: 2,
            fill: false,
            tension: 0.1,
          },
          {
            label: '最高価格',
            data: [],
            borderColor: '#FF9800',
            backgroundColor: 'rgba(255, 152, 0, 0.1)',
            borderWidth: 2,
            fill: false,
            tension: 0.1,
          },
          {
            label: '最低価格',
            data: [],
            borderColor: '#F44336',
            backgroundColor: 'rgba(244, 67, 54, 0.1)',
            borderWidth: 2,
            fill: false,
            tension: 0.1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              label: function (context) {
                return (
                  context.dataset.label +
                  ': ¥' +
                  context.parsed.y.toLocaleString()
                );
              },
            },
          },
        },
        scales: {
          x: {
            display: true,
            title: {
              display: true,
              text: '日付',
            },
          },
          y: {
            display: true,
            title: {
              display: true,
              text: '価格 (円)',
            },
            ticks: {
              callback: function (value) {
                return '¥' + value.toLocaleString();
              },
            },
          },
        },
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false,
        },
      },
    });

    // 容量選択のイベントリスナー
    const capacitySelect = document.getElementById('chart-capacity-select');
    if (capacitySelect) {
      capacitySelect.addEventListener('change', e => {
        this.loadPriceHistory(e.target.value);
      });
    }
  }

  async loadPriceHistory(capacity) {
    try {
      // 現在選択されているシリーズを取得
      const currentSeries = this.getCurrentSeries();
      if (!currentSeries) {
        console.warn('No series selected');
        return;
      }

      // APIから価格履歴を取得
      const response = await fetch(
        `${this.getApiBaseUrl()}/get_price_history?series=${encodeURIComponent(
          currentSeries
        )}&capacity=${encodeURIComponent(capacity)}&days=${this.options.days}`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      this.updateChart(data.history);
    } catch (error) {
      console.error('Error loading price history:', error);
      this.showError('価格履歴の取得に失敗しました');
    }
  }

  updateChart(historyData) {
    if (!this.chart || !historyData || historyData.length === 0) {
      this.showNoData();
      return;
    }

    // データを日付順にソート
    const sortedData = historyData.sort(
      (a, b) => new Date(a.date) - new Date(b.date)
    );

    // チャートデータを更新
    this.chart.data.labels = sortedData.map(item => {
      const date = new Date(item.date);
      return date.toLocaleDateString('ja-JP', {
        month: 'short',
        day: 'numeric',
      });
    });

    this.chart.data.datasets[0].data = sortedData.map(item => item.price_avg);
    this.chart.data.datasets[1].data = sortedData.map(item => item.price_max);
    this.chart.data.datasets[2].data = sortedData.map(item => item.price_min);

    this.chart.update();

    // エラーメッセージをクリア
    this.clearMessages();
  }

  getCurrentSeries() {
    // 現在選択されているシリーズを取得するロジック
    // 実際の実装では、ページの状態から取得
    const seriesSelect = document.getElementById('series-select');
    return seriesSelect ? seriesSelect.value : 'iPhone 16';
  }

  getApiBaseUrl() {
    // APIのベースURLを取得
    // 開発環境と本番環境で切り替え
    return window.location.hostname === 'localhost'
      ? 'http://localhost:8080'
      : 'https://your-cloud-function-url.com';
  }

  showError(message) {
    this.clearMessages();
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger';
    errorDiv.textContent = message;
    this.container.appendChild(errorDiv);
  }

  showNoData() {
    this.clearMessages();
    const noDataDiv = document.createElement('div');
    noDataDiv.className = 'alert alert-info';
    noDataDiv.textContent = '価格履歴データがありません';
    this.container.appendChild(noDataDiv);
  }

  clearMessages() {
    const alerts = this.container.querySelectorAll('.alert');
    alerts.forEach(alert => alert.remove());
  }

  // 外部から呼び出せるメソッド
  refresh(series, capacity) {
    if (capacity) {
      const capacitySelect = document.getElementById('chart-capacity-select');
      if (capacitySelect) {
        capacitySelect.value = capacity;
      }
    }
    this.loadPriceHistory(capacity || this.getSelectedCapacity());
  }

  getSelectedCapacity() {
    const capacitySelect = document.getElementById('chart-capacity-select');
    return capacitySelect ? capacitySelect.value : '128GB';
  }
}

// グローバル関数として公開
window.PriceChart = PriceChart;
