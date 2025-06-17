import { memo, useCallback } from 'react';
import { FiRefreshCw } from 'react-icons/fi';

type ModelSelectorProps = {
  series: string[];
  selectedSeries: string[];
  onSeriesToggle: (series: string) => void;
  onRefresh: () => void;
  loading: boolean;
};

export const ModelSelector = memo(function ModelSelector({
  series,
  selectedSeries,
  onSeriesToggle,
  onRefresh,
  loading,
}: ModelSelectorProps) {
  const handleKeyPress = useCallback(
    (event: React.KeyboardEvent, series: string) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        onSeriesToggle(series);
        alert(
          selectedSeries.includes(series)
            ? `${series}の選択を解除しました`
            : `${series}を選択しました`
        );
      }
    },
    [onSeriesToggle, selectedSeries]
  );

  return (
    <div
      className='p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200'
      role='region'
      aria-label='モデル選択'
    >
      <div className='flex justify-between items-center mb-4 flex-wrap gap-2'>
        <label
          className='font-bold text-sm md:text-base'
          id='model-selector-label'
        >
          比較するモデルを選択：
        </label>
        <button
          onClick={onRefresh}
          disabled={loading}
          className='inline-flex items-center px-4 py-2 text-sm md:text-base font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed'
          aria-label='データを更新'
          aria-busy={loading}
        >
          {loading ? (
            <>
              <div className='animate-spin -ml-1 mr-2 h-4 w-4 text-white'>
                <FiRefreshCw className='h-4 w-4' />
              </div>
              更新中
            </>
          ) : (
            <>
              <FiRefreshCw className='mr-2' />
              データを更新
            </>
          )}
        </button>
      </div>
      <div
        className='flex flex-col md:flex-row gap-4 flex-wrap'
        role='group'
        aria-labelledby='model-selector-label'
      >
        {series.map(model => (
          <label
            key={model}
            className='inline-flex items-center space-x-2 cursor-pointer'
          >
            <input
              type='checkbox'
              checked={selectedSeries.includes(model)}
              onChange={() => onSeriesToggle(model)}
              onKeyPress={e => handleKeyPress(e, model)}
              className='h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
              aria-label={`${model}を選択`}
              tabIndex={0}
            />
            <span className='text-sm md:text-base'>{model}</span>
          </label>
        ))}
      </div>
    </div>
  );
});
