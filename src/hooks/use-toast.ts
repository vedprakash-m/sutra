import { useState, useCallback } from 'react';

interface Toast {
  id: string;
  title?: string;
  description?: string;
  variant?: 'default' | 'destructive';
}

let toastCounter = 0;

export const useToast = () => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback(({ title, description, variant = 'default' }: Omit<Toast, 'id'>) => {
    const id = `toast-${++toastCounter}`;
    const newToast: Toast = { id, title, description, variant };
    
    setToasts(prev => [...prev, newToast]);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 5000);
    
    return id;
  }, []);

  const dismiss = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return {
    toast,
    dismiss,
    toasts
  };
};

// Export toast function directly for easier import
export const toast = {
  success: (message: string) => {
    console.log(`✅ Success: ${message}`);
  },
  error: (message: string) => {
    console.error(`❌ Error: ${message}`);
  },
  info: (message: string) => {
    console.log(`ℹ️ Info: ${message}`);
  },
  // Also support object-style calls
  __call: ({ title, description, variant = 'default' }: Omit<Toast, 'id'>) => {
    console.log(`Toast: ${title} - ${description} (${variant})`);
  }
} as any;
