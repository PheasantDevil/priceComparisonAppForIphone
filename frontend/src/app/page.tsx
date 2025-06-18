'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { LoadingState } from '../components/LoadingState';
import { ModelSelector } from '../components/ModelSelector';
import { PriceComparisonTable } from '../components/PriceComparisonTable';
import PriceHistoryChart from '../components/PriceHistoryChart';
import { clearCache, fetchPrices, PricesResponse } from '../lib/api';

const SERIES = [
  'iPhone 16',
  'iPhone 16 Pro',
  'iPhone 16 Plus',
  'iPhone 16 Pro Max',
  'iPhone 16 e',
];
const STORAGE_KEY = 'selected_iphone_models';

export default function Home() {
  const [selectedSeries, setSelectedSeries] = useState<string[]>([]);
  const [data, setData] = useState<Record<string, PricesResponse>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [showPriceHistory, setShowPriceHistory] = useState(false);
  const [selectedHistorySeries, setSelectedHistorySeries] =
    useState('iPhone 16 Pro');
  const [selectedHistoryCapacity, setSelectedHistoryCapacity] = useState('1TB');

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
    } catch (error) {
      console.error('Failed to load saved series:', error);
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
      />
    ),
    [data, selectedSeries, loading]
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
            <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
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
    [showPriceHistory, selectedHistorySeries, selectedHistoryCapacity]
  );

  return (
    <ErrorBoundary>
      <div className='max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8'>
        <div className='bg-white dark:bg-gray-800 p-6 rounded-lg shadow border border-gray-200 dark:border-gray-700'>
          <h1 className='text-2xl font-bold text-center mb-6'>
            iPhone 価格比較
          </h1>

          <div className='space-y-4 mb-6'>{modelSelector}</div>

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
