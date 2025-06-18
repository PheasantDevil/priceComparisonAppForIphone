import { memo } from 'react';
import { PricesResponse } from '../lib/api';

type PriceComparisonTableProps = {
  data: Record<string, PricesResponse>;
  selectedSeries: string[];
  loading: boolean;
};

const formatPrice = (price: number) => {
  return `${price.toLocaleString()}円`;
};

const formatPercentage = (price: number, basePrice: number) => {
  if (!basePrice) return '-';
  const percentage = (price / basePrice) * 100;
  return `${percentage.toFixed(1)}%`;
};

const getPriceDiffColor = (diff: number) => {
  if (diff > 0) return 'text-green-500';
  if (diff < 0) return 'text-red-500';
  return 'text-gray-500';
};

export const PriceComparisonTable = memo(function PriceComparisonTable({
  data,
  selectedSeries,
  loading,
}: PriceComparisonTableProps) {
  if (loading) {
    return (
      <div
        className='text-center py-8'
        role='status'
        aria-label='データを読み込み中'
      >
        <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto'></div>
        <p className='mt-4'>データを読み込み中...</p>
      </div>
    );
  }

  if (selectedSeries.length === 0) {
    return (
      <div
        className='text-center py-8 text-gray-500 bg-gray-50 rounded-md'
        role='status'
        aria-label='モデルが選択されていません'
      >
        比較するモデルを選択してください
      </div>
    );
  }

  // モデルごとにまとめて縦並び
  // 各モデル・各容量ごとに1行ずつ表示
  const rows: {
    series: string;
    capacity: string;
    official_price: number;
    kaitori_price: number;
    price_diff: number;
    rakuten_diff: number;
  }[] = [];

  selectedSeries.forEach(series => {
    const modelData = data[series];
    if (modelData && modelData.prices) {
      Object.entries(modelData.prices).forEach(([capacity, priceInfo]) => {
        rows.push({
          series,
          capacity,
          official_price: priceInfo.official_price,
          kaitori_price: priceInfo.kaitori_price,
          price_diff: priceInfo.price_diff,
          rakuten_diff: priceInfo.rakuten_diff,
        });
      });
    }
  });

  return (
    <div
      className='max-w-full overflow-x-auto'
      role='region'
      aria-label='価格比較テーブル'
    >
      <table className='min-w-full divide-y divide-gray-200'>
        <thead className='bg-gray-50 sticky top-0'>
          <tr>
            <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
              モデル
            </th>
            <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
              容量
            </th>
            <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
              公式価格
            </th>
            <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
              買取価格
            </th>
            <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
              差額
            </th>
            <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
              差額率
            </th>
          </tr>
        </thead>
        <tbody className='bg-white divide-y divide-gray-200'>
          {rows.map(row => {
            const diffColor = getPriceDiffColor(row.price_diff);
            return (
              <tr key={`${row.series}-${row.capacity}`}>
                <td className='px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900'>
                  {row.series}
                </td>
                <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-900'>
                  {row.capacity}
                </td>
                <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right'>
                  {formatPrice(row.official_price)}
                </td>
                <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right'>
                  {formatPrice(row.kaitori_price)}
                </td>
                <td
                  className={`px-6 py-4 whitespace-nowrap text-sm text-right ${diffColor}`}
                >
                  {formatPrice(row.price_diff)}
                </td>
                <td
                  className={`px-6 py-4 whitespace-nowrap text-sm text-right ${diffColor}`}
                >
                  {formatPercentage(row.price_diff, row.official_price)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
});
