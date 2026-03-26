import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import Pagination from "@/components/Pagination";

describe("Pagination", () => {
  it("renders nothing for single page", () => {
    const { container } = render(
      <Pagination page={1} pageSize={20} total={5} basePath="/" />
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders page numbers for multiple pages", () => {
    render(
      <Pagination page={1} pageSize={10} total={50} basePath="/" />
    );
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("Showing 1–10 of 50")).toBeInTheDocument();
  });

  it("highlights current page", () => {
    render(
      <Pagination page={2} pageSize={10} total={50} basePath="/" />
    );
    const currentPage = screen.getByText("2");
    expect(currentPage.className).toContain("bg-blue-600");
  });

  it("includes extra params in links", () => {
    render(
      <Pagination
        page={1}
        pageSize={10}
        total={30}
        basePath="/companies"
        extraParams={{ search: "acme" }}
      />
    );
    const link = screen.getByText("2").closest("a");
    expect(link?.getAttribute("href")).toContain("search=acme");
    expect(link?.getAttribute("href")).toContain("page=2");
  });

  it("shows correct range text", () => {
    render(
      <Pagination page={2} pageSize={10} total={25} basePath="/" />
    );
    expect(screen.getByText("Showing 11–20 of 25")).toBeInTheDocument();
  });

  it("shows correct range for last page", () => {
    render(
      <Pagination page={3} pageSize={10} total={25} basePath="/" />
    );
    expect(screen.getByText("Showing 21–25 of 25")).toBeInTheDocument();
  });
});
