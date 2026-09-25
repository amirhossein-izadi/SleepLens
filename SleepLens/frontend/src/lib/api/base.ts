"use client";

import axios, {
  AxiosError,
  AxiosInstance,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from "axios";
import { useAuthStore } from "../store";

const rawApiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
export const API_ORIGIN = rawApiUrl.replace(/\/+$/, "");
const API_URL = `${API_ORIGIN}/api/v1`;

/**
 * Base axios instance.
 *
 * The backend wraps every JSON response in an envelope:
 *   { success: true, data: …, metadata?: { total, page, limit, pages } }
 *   { success: false, data: null, error: { code, message, details } }
 *
 * This interceptor unwraps `data` for callers, stores `metadata` on the
 * response, and rejects business errors with an axios-like error object so
 * `extractErrorMessage` can read them uniformly.
 */

interface Envelope {
  success?: boolean;
  data?: unknown;
  metadata?: { total?: number; page?: number; limit?: number; pages?: number };
  error?: { code?: string; message?: string; details?: unknown };
}

declare module "axios" {
  export interface AxiosResponse {
    metadata?: Envelope["metadata"];
  }
}

export const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (response) => {
    const body = response.data as Envelope | undefined;
    if (
      body &&
      typeof body === "object" &&
      (body.success === true || body.success === false)
    ) {
      if (body.success === false) {
        return Promise.reject({
          response,
          message: body.error?.message || "Request failed",
          code: body.error?.code,
          details: body.error?.details,
        });
      }
      response.data = body.data;
      response.metadata = body.metadata;
    }
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (!originalRequest) return Promise.reject(error);

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        await axios.post(`${API_URL}/accounts/token/refresh/`, {}, { withCredentials: true });
        return api(originalRequest);
      } catch (refreshError) {
        useAuthStore.getState().logout();
        if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);
