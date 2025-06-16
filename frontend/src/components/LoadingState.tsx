import { Box, Progress, Text, VStack } from '@chakra-ui/react';
import { memo } from 'react';

type LoadingStateProps = {
  message?: string;
};

export const LoadingState = memo(function LoadingState({
  message = 'データを読み込み中...',
}: LoadingStateProps) {
  return (
    <Box
      p={8}
      borderRadius='lg'
      bg='blue.50'
      borderWidth='1px'
      borderColor='blue.200'
      textAlign='center'
    >
      <VStack spacing={4}>
        <Progress
          size='xs'
          isIndeterminate
          width='100%'
          colorScheme='blue'
          borderRadius='full'
        />
        <Text color='blue.600' fontWeight='medium'>
          {message}
        </Text>
      </VStack>
    </Box>
  );
});
