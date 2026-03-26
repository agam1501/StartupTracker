import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

// Must import after mocking fetch
import {
  getCompanies,
  getCompany,
  getFundingRounds,
  getInvestors,
  getStats,
} from "@/lib/api";

describe("API client", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  function mockResponse(data: unknown, status = 200) {
    mockFetch.mockResolvedValueOnce({
      ok: status >= 200 && status < 300,
      status,
      statusText: status === 200 ? "OK" : "Error",
      json: () => Promise.resolve(data),
    });
  }

  describe("getCompanies", () => {
    it("fetches companies with no params", async () => {
      mockResponse({ items: [], total: 0, page: 1, page_size: 20 });

      const result = await getCompanies();
      expect(result.items).toEqual([]);
      expect(mockFetch).toHaveBeenCalledTimes(1);

      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("/companies");
    });

    it("includes search and pagination params", async () => {
      mockResponse({ items: [], total: 0, page: 1, page_size: 10 });

      await getCompanies({ search: "acme", page: 2, page_size: 10 });

      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("search=acme");
      expect(url).toContain("page=2");
      expect(url).toContain("page_size=10");
    });

    it("throws on API error", async () => {
      mockResponse(null, 500);

      await expect(getCompanies()).rejects.toThrow("API error");
    });
  });

  describe("getCompany", () => {
    it("fetches a company by ID", async () => {
      const mockCompany = {
        id: "abc-123",
        name: "Acme",
        funding_rounds: [],
      };
      mockResponse(mockCompany);

      const result = await getCompany("abc-123");
      expect(result.name).toBe("Acme");

      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("/companies/abc-123");
    });
  });

  describe("getFundingRounds", () => {
    it("includes round_type filter", async () => {
      mockResponse({ items: [], total: 0, page: 1, page_size: 20 });

      await getFundingRounds({ round_type: "Seed" });

      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("round_type=Seed");
    });
  });

  describe("getInvestors", () => {
    it("includes search param", async () => {
      mockResponse({ items: [], total: 0, page: 1, page_size: 20 });

      await getInvestors({ search: "sequoia" });

      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("search=sequoia");
    });
  });

  describe("getStats", () => {
    it("fetches stats", async () => {
      const mockStats = {
        total_companies: 10,
        total_rounds: 25,
        total_investors: 15,
        total_funding_usd: 50000000,
      };
      mockResponse(mockStats);

      const result = await getStats();
      expect(result.total_companies).toBe(10);

      const url = mockFetch.mock.calls[0][0] as string;
      expect(url).toContain("/stats");
    });
  });
});
