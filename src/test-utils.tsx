import React from "react";
import { render, RenderOptions } from "@testing-library/react";
import { BrowserRouter, MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "react-query";

// Create a custom render function that includes providers with future flags
const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, "wrapper">,
) => render(ui, { wrapper: AllTheProviders, ...options });

// Helper for BrowserRouter with future flags
export const renderWithBrowserRouter = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, "wrapper">,
) => {
  const BrowserRouterWrapper: React.FC<{ children: React.ReactNode }> = ({
    children,
  }) => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
        mutations: {
          retry: false,
        },
      },
    });

    return (
      <QueryClientProvider client={queryClient}>
        <BrowserRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
        >
          {children}
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  return render(ui, { wrapper: BrowserRouterWrapper, ...options });
};

// re-export everything
export * from "@testing-library/react";

// override render method
export { customRender as render };
