import axios from "axios";
import config from "../config";
import * as store from "./datastore";

const api = axios.create({
  baseURL: config.API_BASE,
  timeout: 10000,
});

// In production (Vercel), serve everything from static data — no Flask backend.
// In local dev, proxy to Flask running on localhost:5000.
const STATIC = import.meta.env.PROD;

export const getBusinesses      = ()              => api.get("/api/businesses");
export const getSummary         = (id)            => api.get(`/api/${id}/summary`);
export const getDSCR            = (id)            => api.get(`/api/${id}/dscr`);
export const getFraud           = (id)            => api.get(`/api/${id}/fraud-check`);
export const getTransactions    = (id, limit = 10) => api.get(`/api/${id}/transactions?limit=${limit}`);

export const getDashboard = (id) =>
  STATIC ? store.getDashboard(id) : api.get(`/api/dashboard/${id}`);

export const getForecast = (id) =>
  STATIC ? store.getForecast(id) : api.get(`/api/${id}/forecast`);

export const getPortfolioSummary = () =>
  STATIC ? store.getPortfolioSummary() : api.get("/api/portfolio/summary");

export const getPortfolioStats = () =>
  STATIC ? store.getPortfolioStats() : api.get("/api/portfolio/stats");

export const getPortfolioBusiness = (bid) =>
  STATIC ? store.getPortfolioBusiness(bid) : api.get(`/api/portfolio/business/${bid}`);

export const assessDBR = (params) =>
  STATIC ? store.assessDBR(params) : api.get("/api/incubator/dbr-assessment", { params });

export const getBusinessProfile = (params) =>
  STATIC ? store.getBusinessProfile(params) : api.get("/api/incubator/business-profile", { params });

export default api;
