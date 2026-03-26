import { describe, it, expect } from "vitest";
import { formatUSD, formatDate } from "@/lib/format";

describe("formatUSD", () => {
  it("formats billions", () => {
    expect(formatUSD("2500000000")).toBe("$2.5B");
  });

  it("formats millions", () => {
    expect(formatUSD("5000000")).toBe("$5.0M");
  });

  it("formats thousands", () => {
    expect(formatUSD("750000")).toBe("$750K");
  });

  it("formats small amounts", () => {
    expect(formatUSD("500")).toBe("$500");
  });

  it("returns Undisclosed for null", () => {
    expect(formatUSD(null)).toBe("Undisclosed");
  });

  it("returns Undisclosed for empty string", () => {
    expect(formatUSD("")).toBe("Undisclosed");
  });

  it("handles exact billion boundary", () => {
    expect(formatUSD("1000000000")).toBe("$1.0B");
  });

  it("handles exact million boundary", () => {
    expect(formatUSD("1000000")).toBe("$1.0M");
  });

  it("handles exact thousand boundary", () => {
    expect(formatUSD("1000")).toBe("$1K");
  });
});

describe("formatDate", () => {
  it("formats a valid date", () => {
    const result = formatDate("2026-03-15");
    expect(result).toContain("Mar");
    expect(result).toContain("2026");
    // Date may show 14 or 15 depending on timezone
    expect(result).toMatch(/1[45]/);
  });

  it("returns Unknown for null", () => {
    expect(formatDate(null)).toBe("Unknown");
  });

  it("returns Unknown for empty string", () => {
    // Empty string creates Invalid Date
    expect(formatDate("")).toBe("Unknown");
  });

  it("formats another date correctly", () => {
    const result = formatDate("2025-12-25");
    expect(result).toContain("Dec");
    expect(result).toContain("25");
    expect(result).toContain("2025");
  });
});
