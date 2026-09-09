import { QueryClient } from "@tanstack/react-query";

import { ApiError } from "./client";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        if (error instanceof ApiError && [401, 403, 404, 422].includes(error.status)) {
          return false;
        }
        return failureCount < 2;
      },
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});
