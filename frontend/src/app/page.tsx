'use client';

import {
  Box,
  Container,
  Heading,
  Text,
  useColorModeValue,
  useToast,
  VStack,
} from '@chakra-ui/react';
import { useCallback, useEffect, useState } from 'react';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { LoadingState } from '../components/LoadingState';
import { ModelSelector } from '../components/ModelSelector';
import { PriceComparisonTable } from '../components/PriceComparisonTable';
import { clearCache, fetchPrices, PricesResponse } from '../lib/api';

const SERIES = ['iPhone 16', 'iPhone 16 Pro'];
const STORAGE_KEY = 'selected_iphone_models';

export default function Home() {
  const [selectedSeries, setSelectedSeries] = useState<string[]>([]);
  const [data, setData] = useState<Record<string, PricesResponse>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const toast = useToast();

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  // ローカルストレージから選択状態を読み込む
  useEffect(() => {
    try {
      const savedSeries = localStorage.getItem(STORAGE_KEY);
      if (savedSeries) {
        const parsed = JSON.parse(savedSeries);
        if (Array.isArray(parsed) && parsed.every(s => SERIES.includes(s))) {
          setSelectedSeries(parsed);
        }
      }
    } catch (error) {
      console.error('Failed to load saved series:', error);
      toast({
        title: '設定の読み込みに失敗しました',
        description: 'デフォルト設定を使用します',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
    }
  }, [toast]);

  // 選択状態をローカルストレージに保存
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(selectedSeries));
    } catch (error) {
      console.error('Failed to save series:', error);
      toast({
        title: '選択状態の保存に失敗しました',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  }, [selectedSeries, toast]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const newData: Record<string, PricesResponse> = {};
      for (const series of selectedSeries) {
        const response = await fetchPrices(series);
        newData[series] = response;
      }
      setData(newData);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      setError(
        error instanceof Error ? error : new Error('データの取得に失敗しました')
      );
      toast({
        title: 'データの取得に失敗しました',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  }, [selectedSeries, toast]);

  useEffect(() => {
    if (selectedSeries.length > 0) {
      fetchData();
    }
  }, [selectedSeries, fetchData]);

  const handleRefresh = useCallback(async () => {
    clearCache();
    await fetchData();
    toast({
      title: 'データを更新しました',
      status: 'success',
      duration: 2000,
      isClosable: true,
    });
  }, [fetchData, toast]);

  const handleSeriesToggle = useCallback((series: string) => {
    setSelectedSeries(prev =>
      prev.includes(series) ? prev.filter(s => s !== series) : [...prev, series]
    );
  }, []);

  return (
    <ErrorBoundary>
      <Container maxW='container.lg' py={8}>
        <Box
          bg={bgColor}
          p={6}
          borderRadius='lg'
          boxShadow='base'
          borderWidth='1px'
          borderColor={borderColor}
        >
          <Heading mb={6} textAlign='center' size='lg'>
            iPhone 価格比較
          </Heading>

          <VStack spacing={4} align='stretch' mb={6}>
            <ModelSelector
              series={SERIES}
              selectedSeries={selectedSeries}
              onSeriesToggle={handleSeriesToggle}
              onRefresh={handleRefresh}
              loading={loading}
            />
          </VStack>

          {loading ? (
            <LoadingState />
          ) : error ? (
            <Box
              p={4}
              borderRadius='md'
              bg='red.50'
              borderWidth='1px'
              borderColor='red.200'
              textAlign='center'
            >
              <Heading size='sm' color='red.600' mb={2}>
                エラーが発生しました
              </Heading>
              <Text color='red.500'>{error.message}</Text>
            </Box>
          ) : (
            <PriceComparisonTable
              data={data}
              selectedSeries={selectedSeries}
              loading={loading}
            />
          )}
        </Box>
      </Container>
    </ErrorBoundary>
  );
}
