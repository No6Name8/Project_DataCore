import axios from "axios";
import config from "../config";

const api = axios.create({
  baseURL: config.API_BASE,
  timeout: 10000,
});

export const getBusinesses     = ()           => api.get("/api/businesses");
export const getSummary        = (id)         => api.get(`/api/${id}/summary`);
export const getDSCR           = (id)         => api.get(`/api/${id}/dscr`);
export const getFraud          = (id)         => api.get(`/api/${id}/fraud-check`);
export const getForecast       = (id)         => api.get(`/api/${id}/forecast`);
export const getDashboard      = (id)         => api.get(`/api/dashboard/${id}`);
export const getTransactions   = (id, limit=10) =>
  api.get(`/api/${id}/transactions?limit=${limit}`);
export const assessDBR         = (params)     =>
  api.get("/api/incubator/dbr-assessment", { params });
export const getBusinessProfile = (params)   =>
  api.get("/api/incubator/business-profile", { params });

export default api;
