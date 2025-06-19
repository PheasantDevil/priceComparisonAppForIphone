import { ComponentType, Suspense, lazy } from 'react';

type LazyLoadProps = {
  component: () => Promise<{ default: ComponentType<Record<string, unknown>> }>;
  fallback?: React.ReactNode;
};

export function LazyLoad({ component, fallback }: LazyLoadProps) {
  const LazyComponent = lazy(component);

  return (
    <Suspense
      fallback={
        fallback || (
          <div className='text-center py-8'>
            <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto'></div>
          </div>
        )
      }
    >
      <LazyComponent />
    </Suspense>
  );
}
