import type { AxiosResponse } from 'axios'
import client from './client'
import type {
  Activity,
  AdminInfo,
  AuditLogDetail,
  AuditLogItem,
  Challenge,
  DashboardData,
  LoginResponse,
  PageResult,
  RegistrationDetail,
  RegistrationItem,
} from './types'

export function login(
  username: string,
  password: string,
): Promise<LoginResponse> {
  return client.post('/auth/login', { username, password }) as any
}

export function me(): Promise<AdminInfo> {
  return client.get('/auth/me') as any
}

export function logout(): Promise<null> {
  return client.post('/auth/logout') as any
}

export function getDashboard(): Promise<DashboardData> {
  return client.get('/dashboard') as any
}

export function getActivity(): Promise<Activity> {
  return client.get('/activity') as any
}

export function updateActivity(payload: any): Promise<Activity> {
  return client.put('/activity', payload) as any
}

export function getChallenge(): Promise<Challenge> {
  return client.get('/challenge') as any
}

export function updateChallenge(payload: any): Promise<Challenge> {
  return client.put('/challenge', payload) as any
}

export function getRegistrations(
  params: Record<string, any>,
): Promise<PageResult<RegistrationItem>> {
  return client.get('/registrations', { params }) as any
}

export function getRegistration(
  id: string,
): Promise<RegistrationDetail> {
  return client.get(`/registrations/${id}`) as any
}

export function exportRegistrations(
  params: Record<string, any>,
): Promise<AxiosResponse<Blob>> {
  return client.get('/registrations/export', {
    params,
    responseType: 'blob',
  }) as any
}

export function getAuditLogs(
  params: Record<string, any>,
): Promise<PageResult<AuditLogItem>> {
  return client.get('/audit-logs', { params }) as any
}

export function getAuditLog(id: string): Promise<AuditLogDetail> {
  return client.get(`/audit-logs/${id}`) as any
}
