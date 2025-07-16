import React from "react";

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

interface CardTitleProps {
  children: React.ReactNode;
  className?: string;
}

interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ children, className = "" }) => (
  <div
    className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}
  >
    {children}
  </div>
);

export const CardHeader: React.FC<CardHeaderProps> = ({
  children,
  className = "",
}) => <div className={`p-6 pb-0 ${className}`}>{children}</div>;

export const CardTitle: React.FC<CardTitleProps> = ({
  children,
  className = "",
}) => (
  <h3 className={`text-lg font-semibold text-gray-900 ${className}`}>
    {children}
  </h3>
);

export const CardContent: React.FC<CardContentProps> = ({
  children,
  className = "",
}) => <div className={`p-6 pt-0 ${className}`}>{children}</div>;
