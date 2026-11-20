<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '../api/admin'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const form = reactive({ username: '', password: '' })
const loading = ref(false)

async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const data = await login(form.username, form.password)
    auth.setAuth(data)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error: any) {
    ElMessage.error(error?.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-brand">
        <h1>LabourRun 管理后台</h1>
        <p>活动须知、挑战配置与报名管理</p>
      </div>
      <el-card shadow="always">
        <div @keyup.enter="submit">
          <el-form label-position="top">
            <el-form-item label="用户名">
              <el-input
                v-model="form.username"
                placeholder="请输入管理员用户名"
                autocomplete="username"
              />
            </el-form-item>
            <el-form-item label="密码">
              <el-input
                v-model="form.password"
                type="password"
                show-password
                placeholder="请输入密码"
                autocomplete="current-password"
              />
            </el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              style="width: 100%"
              @click="submit"
            >
              登录
            </el-button>
          </el-form>
        </div>
        <p class="login-tip">
          管理员账号由后端 CLI 创建，忘记密码请联系超级管理员。
        </p>
      </el-card>
    </div>
  </div>
</template>
