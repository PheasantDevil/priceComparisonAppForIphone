import {
  Box,
  Button,
  Checkbox,
  HStack,
  Icon,
  Stack,
  Text,
  useColorModeValue,
  useToast,
} from '@chakra-ui/react';
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
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  const toast = useToast();

  const handleKeyPress = useCallback(
    (event: React.KeyboardEvent, series: string) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        onSeriesToggle(series);
        toast({
          title: selectedSeries.includes(series)
            ? `${series}の選択を解除しました`
            : `${series}を選択しました`,
          status: 'info',
          duration: 2000,
          isClosable: true,
        });
      }
    },
    [onSeriesToggle, selectedSeries, toast]
  );

  return (
    <Box
      p={4}
      borderRadius='lg'
      borderWidth='1px'
      borderColor={borderColor}
      _hover={{ bg: hoverBg }}
      transition='background-color 0.2s'
      role='region'
      aria-label='モデル選択'
    >
      <HStack
        justify='space-between'
        align='center'
        mb={4}
        flexWrap='wrap'
        gap={2}
      >
        <Text
          fontWeight='bold'
          fontSize={['sm', 'md']}
          id='model-selector-label'
        >
          比較するモデルを選択：
        </Text>
        <Button
          onClick={onRefresh}
          isLoading={loading}
          loadingText='更新中'
          colorScheme='blue'
          size={['sm', 'md']}
          leftIcon={<Icon as={FiRefreshCw} />}
          aria-label='データを更新'
          aria-busy={loading}
        >
          データを更新
        </Button>
      </HStack>
      <Stack
        direction={['column', 'row']}
        spacing={4}
        flexWrap='wrap'
        align='flex-start'
        role='group'
        aria-labelledby='model-selector-label'
      >
        {series.map(model => (
          <Checkbox
            key={model}
            isChecked={selectedSeries.includes(model)}
            onChange={() => onSeriesToggle(model)}
            size={['md', 'lg']}
            aria-label={`${model}を選択`}
            onKeyPress={e => handleKeyPress(e, model)}
            tabIndex={0}
            _focus={{
              boxShadow: 'outline',
              outline: 'none',
            }}
          >
            {model}
          </Checkbox>
        ))}
      </Stack>
    </Box>
  );
});
