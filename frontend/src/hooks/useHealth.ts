import { useEffect, useState } from 'react';
import { healthService } from '@/services/healthService';
import { HealthResponse } from '@/types';

export function useHealth() {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isError, setIsError] = useState<boolean>(false);

  useEffect(() => {
    healthService
      .getHealth()
      .then((res) => {
        setData(res);
        setIsLoading(false);
      })
      .catch(() => {
        setIsError(true);
        setIsLoading(false);
      });
  }, []);

  return { data, isLoading, isError };
}
