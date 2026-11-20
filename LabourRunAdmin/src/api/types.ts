export interface AdminInfo {
  id: string
  username: string
  displayName: string
  role: 'super_admin' | 'operator'
}

export interface LoginResponse {
  token: string
  expiresIn: number
  admin: AdminInfo
}

export interface Rule {
  no: string
  text: string
}

export interface Activity {
  id: string
  name: string
  noticeText: string
  rules: Rule[]
  startDate: string | null
  endDate: string | null
  status: string
  imageUrl: string | null
  updatedAt: string
  updatedBy: string | null
}

export interface ActivityImage {
  imageUrl: string
  width: number
  height: number
  bytes: number
}

export interface ChallengeRule {
  title: string
  content: string
}

export interface Challenge {
  id: string
  title: string
  startDate: string
  endDate: string | null
  targetSteps: number
  depositCoupons: string
  participantCount: number
  rules: ChallengeRule[]
  status: string
  updatedAt: string
  updatedBy: string | null
}

export interface RegistrationItem {
  id: string
  realName: string
  phoneMasked: string
  company: string
  status: string
  createdAt: string
  updatedAt: string
  cancelledAt: string | null
}

export interface RegistrationDetail extends RegistrationItem {
  phone: string | null
}

export interface PageResult<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
}

export interface AuditLogItem {
  id: string
  adminId: string | null
  adminUsername: string
  action: string
  resourceType: string
  resourceId: string | null
  ip: string | null
  createdAt: string
}

export interface AuditLogDetail extends AuditLogItem {
  before: any
  after: any
  userAgent: string | null
}

export interface DashboardActivity {
  id: string
  name: string
  status: string
  noticeText: string | null
  updatedAt: string
}

export interface DashboardChallenge {
  id: string
  title: string
  status: string
  targetSteps: number
  participantCount: number
  updatedAt: string
}

export interface DashboardData {
  activity: DashboardActivity | null
  challenge: DashboardChallenge | null
  registrationCount: number
  todayRegistrationCount: number
  recentAuditLogs: AuditLogItem[]
}
