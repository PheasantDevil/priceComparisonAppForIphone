import {
  Box,
  Spinner,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  useColorModeValue,
} from '@chakra-ui/react';
import { memo } from 'react';
import { PricesResponse } from '../lib/api';

type PriceComparisonTableProps = {
  data: Record<string, PricesResponse>;
  selectedSeries: string[];
  loading: boolean;
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

const getUniqueCapacities = (data: Record<string, PricesResponse>) => {
  const capacities = new Set<string>();
  Object.values(data).forEach(modelData => {
    Object.keys(modelData.prices).forEach(capacity => {
      capacities.add(capacity);
    });
  });
  return Array.from(capacities).sort();
};

const getModelPrice = (
  data: Record<string, PricesResponse>,
  series: string,
  capacity: string
) => {
  return data[series]?.prices[capacity] || null;
};

export const PriceComparisonTable = memo(function PriceComparisonTable({
  data,
  selectedSeries,
  loading,
}: PriceComparisonTableProps) {
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const headerBg = useColorModeValue('gray.50', 'gray.700');

  if (loading) {
    return (
      <Box textAlign='center' py={8}>
        <Spinner size='xl' />
        <Text mt={4}>データを読み込み中...</Text>
      </Box>
    );
  }

  if (selectedSeries.length === 0) {
    return (
      <Box
        textAlign='center'
        py={8}
        color='gray.500'
        bg='gray.50'
        borderRadius='md'
      >
        比較するモデルを選択してください
      </Box>
    );
  }

  return (
    <TableContainer
      maxW='100%'
      overflowX='auto'
      css={{
        '&::-webkit-scrollbar': {
          height: '8px',
        },
        '&::-webkit-scrollbar-track': {
          background: 'transparent',
        },
        '&::-webkit-scrollbar-thumb': {
          background: borderColor,
          borderRadius: '4px',
        },
      }}
    >
      <Table variant='simple' size={['sm', 'md']}>
        <Thead position='sticky' top={0} bg={headerBg}>
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
          {getUniqueCapacities(data).map(capacity => (
            <Tr key={capacity}>
              <Td fontWeight='bold' whiteSpace='nowrap'>
                {capacity}
              </Td>
              {selectedSeries.map(series => {
                const priceInfo = getModelPrice(data, series, capacity);
                if (!priceInfo)
                  return (
                    <Td key={series} colSpan={4}>
                      -
                    </Td>
                  );

                return (
                  <>
                    <Td isNumeric whiteSpace='nowrap'>
                      {formatPrice(priceInfo.official_price)}
                    </Td>
                    <Td isNumeric whiteSpace='nowrap'>
                      {formatPrice(priceInfo.kaitori_price)}
                    </Td>
                    <Td
                      isNumeric
                      color={getPriceDiffColor(priceInfo.price_diff)}
                      whiteSpace='nowrap'
                    >
                      {formatPrice(priceInfo.price_diff)}
                    </Td>
                    <Td
                      isNumeric
                      color={getPriceDiffColor(priceInfo.price_diff)}
                      whiteSpace='nowrap'
                    >
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
    </TableContainer>
  );
});
