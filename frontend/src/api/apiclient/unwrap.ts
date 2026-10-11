import type { ApiResponse } from '@/types/api';

export function unwrapResponse<T>(response: T | ApiResponse<T>): T {
  if (
    response &&
    typeof response === 'object' &&
    'success' in response &&
    response.success &&
    'data' in response
  ) {
    return response.data as T;
  }

  return response as T;
}
