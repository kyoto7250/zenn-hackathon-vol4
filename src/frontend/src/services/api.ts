import axios from 'axios';
import type { ChatResponse, Scenario, Session } from '../types';

const api = axios.create({
    baseURL: '/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

export const createSession = async (title?: string) => {
    const response = await api.post<Session>('/sessions/', { title });
    return response.data;
};

export const sendMessage = async (sessionId: string, content: string) => {
    const response = await api.post<ChatResponse>(`/sessions/${sessionId}/messages`, { content });
    return response.data;
};

export const getScenario = async (id: string) => {
    const response = await api.get<Scenario>(`/scenarios/${id}`);
    return response.data;
};

export const addEvent = async (id: string, event: any) => {
    const response = await api.post(`/scenarios/${id}/events`, event);
    return response.data;
};

export const deletePod = async (name: string, namespace: string = 'default') => {
    const response = await api.delete(`/k8s/pods/${namespace}/${name}`);
    return response.data;
};

export const retryScenarioDiagram = async (
    id: string,
    payload: { mermaid?: string; instruction: string; render_error?: string }
) => {
    const response = await api.post<Scenario>(`/scenarios/${id}/diagram/retry`, payload);
    return response.data;
};
