<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { logout } from '../api/admin'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const displayName = computed(
  () => auth.admin?.displayName || auth.admin?.username || '管理员',
)
const roleLabel = computed(() =>
  auth.admin?.role === 'super_admin' ? '超级管理员' : '运营',
)

async function handleLogout() {
  try {
    await logout()
  } catch {
    // token 失效时也允许前端退出
  }
  auth.clear()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<template>
  <el-container class="admin-shell">
    <el-aside width="220px" class="admin-aside">
      <div class="brand">
        LabourRun
        <small>管理后台</small>
      </div>
      <el-menu
        :default-active="route.path"
        router
        class="admin-menu"
        background-color="#1f2d3d"
        text-color="#c0cbd8"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/">概览</el-menu-item>
        <el-menu-item index="/activity">活动管理</el-menu-item>
        <el-menu-item index="/challenge">挑战管理</el-menu-item>
        <el-menu-item index="/registrations">报名管理</el-menu-item>
        <el-menu-item index="/audit-logs">审计日志</el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="admin-header">
        <div class="header-title">
          {{ route.meta.title || '管理后台' }}
        </div>
        <div class="header-user">
          <span>{{ displayName }}</span>
          <el-tag size="small" type="info">{{ roleLabel }}</el-tag>
          <el-button link type="danger" @click="handleLogout">
            退出
          </el-button>
        </div>
      </el-header>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>
