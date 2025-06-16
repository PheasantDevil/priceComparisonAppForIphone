import { Box, Spinner, Text, VStack } from '@chakra-ui/react';

export const LoadingState = () => {
  return (
    <Box
      p={6}
      borderRadius='lg'
      bg='gray.50'
      borderWidth='1px'
      borderColor='gray.200'
      textAlign='center'
    >
      <VStack spacing={4}>
        <Spinner
          thickness='4px'
          speed='0.65s'
          emptyColor='gray.200'
          color='blue.500'
          size='xl'
        />
        <Text color='gray.600'>データを読み込み中...</Text>
      </VStack>
    </Box>
  );
};
