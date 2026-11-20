<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  exportRegistrations,
  getRegistration,
  getRegistrations,
} from '../api/admin'
import type {
  RegistrationDetail,
  RegistrationItem,
} from '../api/types'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const loading = ref(false)
const list = ref<RegistrationItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filters = reactive({ keyword: '', status: '' })

const drawerVisible = ref(false)
const detailLoading = ref(false)
const detail = ref<RegistrationDetail | null>(null)

function formatTime(value?: string | null) {
  if (!value) return '—'
  return new Date(value).toLocaleString('zh-CN')
}

function statusLabel(status: string) {
  return status === 'registered' ? '已报名' : '已取消'
}

function statusType(status: string) {
  return status === 'registered' ? 'success' : 'info'
}

async function load() {
  loading.value = true
  try {
    const data = await getRegistrations({
      page: page.value,
      pageSize: pageSize.value,
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
    })
    list.value = data.list
    total.value = data.total
  } catch (error: any) {
    ElMessage.error(error?.message || '加载报名列表失败')
  } finally {
    loading.value = false
  }
}

function search() {
  page.value = 1
  load()
}

function reset() {
  filters.keyword = ''
  filters.status = ''
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

async function openDetail(row: RegistrationItem) {
  drawerVisible.value = true
  detailLoading.value = true
  detail.value = null
  try {
    detail.value = await getRegistration(row.id)
  } catch (error: any) {
    ElMessage.error(error?.message || '加载报名详情失败')
  } finally {
    detailLoading.value = false
  }
}

async function exportCsv() {
  try {
    const response = await exportRegistrations({
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
    })
    const blob = new Blob([response.data], {
      type: 'text/csv;charset=utf-8;',
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'registrations.csv'
    link.click()
    URL.revokeObjectURL(url)
  } catch (error: any) {
    ElMessage.error(error?.message || '导出失败')
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <h2>报名管理</h2>
        <p>查看报名记录；手机号默认脱敏，超级管理员可导出完整数据。</p>
      </div>
      <el-button
        v-if="auth.isSuperAdmin"
        type="primary"
        plain
        @click="exportCsv"
      >
        导出 CSV
      </el-button>
    </div>

    <el-card>
      <div class="toolbar">
        <el-input
          v-model="filters.keyword"
          placeholder="姓名 / 手机号 / 工作单位"
          clearable
          style="width: 260px"
          @keyup.enter="search"
        />
        <el-select
          v-model="filters.status"
          placeholder="全部状态"
          clearable
          style="width: 150px"
        >
          <el-option label="已报名" value="registered" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </div>

      <el-table
        v-loading="loading"
        :data="list"
        size="small"
        @row-click="openDetail"
      >
        <el-table-column prop="realName" label="姓名" width="120" />
        <el-table-column prop="phoneMasked" label="手机号" width="150" />
        <el-table-column prop="company" label="工作单位" min-width="180" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="statusType(row.status)">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="报名时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.updatedAt) }}
          </template>
        </el-table-column>
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
      title="报名详情"
      size="420px"
    >
      <div v-loading="detailLoading">
        <template v-if="detail">
          <div class="detail-row">
            <span class="detail-label">姓名</span>
            <span>{{ detail.realName }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">手机号</span>
            <span>{{ detail.phone || detail.phoneMasked }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">工作单位</span>
            <span>{{ detail.company }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">状态</span>
            <el-tag size="small" :type="statusType(detail.status)">
              {{ statusLabel(detail.status) }}
            </el-tag>
          </div>
          <div class="detail-row">
            <span class="detail-label">报名时间</span>
            <span>{{ formatTime(detail.createdAt) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">更新时间</span>
            <span>{{ formatTime(detail.updatedAt) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">取消时间</span>
            <span>{{ formatTime(detail.cancelledAt) }}</span>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>
