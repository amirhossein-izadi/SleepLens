import { api } from "./base";
import { User } from "./types";

export const authApi = {
  register: async (data: {
    email: string;
    password: string;
    full_name: string;
  }): Promise<User> => {
    const response = await api.post<{ user: User }>("/accounts/register/", data);
    return response.data.user;
  },

  login: async (data: { email: string; password: string }): Promise<User> => {
    const response = await api.post<{ user: User }>("/accounts/login/", data);
    return response.data.user;
  },

  me: async (): Promise<User> => {
    const response = await api.get<User>("/accounts/me/");
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post("/accounts/logout/");
  },
};
