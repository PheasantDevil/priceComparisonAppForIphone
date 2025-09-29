'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { LoadingState } from '../components/LoadingState';
import { ModelSelector } from '../components/ModelSelector';
import { PriceComparisonTable } from '../components/PriceComparisonTable';
import PriceHistoryChart from '../components/PriceHistoryChart';
import { clearCache, fetchPrices, PricesResponse } from '../lib/api';

const SERIES = [
  'iPhone 17',
  'iPhone 17 Air',
  'iPhone 17 Pro',
  'iPhone 17 Pro Max',
];
const STORAGE_KEY = 'selected_iphone_models';
const RAKUTEN_COLUMNS_STORAGE_KEY = 'show_rakuten_columns';

export default function Home() {
  const [selectedSeries, setSelectedSeries] = useState<string[]>([]);
  const [data, setData] = useState<Record<string, PricesResponse>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [showPriceHistory, setShowPriceHistory] = useState(false);
  const [selectedHistorySeries, setSelectedHistorySeries] =
    useState('iPhone 17 Pro');
  const [selectedHistoryCapacity, setSelectedHistoryCapacity] = useState('1TB');
  const [showRakutenColumns, setShowRakutenColumns] = useState(false);
  const [tickInterval, setTickInterval] = useState(10000); // Y軸の目盛り間隔

  // GitHub Pages 404 redirect handling
  useEffect(() => {
    // Check if we're on GitHub Pages and need to redirect
    if (typeof window !== 'undefined') {
      const { pathname } = window.location;
      if (pathname.includes('/?/')) {
        const newPath = pathname.replace('/?/', '/').replace(/~and~/g, '&');
        window.history.replaceState(null, '', newPath);
      }
    }
  }, []);

  // ローカルストレージから選択状態を読み込む
  useEffect(() => {
    try {
      const savedSeries = localStorage.getItem(STORAGE_KEY);
      if (savedSeries) {
        const parsed = JSON.parse(savedSeries);
        if (Array.isArray(parsed) && parsed.every(s => SERIES.includes(s))) {
          setSelectedSeries(parsed);
        }
      }

      // 楽天錬金列の表示状態を読み込む
      const savedRakutenColumns = localStorage.getItem(
        RAKUTEN_COLUMNS_STORAGE_KEY
      );
      if (savedRakutenColumns) {
        setShowRakutenColumns(JSON.parse(savedRakutenColumns));
      }
    } catch (error) {
      console.error('Failed to load saved settings:', error);
      alert('設定の読み込みに失敗しました。デフォルト設定を使用します。');
    }
  }, []);

  // 選択状態をローカルストレージに保存
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(selectedSeries));
    } catch (error) {
      console.error('Failed to save series:', error);
      alert('選択状態の保存に失敗しました。');
    }
  }, [selectedSeries]);

  // 楽天錬金列の表示状態をローカルストレージに保存
  useEffect(() => {
    try {
      localStorage.setItem(
        RAKUTEN_COLUMNS_STORAGE_KEY,
        JSON.stringify(showRakutenColumns)
      );
    } catch (error) {
      console.error('Failed to save rakuten columns setting:', error);
      alert('楽天錬金列の設定保存に失敗しました。');
    }
  }, [showRakutenColumns]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const newData: Record<string, PricesResponse> = {};
      // 並列でデータを取得
      const promises = selectedSeries.map(series => fetchPrices(series));
      const results = await Promise.all(promises);

      selectedSeries.forEach((series, index) => {
        newData[series] = results[index];
      });

      setData(newData);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      setError(
        error instanceof Error ? error : new Error('データの取得に失敗しました')
      );
      alert('データの取得に失敗しました。');
    } finally {
      setLoading(false);
    }
  }, [selectedSeries]);

  useEffect(() => {
    if (selectedSeries.length > 0) {
      fetchData();
    }
  }, [selectedSeries, fetchData]);

  const handleRefresh = useCallback(async () => {
    clearCache();
    await fetchData();
    alert('データを更新しました。');
  }, [fetchData]);

  const handleSeriesToggle = useCallback((series: string) => {
    setSelectedSeries(prev =>
      prev.includes(series) ? prev.filter(s => s !== series) : [...prev, series]
    );
  }, []);

  // メモ化されたコンポーネントのレンダリング
  const modelSelector = useMemo(
    () => (
      <ModelSelector
        series={SERIES}
        selectedSeries={selectedSeries}
        onSeriesToggle={handleSeriesToggle}
        onRefresh={handleRefresh}
        loading={loading}
      />
    ),
    [selectedSeries, handleSeriesToggle, handleRefresh, loading]
  );

  const priceTable = useMemo(
    () => (
      <PriceComparisonTable
        data={data}
        selectedSeries={selectedSeries}
        loading={loading}
        showRakutenColumns={showRakutenColumns}
      />
    ),
    [data, selectedSeries, loading, showRakutenColumns]
  );

  const priceHistorySection = useMemo(
    () => (
      <div className='mt-8 bg-white dark:bg-gray-800 p-6 rounded-lg shadow border border-gray-200 dark:border-gray-700'>
        <div className='flex items-center justify-between mb-6'>
          <h2 className='text-xl font-bold'>価格推移グラフ</h2>
          <button
            onClick={() => setShowPriceHistory(!showPriceHistory)}
            className='px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500'
          >
            {showPriceHistory ? 'グラフを隠す' : 'グラフを表示'}
          </button>
        </div>

        {showPriceHistory && (
          <div className='space-y-6'>
            {/* グラフ設定 */}
            <div className='grid grid-cols-1 md:grid-cols-4 gap-4'>
              <div>
                <label className='block text-sm font-medium text-gray-700 mb-2'>
                  シリーズ
                </label>
                <select
                  value={selectedHistorySeries}
                  onChange={e => setSelectedHistorySeries(e.target.value)}
                  className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
                >
                  {SERIES.map(series => (
                    <option key={series} value={series}>
                      {series}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className='block text-sm font-medium text-gray-700 mb-2'>
                  容量
                </label>
                <select
                  value={selectedHistoryCapacity}
                  onChange={e => setSelectedHistoryCapacity(e.target.value)}
                  className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
                >
                  <option value='128GB'>128GB</option>
                  <option value='256GB'>256GB</option>
                  <option value='512GB'>512GB</option>
                  <option value='1TB'>1TB</option>
                </select>
              </div>

              <div>
                <label className='block text-sm font-medium text-gray-700 mb-2'>
                  Y軸目盛り間隔
                </label>
                <select
                  value={tickInterval}
                  onChange={e => setTickInterval(Number(e.target.value))}
                  className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
                >
                  <option value={5000}>¥5,000</option>
                  <option value={10000}>¥10,000</option>
                  <option value={15000}>¥15,000</option>
                  <option value={20000}>¥20,000</option>
                  <option value={30000}>¥30,000</option>
                  <option value={50000}>¥50,000</option>
                  <option value={60000}>¥60,000</option>
                </select>
              </div>

              <div className='flex items-end'>
                <div className='text-sm text-gray-600'>
                  過去14日間の価格推移を表示
                </div>
              </div>
            </div>

            {/* グラフ表示 */}
            <div className='bg-gray-50 dark:bg-gray-700 rounded-lg p-4'>
              <PriceHistoryChart
                series={selectedHistorySeries}
                capacity={selectedHistoryCapacity}
                days={14}
                height={400}
                className='w-full'
                tickInterval={tickInterval}
              />
            </div>

            {/* 説明 */}
            <div className='bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4'>
              <h3 className='text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2'>
                グラフの見方
              </h3>
              <ul className='text-sm text-blue-800 dark:text-blue-200 space-y-1'>
                <li>
                  • <strong>平均価格（緑）</strong>: その日の平均買取価格
                </li>
                <li>
                  • <strong>最高価格（オレンジ）</strong>: その日の最高買取価格
                </li>
                <li>
                  • <strong>最低価格（赤）</strong>: その日の最低買取価格
                </li>
                <li>• データは毎日午前9時に自動更新されます</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    ),
    [
      showPriceHistory,
      selectedHistorySeries,
      selectedHistoryCapacity,
      tickInterval,
    ]
  );

  return (
    <ErrorBoundary>
      <div className='max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8'>
        <div className='bg-white dark:bg-gray-800 p-6 rounded-lg shadow border border-gray-200 dark:border-gray-700'>
          <h1 className='text-2xl font-bold text-center mb-6'>
            iPhone 価格比較
          </h1>

          <div className='space-y-4 mb-6'>{modelSelector}</div>

          {/* 楽天錬金列の表示/非表示切り替え */}
          <div className='mb-6'>
            <label className='inline-flex items-center space-x-2 cursor-pointer'>
              <input
                type='checkbox'
                checked={showRakutenColumns}
                onChange={() => setShowRakutenColumns(!showRakutenColumns)}
                className='h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
                aria-label='楽天錬金列を表示'
              />
              <span className='text-sm font-medium text-gray-700'>
                楽天錬金列を表示（楽天錬金時差額・楽天錬金差額率）
              </span>
            </label>
          </div>

          {loading ? (
            <LoadingState />
          ) : error ? (
            <div className='p-4 rounded-md bg-red-50 border border-red-200 text-center'>
              <h2 className='text-lg font-semibold text-red-600 mb-2'>
                エラーが発生しました
              </h2>
              <p className='text-red-500'>{error.message}</p>
            </div>
          ) : (
            priceTable
          )}
        </div>

        {/* 価格推移グラフセクション */}
        {priceHistorySection}
      </div>
    </ErrorBoundary>
  );
}
