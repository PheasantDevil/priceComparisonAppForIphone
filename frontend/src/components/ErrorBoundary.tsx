import { Box, Button, Heading, Text, VStack } from '@chakra-ui/react';
import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <Box
          p={6}
          borderRadius='lg'
          bg='red.50'
          borderWidth='1px'
          borderColor='red.200'
          textAlign='center'
        >
          <VStack spacing={4}>
            <Heading size='md' color='red.600'>
              予期せぬエラーが発生しました
            </Heading>
            <Text color='red.500'>
              {this.state.error?.message || '不明なエラーが発生しました'}
            </Text>
            <Button
              colorScheme='red'
              variant='outline'
              onClick={this.handleRetry}
              size='sm'
            >
              再試行
            </Button>
          </VStack>
        </Box>
      );
    }

    return this.props.children;
  }
}
