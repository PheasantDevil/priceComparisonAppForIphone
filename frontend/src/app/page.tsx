'use client';

import {
  Box,
  Button,
  Checkbox,
  Container,
  Heading,
  HStack,
  Spinner,
  Stack,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  useColorModeValue,
  useToast,
  VStack,
} from '@chakra-ui/react';
import { useEffect, useState } from 'react';
import { clearCache, fetchPrices, PricesResponse } from '../lib/api';

const SERIES = ['iPhone 16', 'iPhone 16 Pro'];
const STORAGE_KEY = 'selected_iphone_models';

export default function Home() {
  const [selectedSeries, setSelectedSeries] = useState<string[]>([]);
  const [data, setData] = useState<Record<string, PricesResponse>>({});
  const [loading, setLoading] = useState(false);
  const [sortBy, setSortBy] = useState<'capacity' | 'price_diff'>('capacity');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
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
    }
  }, []);

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

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const newData: Record<string, PricesResponse> = {};
        for (const series of selectedSeries) {
          const response = await fetchPrices(series);
          newData[series] = response;
        }
        setData(newData);
      } catch (error) {
        console.error('Failed to fetch data:', error);
        toast({
          title: 'データの取得に失敗しました',
          status: 'error',
          duration: 3000,
          isClosable: true,
        });
      } finally {
        setLoading(false);
      }
    };

    if (selectedSeries.length > 0) {
      fetchData();
    }
  }, [selectedSeries, toast]);

  const handleRefresh = async () => {
    clearCache();
    setLoading(true);
    try {
      const newData: Record<string, PricesResponse> = {};
      for (const series of selectedSeries) {
        const response = await fetchPrices(series);
        newData[series] = response;
      }
      setData(newData);
      toast({
        title: 'データを更新しました',
        status: 'success',
        duration: 2000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Failed to refresh data:', error);
      toast({
        title: 'データの更新に失敗しました',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price: number) => {
    return `${price.toLocaleString()}円`;
  };

  const formatPercentage = (price: number, basePrice: number) => {
    const percentage = (price / basePrice) * 100;
    return `${percentage.toFixed(1)}%`;
  };

  const getPriceDiffColor = (diff: number) => {
    if (diff > 0) return 'green.500';
    if (diff < 0) return 'red.500';
    return 'gray.500';
  };

  const handleSeriesToggle = (series: string) => {
    setSelectedSeries(prev =>
      prev.includes(series) ? prev.filter(s => s !== series) : [...prev, series]
    );
  };

  const getUniqueCapacities = () => {
    const capacities = new Set<string>();
    Object.values(data).forEach(modelData => {
      Object.keys(modelData.prices).forEach(capacity => {
        capacities.add(capacity);
      });
    });
    return Array.from(capacities).sort();
  };

  const getModelPrice = (series: string, capacity: string) => {
    return data[series]?.prices[capacity] || null;
  };

  return (
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
          <HStack justify='space-between' align='center'>
            <Text fontWeight='bold'>比較するモデルを選択：</Text>
            <Button
              onClick={handleRefresh}
              isLoading={loading}
              loadingText='更新中'
              colorScheme='blue'
              size='sm'
            >
              データを更新
            </Button>
          </HStack>
          <Stack direction={['column', 'row']} spacing={4}>
            {SERIES.map(series => (
              <Checkbox
                key={series}
                isChecked={selectedSeries.includes(series)}
                onChange={() => handleSeriesToggle(series)}
                size='lg'
              >
                {series}
              </Checkbox>
            ))}
          </Stack>
        </VStack>

        {loading ? (
          <Box textAlign='center' py={8}>
            <Spinner size='xl' />
            <Text mt={4}>データを読み込み中...</Text>
          </Box>
        ) : selectedSeries.length > 0 ? (
          <Box overflowX='auto'>
            <Table variant='simple'>
              <Thead>
                <Tr>
                  <Th>容量</Th>
                  {selectedSeries.map(series => (
                    <Th key={series} colSpan={4}>
                      {series}
                    </Th>
                  ))}
                </Tr>
                <Tr>
                  <Th></Th>
                  {selectedSeries.map(series => (
                    <>
                      <Th>公式価格</Th>
                      <Th>買取価格</Th>
                      <Th>差額</Th>
                      <Th>差額率</Th>
                    </>
                  ))}
                </Tr>
              </Thead>
              <Tbody>
                {getUniqueCapacities().map(capacity => (
                  <Tr key={capacity}>
                    <Td fontWeight='bold'>{capacity}</Td>
                    {selectedSeries.map(series => {
                      const priceInfo = getModelPrice(series, capacity);
                      if (!priceInfo)
                        return (
                          <Td key={series} colSpan={4}>
                            -
                          </Td>
                        );

                      return (
                        <>
                          <Td>{formatPrice(priceInfo.official_price)}</Td>
                          <Td>{formatPrice(priceInfo.kaitori_price)}</Td>
                          <Td color={getPriceDiffColor(priceInfo.price_diff)}>
                            {formatPrice(priceInfo.price_diff)}
                          </Td>
                          <Td color={getPriceDiffColor(priceInfo.price_diff)}>
                            {formatPercentage(
                              priceInfo.price_diff,
                              priceInfo.official_price
                            )}
                          </Td>
                        </>
                      );
                    })}
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </Box>
        ) : (
          <Box
            textAlign='center'
            py={8}
            color='gray.500'
            bg='gray.50'
            borderRadius='md'
          >
            比較するモデルを選択してください
          </Box>
        )}
      </Box>
    </Container>
  );
}
