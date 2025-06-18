interface ErrorMessageProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export default function ErrorMessage({
  title = "Error",
  message,
  onRetry,
}: ErrorMessageProps) {
  return (
    <div className="text-center py-8">
      <div className="bg-red-50 border border-red-200 rounded-md p-4 inline-block">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-red-400"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3 text-left">
            <h3 className="text-sm font-medium text-red-800">{title}</h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{message}</p>
            </div>
            {onRetry && (
              <div className="mt-3">
                <button
                  onClick={onRetry}
                  className="text-sm font-medium text-red-800 hover:text-red-900 underline"
                >
                  Try again
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
