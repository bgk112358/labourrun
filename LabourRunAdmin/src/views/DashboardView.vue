<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getDashboard } from '../api/admin'
import type { DashboardData } from '../api/types'

const loading = ref(false)
const data = ref<DashboardData | null>(null)

function formatTime(value?: string | null) {
  if (!value) return '—'
  return new Date(value).toLocaleString('zh-CN')
}

function statusLabel(status?: string) {
  return (
    {
      upcoming: '未开始',
      ongoing: '进行中',
      ended: '已结束',
    }[status || ''] || status || '—'
  )
}

function actionLabel(action: string) {
  return (
    {
      login: '登录',
      login_failed: '登录失败',
      logout: '退出',
      update_activity: '更新活动',
      update_challenge: '更新挑战',
    }[action] || action
  )
}

async function load() {
  loading.value = true
  try {
    data.value = await getDashboard()
  } catch (error: any) {
    ElMessage.error(error?.message || '加载概览失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <div class="page-head">
      <div>
        <h2>概览</h2>
        <p>当前活动、挑战与报名情况；所有修改会记录审计日志。</p>
      </div>
      <el-button @click="load">刷新</el-button>
    </div>

    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <el-card>
          <div class="stat-label">当前活动</div>
          <div class="stat-value">
            {{ data?.activity?.name || '暂无' }}
          </div>
          <el-tag size="small" type="success">
            {{ statusLabel(data?.activity?.status) }}
          </el-tag>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-label">当前挑战</div>
          <div class="stat-value">
            {{ data?.challenge?.title || '暂无' }}
          </div>
          <el-tag size="small" type="warning">
            {{ statusLabel(data?.challenge?.status) }}
          </el-tag>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-label">报名总数</div>
          <div class="stat-number">
            {{ data?.registrationCount ?? 0 }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-label">今日新增报名</div>
          <div class="stat-number">
            {{ data?.todayRegistrationCount ?? 0 }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card>
          <template #header>当前活动</template>
          <div class="detail-row">
            <span class="detail-label">公告</span>
            <span>{{ data?.activity?.noticeText || '暂无' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">更新时间</span>
            <span>{{ formatTime(data?.activity?.updatedAt) }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>当前挑战</template>
          <div class="detail-row">
            <span class="detail-label">目标步数</span>
            <span>{{ data?.challenge?.targetSteps ?? '—' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">参与人数</span>
            <span>{{ data?.challenge?.participantCount ?? '—' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">更新时间</span>
            <span>{{ formatTime(data?.challenge?.updatedAt) }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 16px">
      <template #header>最近审计日志</template>
      <el-table :data="data?.recentAuditLogs || []" size="small">
        <el-table-column label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column prop="adminUsername" label="管理员" width="120" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            {{ actionLabel(row.action) }}
          </template>
        </el-table-column>
        <el-table-column prop="resourceType" label="资源" width="120" />
        <el-table-column prop="ip" label="IP" width="140" />
      </el-table>
    </el-card>
  </div>
</template>
