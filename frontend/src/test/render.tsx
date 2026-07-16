import {QueryClient, QueryClientProvider} from "@tanstack/react-query";
import {render} from "@testing-library/react-native";
import React from "react";

export function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {gcTime: 0, retry: false},
      mutations: {gcTime: 0, retry: false},
    },
  });

  return {
    ...render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>),
    queryClient,
  };
}
