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
      <Box
        textAlign='center'
        py={8}
        role='status'
        aria-label='データを読み込み中'
      >
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
        role='status'
        aria-label='モデルが選択されていません'
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
      role='region'
      aria-label='価格比較テーブル'
    >
      <Table
        variant='simple'
        size={['sm', 'md']}
        role='grid'
        aria-label='iPhone価格比較'
      >
        <Thead position='sticky' top={0} bg={headerBg}>
          <Tr>
            <Th scope='col' role='columnheader'>
              容量
            </Th>
            {selectedSeries.map(series => (
              <Th
                key={series}
                colSpan={4}
                scope='colgroup'
                role='columnheader'
                aria-label={`${series}の価格情報`}
              >
                {series}
              </Th>
            ))}
          </Tr>
          <Tr>
            <Th scope='col' role='columnheader'></Th>
            {selectedSeries.map(series => (
              <>
                <Th
                  scope='col'
                  role='columnheader'
                  aria-label={`${series}の公式価格`}
                >
                  公式価格
                </Th>
                <Th
                  scope='col'
                  role='columnheader'
                  aria-label={`${series}の買取価格`}
                >
                  買取価格
                </Th>
                <Th
                  scope='col'
                  role='columnheader'
                  aria-label={`${series}の差額`}
                >
                  差額
                </Th>
                <Th
                  scope='col'
                  role='columnheader'
                  aria-label={`${series}の差額率`}
                >
                  差額率
                </Th>
              </>
            ))}
          </Tr>
        </Thead>
        <Tbody>
          {getUniqueCapacities(data).map(capacity => (
            <Tr key={capacity} role='row'>
              <Td
                fontWeight='bold'
                whiteSpace='nowrap'
                role='cell'
                aria-label={`容量: ${capacity}`}
              >
                {capacity}
              </Td>
              {selectedSeries.map(series => {
                const priceInfo = getModelPrice(data, series, capacity);
                if (!priceInfo)
                  return (
                    <Td
                      key={series}
                      colSpan={4}
                      role='cell'
                      aria-label={`${series}の${capacity}の価格情報はありません`}
                    >
                      -
                    </Td>
                  );

                return (
                  <>
                    <Td
                      isNumeric
                      whiteSpace='nowrap'
                      role='cell'
                      aria-label={`${series}の${capacity}の公式価格: ${formatPrice(
                        priceInfo.official_price
                      )}`}
                    >
                      {formatPrice(priceInfo.official_price)}
                    </Td>
                    <Td
                      isNumeric
                      whiteSpace='nowrap'
                      role='cell'
                      aria-label={`${series}の${capacity}の買取価格: ${formatPrice(
                        priceInfo.kaitori_price
                      )}`}
                    >
                      {formatPrice(priceInfo.kaitori_price)}
                    </Td>
                    <Td
                      isNumeric
                      color={getPriceDiffColor(priceInfo.price_diff)}
                      whiteSpace='nowrap'
                      role='cell'
                      aria-label={`${series}の${capacity}の差額: ${formatPrice(
                        priceInfo.price_diff
                      )}`}
                    >
                      {formatPrice(priceInfo.price_diff)}
                    </Td>
                    <Td
                      isNumeric
                      color={getPriceDiffColor(priceInfo.price_diff)}
                      whiteSpace='nowrap'
                      role='cell'
                      aria-label={`${series}の${capacity}の差額率: ${formatPercentage(
                        priceInfo.price_diff,
                        priceInfo.official_price
                      )}`}
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
