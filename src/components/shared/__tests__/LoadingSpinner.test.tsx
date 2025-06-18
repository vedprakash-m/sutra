import { render } from "@testing-library/react";
import LoadingSpinner from "../LoadingSpinner";

describe("LoadingSpinner", () => {
  it("should render loading spinner", () => {
    render(<LoadingSpinner />);

    // Look for the spinning element by its class
    const spinnerElement = document.querySelector(".animate-spin");
    expect(spinnerElement).toBeInTheDocument();
  });

  it("should have proper styling classes", () => {
    render(<LoadingSpinner />);

    // Look for the container div with loading styles
    const container = document.querySelector(
      ".flex.flex-col.items-center.justify-center.py-8",
    );
    expect(container).toBeInTheDocument();

    // Look for the spinning animation element
    const spinner = document.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });
});
