import axios, { AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios';

import type { ApiResponse } from '@/types/api';

export interface ApiError {
  code: string;
  message: string;
  status?: number;
  details?: unknown;
}

function createApiClient(baseURL: string) {
  const instance = axios.create({
    baseURL,
    headers: {
      Accept: 'application/json',
    },
  });

  instance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    if (typeof window !== 'undefined' && !window.navigator.onLine) {
      return Promise.reject({
        code: 'NETWORK_OFFLINE',
        message: 'You are offline. Please check your internet connection.',
      } satisfies ApiError);
    }

    if (config.data instanceof FormData) {
      config.headers.delete('Content-Type');
    } else if (!config.headers.has('Content-Type')) {
      config.headers.set('Content-Type', 'application/json');
    }

    return config;
  });

  instance.interceptors.response.use(
    (response: AxiosResponse) => {
      const data = response.data;

      if (data && typeof data === 'object' && 'success' in data) {
        if (data.success === false) {
          const wrapped = data.error as ApiError | undefined;
          return Promise.reject(
            wrapped ||
              ({
                code: 'api_error',
                message: 'An unknown error occurred',
              } satisfies ApiError),
          );
        }
        return data;
      }

      return response.data;
    },
    (error: AxiosError) => {
      if (!error.response) {
        return Promise.reject({
          code: 'network_error',
          message: 'Unable to reach the API.',
          status: 0,
        } satisfies ApiError);
      }

      const responseData = error.response.data as
        | ApiResponse<unknown>
        | Record<string, unknown>
        | undefined;

      if (
        responseData &&
        typeof responseData === 'object' &&
        'success' in responseData &&
        responseData.success === false
      ) {
        const wrapped = (responseData as { error?: ApiError }).error;
        return Promise.reject({
          code: wrapped?.code || 'api_error',
          message: wrapped?.message || 'Request failed.',
          status: error.response.status,
          details: wrapped?.details,
        } satisfies ApiError);
      }

      return Promise.reject({
        code: 'api_error',
        message: 'Request failed.',
        status: error.response.status,
        details: responseData,
      } satisfies ApiError);
    },
  );

  return instance;
}

const api = createApiClient(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');

export default api;
