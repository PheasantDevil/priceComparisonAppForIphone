import { memo } from 'react';
import { PricesResponse } from '../lib/api';

type PriceComparisonTableProps = {
  data: Record<string, PricesResponse>;
  selectedSeries: string[];
  loading: boolean;
  showRakutenColumns: boolean;
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

const calculateRakutenDiff = (officialPrice: number, kaitoriPrice: number) => {
  return Math.round(kaitoriPrice - officialPrice * 0.9);
};

const calculateRakutenDiffPercentage = (
  rakutenDiff: number,
  kaitoriPrice: number
) => {
  if (!kaitoriPrice) return 0;
  return (rakutenDiff / kaitoriPrice) * 100;
};

export const PriceComparisonTable = memo(function PriceComparisonTable({
  data,
  selectedSeries,
  loading,
  showRakutenColumns,
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
    rakuten_diff_percentage: number;
  }[] = [];

  selectedSeries.forEach(series => {
    const modelData = data[series];
    if (modelData && modelData.prices) {
      Object.entries(modelData.prices).forEach(([capacity, priceInfo]) => {
        const calculatedRakutenDiff = calculateRakutenDiff(
          priceInfo.official_price,
          priceInfo.kaitori_price
        );
        const calculatedRakutenDiffPercentage = calculateRakutenDiffPercentage(
          calculatedRakutenDiff,
          priceInfo.kaitori_price
        );

        rows.push({
          series,
          capacity,
          official_price: priceInfo.official_price,
          kaitori_price: priceInfo.kaitori_price,
          price_diff: priceInfo.price_diff,
          rakuten_diff: calculatedRakutenDiff,
          rakuten_diff_percentage: calculatedRakutenDiffPercentage,
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
            {showRakutenColumns && (
              <>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  <div className='flex items-center'>
                    楽天錬金時差額
                    <div className='group relative ml-1'>
                      <div className='cursor-help'>
                        <svg
                          className='w-4 h-4 text-gray-400'
                          fill='currentColor'
                          viewBox='0 0 20 20'
                        >
                          <path
                            fillRule='evenodd'
                            d='M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z'
                            clipRule='evenodd'
                          />
                        </svg>
                      </div>
                      <div className='absolute top-full left-1/2 transform -translate-x-1/2 mt-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-50'>
                        買取価格 - (公式価格 × 0.9)
                        <div className='absolute bottom-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-b-4 border-transparent border-b-gray-900'></div>
                      </div>
                    </div>
                  </div>
                </th>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  楽天錬金差額率
                </th>
              </>
            )}
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
                  {row.official_price > 0 ? formatPrice(row.official_price) : 'データなし'}
                </td>
                <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right'>
                  {formatPrice(row.kaitori_price)}
                </td>
                <td
                  className={`px-6 py-4 whitespace-nowrap text-sm text-right ${diffColor}`}
                >
                  {row.official_price > 0 ? formatPrice(row.price_diff) : '-'}
                </td>
                <td
                  className={`px-6 py-4 whitespace-nowrap text-sm text-right ${diffColor}`}
                >
                  {row.official_price > 0 ? formatPercentage(row.price_diff, row.official_price) : '-'}
                </td>
                {showRakutenColumns && (
                  <>
                    <td
                      className={`px-6 py-4 whitespace-nowrap text-sm text-right ${getPriceDiffColor(
                        row.rakuten_diff
                      )}`}
                    >
                      {row.official_price > 0 ? formatPrice(row.rakuten_diff) : '-'}
                    </td>
                    <td
                      className={`px-6 py-4 whitespace-nowrap text-sm text-right ${getPriceDiffColor(
                        row.rakuten_diff
                      )}`}
                    >
                      {row.official_price > 0 ? formatPercentage(row.rakuten_diff, row.kaitori_price) : '-'}
                    </td>
                  </>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
});
