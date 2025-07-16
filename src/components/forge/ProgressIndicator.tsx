import React from "react";

interface ProgressIndicatorProps {
  currentStep?: number;
  current?: number;
  totalSteps?: number;
  steps?: string[];
  threshold?: number;
  label?: string;
  className?: string;
}

export const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  currentStep,
  current,
  totalSteps,
  steps,
  threshold,
  label,
  className = "",
}) => {
  const actualCurrentStep = currentStep ?? current ?? 0;
  const actualTotalSteps = totalSteps ?? steps?.length ?? 5;
  const actualSteps =
    steps ??
    Array.from({ length: actualTotalSteps }, (_, i) => `Step ${i + 1}`);
  return (
    <div className={`w-full ${className}`}>
      <div className="flex justify-between mb-2">
        {steps.map((step, index) => (
          <div key={index} className="flex flex-col items-center">
            <div
              className={`
              w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
              ${
                index < currentStep
                  ? "bg-green-500 text-white"
                  : index === currentStep
                    ? "bg-blue-500 text-white"
                    : "bg-gray-200 text-gray-600"
              }
            `}
            >
              {index < currentStep ? "✓" : index + 1}
            </div>
            <span
              className={`
              mt-2 text-xs text-center max-w-20
              ${index <= currentStep ? "text-gray-900" : "text-gray-500"}
            `}
            >
              {step}
            </span>
          </div>
        ))}
      </div>

      <div className="relative">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${(currentStep / (totalSteps - 1)) * 100}%` }}
          />
        </div>
      </div>

      <div className="flex justify-between text-xs text-gray-500 mt-2">
        <span>
          Step {currentStep + 1} of {totalSteps}
        </span>
        <span>
          {Math.round(((currentStep + 1) / totalSteps) * 100)}% Complete
        </span>
      </div>
    </div>
  );
};
