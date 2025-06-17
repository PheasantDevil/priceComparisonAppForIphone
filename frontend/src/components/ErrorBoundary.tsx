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
        <div className='p-6 rounded-lg bg-red-50 border border-red-200 text-center'>
          <div className='flex flex-col items-center space-y-4'>
            <h2 className='text-lg font-semibold text-red-600'>
              予期せぬエラーが発生しました
            </h2>
            <p className='text-red-500'>
              {this.state.error?.message || '不明なエラーが発生しました'}
            </p>
            <button
              className='px-4 py-2 text-sm font-medium text-red-600 bg-white border border-red-600 rounded-md hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500'
              onClick={this.handleRetry}
            >
              再試行
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
