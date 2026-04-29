import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

export const logInteraction = async (payload) => {
  const response = await api.post("/log-interaction", payload);
  return response.data;
};

export const chatWithAgent = async (message) => {
  const response = await api.post("/chat", { message });
  return response.data;
};

export const fetchInteractions = async () => {
  const response = await api.get("/interactions");
  return response.data;
};

export const updateInteraction = async (id, payload) => {
  const response = await api.put(`/interaction/${id}`, payload);
  return response.data;
};

export default api;
