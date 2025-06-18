'use client';

import axios from 'axios';
import React, { useCallback, useEffect, useState } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

interface PriceHistoryData {
  date: string;
  timestamp: number;
  price_min: number;
  price_max: number;
  price_avg: number;
}

interface PriceHistoryResponse {
  series: string;
  capacity: string;
  days: number;
  history: PriceHistoryData[];
}

interface PriceHistoryChartProps {
  series: string;
  capacity: string;
  days?: number;
  height?: number;
  className?: string;
}

const PriceHistoryChart: React.FC<PriceHistoryChartProps> = ({
  series,
  capacity,
  days = 14,
  height = 400,
  className = '',
}) => {
  const [data, setData] = useState<PriceHistoryData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPriceHistory = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.get<PriceHistoryResponse>(
        `https://us-central1-price-comparison-app-463007.cloudfunctions.net/get_price_history`,
        {
          params: {
            series,
            capacity,
            days,
          },
        }
      );

      setData(response.data.history);
    } catch (err) {
      console.error('Error fetching price history:', err);
      setError('価格履歴の取得に失敗しました');
    } finally {
      setLoading(false);
    }
  }, [series, capacity, days]);

  useEffect(() => {
    fetchPriceHistory();
  }, [series, capacity, days, fetchPriceHistory]);

  const formatPrice = (value: number) => {
    return `¥${value.toLocaleString()}`;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ja-JP', {
      month: 'short',
      day: 'numeric',
    });
  };

  if (loading) {
    return (
      <div
        className={`flex items-center justify-center ${className}`}
        style={{ height }}
      >
        <div className='text-gray-500'>読み込み中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className={`flex items-center justify-center ${className}`}
        style={{ height }}
      >
        <div className='text-red-500'>{error}</div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div
        className={`flex items-center justify-center ${className}`}
        style={{ height }}
      >
        <div className='text-gray-500'>価格履歴データがありません</div>
      </div>
    );
  }

  return (
    <div className={`w-full ${className}`}>
      <div className='mb-4'>
        <h3 className='text-lg font-semibold text-gray-800'>
          {series} {capacity} 価格推移（過去{days}日間）
        </h3>
      </div>

      <ResponsiveContainer width='100%' height={height}>
        <AreaChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray='3 3' />
          <XAxis
            dataKey='date'
            tickFormatter={formatDate}
            tick={{ fontSize: 12 }}
          />
          <YAxis tickFormatter={formatPrice} tick={{ fontSize: 12 }} />
          <Tooltip
            formatter={(value: number) => [formatPrice(value), '価格']}
            labelFormatter={label => formatDate(label as string)}
          />
          <Legend />

          {/* 平均価格（メインライン） */}
          <Area
            type='monotone'
            dataKey='price_avg'
            stroke='#4CAF50'
            fill='rgba(76, 175, 80, 0.1)'
            strokeWidth={3}
            name='平均価格'
          />

          {/* 最高価格 */}
          <Line
            type='monotone'
            dataKey='price_max'
            stroke='#FF9800'
            strokeWidth={2}
            dot={{ fill: '#FF9800', strokeWidth: 2, r: 4 }}
            name='最高価格'
          />

          {/* 最低価格 */}
          <Line
            type='monotone'
            dataKey='price_min'
            stroke='#F44336'
            strokeWidth={2}
            dot={{ fill: '#F44336', strokeWidth: 2, r: 4 }}
            name='最低価格'
          />
        </AreaChart>
      </ResponsiveContainer>

      <div className='mt-4 flex justify-center space-x-6 text-sm'>
        <div className='flex items-center'>
          <div className='w-3 h-3 bg-green-500 rounded mr-2'></div>
          <span>平均価格</span>
        </div>
        <div className='flex items-center'>
          <div className='w-3 h-3 bg-orange-500 rounded mr-2'></div>
          <span>最高価格</span>
        </div>
        <div className='flex items-center'>
          <div className='w-3 h-3 bg-red-500 rounded mr-2'></div>
          <span>最低価格</span>
        </div>
      </div>
    </div>
  );
};

export default PriceHistoryChart;
