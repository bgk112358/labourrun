import type { AxiosResponse } from 'axios'
import client from './client'
import type {
  Activity,
  ActivityImage,
  AdminInfo,
  AuditLogDetail,
  AuditLogItem,
  Challenge,
  DashboardData,
  LoginResponse,
  PageResult,
  RegistrationDetail,
  RegistrationItem,
  RewardAdmin,
  RewardImage,
  RewardLookup,
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

export function uploadActivityImage(file: File): Promise<ActivityImage> {
  return client.post('/activity/image', file, {
    headers: { 'Content-Type': file.type || 'application/octet-stream' },
  }) as any
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

export function getRewards(): Promise<{ list: RewardAdmin[] }> {
  return client.get('/rewards') as any
}

export function updateReward(
  id: string,
  payload: any,
): Promise<RewardAdmin> {
  return client.patch(`/rewards/${id}`, payload) as any
}

export function uploadRewardImage(file: File): Promise<RewardImage> {
  return client.post('/rewards/image', file, {
    headers: { 'Content-Type': file.type || 'application/octet-stream' },
  }) as any
}

export function getRewardRedemption(code: string): Promise<RewardLookup> {
  return client.get(`/redemptions/${encodeURIComponent(code)}`) as any
}
