import { render, screen } from "@testing-library/react";
import ErrorMessage from "../ErrorMessage";

describe("ErrorMessage", () => {
  it("should render error message", () => {
    const errorMessage = "Something went wrong";
    render(<ErrorMessage message={errorMessage} />);

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it("should have proper error styling", () => {
    const errorMessage = "Test error";
    render(<ErrorMessage message={errorMessage} />);

    const errorElement = screen.getByText(errorMessage);
    // Check for the actual CSS classes used in the component
    expect(errorElement.closest(".bg-red-50")).toBeInTheDocument();
  });
});
