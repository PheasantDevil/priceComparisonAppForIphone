export const LoadingState = () => {
  return (
    <div className='p-6 rounded-lg bg-gray-50 border border-gray-200 text-center'>
      <div className='flex flex-col items-center space-y-4'>
        <div className='animate-spin rounded-full h-12 w-12 border-4 border-gray-200 border-t-blue-500'></div>
        <p className='text-gray-600'>データを読み込み中...</p>
      </div>
    </div>
  );
};
