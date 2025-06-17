'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { LoadingState } from '../components/LoadingState';
import { ModelSelector } from '../components/ModelSelector';
import { PriceComparisonTable } from '../components/PriceComparisonTable';
import { clearCache, fetchPrices, PricesResponse } from '../lib/api';

const SERIES = ['iPhone 16', 'iPhone 16 Pro', 'iPhone 16 Plus', 'iPhone 16 Pro Max', 'iPhone 16 e'];
const STORAGE_KEY = 'selected_iphone_models';

export default function Home() {
  const [selectedSeries, setSelectedSeries] = useState<string[]>([]);
  const [data, setData] = useState<Record<string, PricesResponse>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

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
      </div>
    </ErrorBoundary>
  );
}
