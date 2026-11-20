import { createRouter, createWebHistory } from 'vue-router'

const AdminLayout = () => import('./layouts/AdminLayout.vue')
const LoginView = () => import('./views/LoginView.vue')
const DashboardView = () => import('./views/DashboardView.vue')
const ActivityView = () => import('./views/ActivityView.vue')
const ChallengeView = () => import('./views/ChallengeView.vue')
const RegistrationsView = () => import('./views/RegistrationsView.vue')
const AuditLogsView = () => import('./views/AuditLogsView.vue')

const router = createRouter({
  history: createWebHistory('/admin/'),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { title: '登录' },
    },
    {
      path: '/',
      component: AdminLayout,
      children: [
        {
          path: '',
          name: 'dashboard',
          component: DashboardView,
          meta: { title: '概览' },
        },
        {
          path: 'activity',
          name: 'activity',
          component: ActivityView,
          meta: { title: '活动管理' },
        },
        {
          path: 'challenge',
          name: 'challenge',
          component: ChallengeView,
          meta: { title: '挑战管理' },
        },
        {
          path: 'registrations',
          name: 'registrations',
          component: RegistrationsView,
          meta: { title: '报名管理' },
        },
        {
          path: 'audit-logs',
          name: 'audit-logs',
          component: AuditLogsView,
          meta: { title: '审计日志' },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.beforeEach((to) => {
  const token = sessionStorage.getItem('admin_token')
  if (to.path !== '/login' && !token) {
    return '/login'
  }
  if (to.path === '/login' && token) {
    return '/'
  }
  return true
})

export default router
