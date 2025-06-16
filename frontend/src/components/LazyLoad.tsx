import { Box, Spinner } from '@chakra-ui/react';
import { ComponentType, Suspense, lazy } from 'react';

type LazyLoadProps = {
  component: () => Promise<{ default: ComponentType<any> }>;
  fallback?: React.ReactNode;
};

export function LazyLoad({ component, fallback }: LazyLoadProps) {
  const LazyComponent = lazy(component);

  return (
    <Suspense
      fallback={
        fallback || (
          <Box textAlign='center' py={8}>
            <Spinner size='xl' />
          </Box>
        )
      }
    >
      <LazyComponent />
    </Suspense>
  );
}
