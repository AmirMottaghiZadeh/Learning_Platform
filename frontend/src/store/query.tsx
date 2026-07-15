import React from "react";
import {QueryClient, QueryClientProvider} from "@tanstack/react-query";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
});

export function AppQueryProvider({children}: {children: React.ReactNode}) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

export {queryClient};
