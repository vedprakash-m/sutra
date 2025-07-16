import React from "react";

interface QualityGateProps {
  score?: number;
  currentScore?: number;
  quality?: any;
  threshold: number;
  title?: string;
  stage?: string;
  description?: string;
  onImprove?: () => void;
}

export const QualityGate: React.FC<QualityGateProps> = ({
  score,
  currentScore,
  quality,
  threshold,
  title = "Quality Gate",
  stage,
  description,
  onImprove,
}) => {
  const actualScore = score || currentScore || quality?.overallScore || 0;
  const isPass = actualScore >= threshold;
  const percentage = Math.round((actualScore / 100) * 100);

  return (
    <div
      className={`p-4 rounded-lg border ${
        isPass
          ? "border-green-200 bg-green-50"
          : "border-yellow-200 bg-yellow-50"
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-gray-900">{title}</h3>
        <div
          className={`px-2 py-1 rounded text-sm font-medium ${
            isPass
              ? "bg-green-100 text-green-800"
              : "bg-yellow-100 text-yellow-800"
          }`}
        >
          {percentage}%
        </div>
      </div>
      {description && (
        <p className="text-sm text-gray-600 mb-3">{description}</p>
      )}
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-300 ${
            isPass ? "bg-green-500" : "bg-yellow-500"
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="flex justify-between items-center mt-2 text-xs text-gray-500">
        <span>Threshold: {threshold}%</span>
        <span className={isPass ? "text-green-600" : "text-yellow-600"}>
          {isPass ? "✓ Pass" : "⚠ Below Threshold"}
        </span>
      </div>
    </div>
  );
};
