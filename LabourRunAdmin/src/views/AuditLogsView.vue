<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getAuditLog, getAuditLogs } from '../api/admin'
import type { AuditLogDetail, AuditLogItem } from '../api/types'

const loading = ref(false)
const list = ref<AuditLogItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filters = reactive({
  adminId: '',
  resourceType: '',
  from: '',
  to: '',
})

const drawerVisible = ref(false)
const detailLoading = ref(false)
const detail = ref<AuditLogDetail | null>(null)

function formatTime(value?: string | null) {
  if (!value) return '—'
  return new Date(value).toLocaleString('zh-CN')
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

function resourceLabel(value: string) {
  return (
    {
      activity: '活动',
      challenge: '挑战',
      auth: '认证',
    }[value] || value
  )
}

function pretty(value: any) {
  if (!value) return '—'
  return JSON.stringify(value, null, 2)
}

async function load() {
  loading.value = true
  try {
    const data = await getAuditLogs({
      page: page.value,
      pageSize: pageSize.value,
      adminId: filters.adminId || undefined,
      resourceType: filters.resourceType || undefined,
      from: filters.from || undefined,
      to: filters.to || undefined,
    })
    list.value = data.list
    total.value = data.total
  } catch (error: any) {
    ElMessage.error(error?.message || '加载审计日志失败')
  } finally {
    loading.value = false
  }
}

function search() {
  page.value = 1
  load()
}

function reset() {
  filters.adminId = ''
  filters.resourceType = ''
  filters.from = ''
  filters.to = ''
  page.value = 1
  load()
}

function handlePageChange(value: number) {
  page.value = value
  load()
}

function handleSizeChange(value: number) {
  pageSize.value = value
  page.value = 1
  load()
}

async function openDetail(row: AuditLogItem) {
  drawerVisible.value = true
  detailLoading.value = true
  detail.value = null
  try {
    detail.value = await getAuditLog(row.id)
  } catch (error: any) {
    ElMessage.error(error?.message || '加载审计详情失败')
  } finally {
    detailLoading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <h2>审计日志</h2>
        <p>查看管理员登录、活动与挑战修改记录。</p>
      </div>
      <el-button @click="load">刷新</el-button>
    </div>

    <el-card>
      <div class="toolbar">
        <el-input
          v-model="filters.adminId"
          placeholder="管理员 ID"
          clearable
          style="width: 210px"
        />
        <el-select
          v-model="filters.resourceType"
          placeholder="全部资源"
          clearable
          style="width: 140px"
        >
          <el-option label="活动" value="activity" />
          <el-option label="挑战" value="challenge" />
          <el-option label="认证" value="auth" />
        </el-select>
        <el-date-picker
          v-model="filters.from"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="开始日期"
          style="width: 150px"
        />
        <el-date-picker
          v-model="filters.to"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="结束日期"
          style="width: 150px"
        />
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </div>

      <el-table
        v-loading="loading"
        :data="list"
        size="small"
        @row-click="openDetail"
      >
        <el-table-column label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column prop="adminUsername" label="管理员" width="130" />
        <el-table-column label="操作" width="110">
          <template #default="{ row }">
            {{ actionLabel(row.action) }}
          </template>
        </el-table-column>
        <el-table-column label="资源" width="100">
          <template #default="{ row }">
            {{ resourceLabel(row.resourceType) }}
          </template>
        </el-table-column>
        <el-table-column prop="resourceId" label="资源 ID" min-width="180" />
        <el-table-column prop="ip" label="IP" width="150" />
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="openDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          :current-page="page"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <el-drawer
      v-model="drawerVisible"
      title="审计详情"
      size="560px"
    >
      <div v-loading="detailLoading">
        <template v-if="detail">
          <div class="detail-row">
            <span class="detail-label">管理员</span>
            <span>{{ detail.adminUsername }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">操作</span>
            <span>{{ actionLabel(detail.action) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">资源</span>
            <span>
              {{ resourceLabel(detail.resourceType) }}
              / {{ detail.resourceId || '—' }}
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">IP</span>
            <span>{{ detail.ip || '—' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">时间</span>
            <span>{{ formatTime(detail.createdAt) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">User-Agent</span>
            <span class="muted">{{ detail.userAgent || '—' }}</span>
          </div>

          <h3 class="drawer-section">修改前</h3>
          <pre class="json-block">{{ pretty(detail.before) }}</pre>
          <h3 class="drawer-section">修改后</h3>
          <pre class="json-block">{{ pretty(detail.after) }}</pre>
        </template>
      </div>
    </el-drawer>
  </div>
</template>
