'use client';

import React, { useState } from 'react';
import PriceHistoryChart from './PriceHistoryChart';

const PriceHistoryExample: React.FC = () => {
  const [selectedSeries, setSelectedSeries] = useState('iPhone 16 Pro');
  const [selectedCapacity, setSelectedCapacity] = useState('1TB');
  const [selectedDays, setSelectedDays] = useState(14);
  const [tickInterval, setTickInterval] = useState(10000); // Y軸の目盛り間隔

  const seriesOptions = [
    'iPhone 16',
    'iPhone 16 Pro',
    'iPhone 16 Plus',
    'iPhone 16 Pro Max',
    'iPhone 16 e',
  ];

  const capacityOptions = ['128GB', '256GB', '512GB', '1TB'];

  const daysOptions = [7, 14, 30];

  return (
    <div className='max-w-6xl mx-auto p-6'>
      <div className='mb-8'>
        <h1 className='text-3xl font-bold text-gray-900 mb-4'>
          iPhone 価格推移グラフ
        </h1>
        <p className='text-gray-600'>
          過去の価格データをグラフで確認できます。シリーズ、容量、期間を選択してください。
        </p>
      </div>

      {/* コントロールパネル */}
      <div className='bg-white rounded-lg shadow-md p-6 mb-8'>
        <div className='grid grid-cols-1 md:grid-cols-5 gap-4'>
          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              シリーズ
            </label>
            <select
              value={selectedSeries}
              onChange={e => setSelectedSeries(e.target.value)}
              className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            >
              {seriesOptions.map(series => (
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
              value={selectedCapacity}
              onChange={e => setSelectedCapacity(e.target.value)}
              className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            >
              {capacityOptions.map(capacity => (
                <option key={capacity} value={capacity}>
                  {capacity}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              期間
            </label>
            <select
              value={selectedDays}
              onChange={e => setSelectedDays(Number(e.target.value))}
              className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            >
              {daysOptions.map(days => (
                <option key={days} value={days}>
                  過去{days}日間
                </option>
              ))}
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
            <button
              onClick={() => {
                // グラフを再読み込み
                window.location.reload();
              }}
              className='w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500'
            >
              更新
            </button>
          </div>
        </div>
      </div>

      {/* グラフ表示エリア */}
      <div className='bg-white rounded-lg shadow-md p-6'>
        <PriceHistoryChart
          series={selectedSeries}
          capacity={selectedCapacity}
          days={selectedDays}
          height={500}
          className='w-full'
          tickInterval={tickInterval}
        />
      </div>

      {/* 説明 */}
      <div className='mt-8 bg-blue-50 rounded-lg p-6'>
        <h3 className='text-lg font-semibold text-blue-900 mb-2'>
          グラフの見方
        </h3>
        <ul className='text-blue-800 space-y-1'>
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
          <li>• 2週間以上古いデータは自動的に削除されます</li>
        </ul>
      </div>
    </div>
  );
};

export default PriceHistoryExample;
