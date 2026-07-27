import axios from "axios";

const apiClient = axios.create({
  baseURL: "http://localhost:8000/api/",
  headers: {
    "Content-Type": "application/json",
  },
});

export default {
  getUsers() {
    return apiClient.get("users/");
  },
  getApplications() {
    return apiClient.get("applications/");
  },
  getApplication(id) {
    return apiClient.get(`applications/${id}/`);
  },
  createApplication(data) {
    return apiClient.post("applications/", data);
  },
  updateApplication(id, data) {
    return apiClient.put(`applications/${id}/`, data);
  },
  deleteApplication(id) {
    return apiClient.delete(`applications/${id}/`);
  },
  getConfigurations(appId) {
    return apiClient.get(`applications/${appId}/configurations/`);
  },
  getConfiguration(appId, id) {
    return apiClient.get(`applications/${appId}/configurations/${id}/`);
  },
  createConfiguration(appId, data) {
    return apiClient.post(`applications/${appId}/configurations/`, data);
  },
  updateConfiguration(appId, id, data) {
    return apiClient.put(`applications/${appId}/configurations/${id}/`, data);
  },
  deleteConfiguration(appId, id) {
    return apiClient.delete(`applications/${appId}/configurations/${id}/`);
  },
};
