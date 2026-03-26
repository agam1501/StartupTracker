import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { RoundBadge } from "@/components/ui/badge";

describe("RoundBadge", () => {
  it("renders the round type text", () => {
    render(<RoundBadge roundType="Seed" />);
    expect(screen.getByText("Seed")).toBeInTheDocument();
  });

  it("renders Series A with correct styling", () => {
    render(<RoundBadge roundType="Series A" />);
    const badge = screen.getByText("Series A");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("blue");
  });

  it("renders Pre-Seed with correct styling", () => {
    render(<RoundBadge roundType="Pre-Seed" />);
    const badge = screen.getByText("Pre-Seed");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("purple");
  });

  it("renders Unknown with default styling", () => {
    render(<RoundBadge roundType="Unknown" />);
    const badge = screen.getByText("Unknown");
    expect(badge).toBeInTheDocument();
  });

  it("handles unknown round types gracefully", () => {
    render(<RoundBadge roundType="Custom Round" />);
    expect(screen.getByText("Custom Round")).toBeInTheDocument();
  });
});
