import React from "react";

interface AlertProps {
  children: React.ReactNode;
  className?: string;
  variant?: "default" | "destructive";
}

interface AlertDescriptionProps {
  children: React.ReactNode;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({
  children,
  className = "",
  variant = "default",
}) => {
  const baseClasses = "relative w-full rounded-lg border p-4";

  const variantClasses = {
    default: "border-blue-200 bg-blue-50 text-blue-900",
    destructive: "border-red-200 bg-red-50 text-red-900",
  };

  return (
    <div className={`${baseClasses} ${variantClasses[variant]} ${className}`}>
      {children}
    </div>
  );
};

export const AlertDescription: React.FC<AlertDescriptionProps> = ({
  children,
  className = "",
}) => <div className={`text-sm ${className}`}>{children}</div>;
