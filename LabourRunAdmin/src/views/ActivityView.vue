<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getActivity, updateActivity } from '../api/admin'
import type { Rule } from '../api/types'

const loading = ref(false)
const saving = ref(false)
const dirty = ref(false)

const form = reactive({
  name: '',
  noticeText: '',
  rules: [] as Rule[],
  startDate: '' as string | null,
  endDate: '' as string | null,
  status: 'ongoing',
})

function markDirty() {
  dirty.value = true
}

function addRule() {
  form.rules.push({
    no: String(form.rules.length + 1).padStart(2, '0'),
    text: '',
  })
  markDirty()
}

function removeRule(index: number) {
  if (form.rules.length <= 1) {
    ElMessage.warning('至少保留一条活动规则')
    return
  }
  form.rules.splice(index, 1)
  markDirty()
}

function moveRule(index: number, delta: number) {
  const target = index + delta
  if (target < 0 || target >= form.rules.length) return
  const [item] = form.rules.splice(index, 1)
  form.rules.splice(target, 0, item)
  markDirty()
}

async function load() {
  loading.value = true
  try {
    const data = await getActivity()
    form.name = data.name
    form.noticeText = data.noticeText
    form.rules = data.rules.map((rule) => ({
      no: rule.no,
      text: rule.text,
    }))
    form.startDate = data.startDate || ''
    form.endDate = data.endDate || ''
    form.status = data.status
    dirty.value = false
  } catch (error: any) {
    ElMessage.error(error?.message || '加载活动配置失败')
  } finally {
    loading.value = false
  }
}

function validate() {
  if (form.name.trim().length < 2) {
    ElMessage.warning('活动名称至少 2 个字符')
    return false
  }
  if (!form.noticeText.trim()) {
    ElMessage.warning('请填写公告文案')
    return false
  }
  if (form.rules.length < 1 || form.rules.length > 20) {
    ElMessage.warning('活动规则需要 1–20 条')
    return false
  }
  const seen = new Set<string>()
  for (const rule of form.rules) {
    const no = rule.no.trim()
    if (!no || !rule.text.trim()) {
      ElMessage.warning('每条规则都需要编号和内容')
      return false
    }
    if (seen.has(no)) {
      ElMessage.warning(`规则编号 ${no} 重复`)
      return false
    }
    seen.add(no)
  }
  if (form.startDate && form.endDate && form.startDate > form.endDate) {
    ElMessage.warning('开始日期不能晚于结束日期')
    return false
  }
  return true
}

async function save() {
  if (!validate()) return
  saving.value = true
  try {
    const data = await updateActivity({
      name: form.name.trim(),
      noticeText: form.noticeText.trim(),
      rules: form.rules.map((rule) => ({
        no: rule.no.trim(),
        text: rule.text.trim(),
      })),
      startDate: form.startDate || null,
      endDate: form.endDate || null,
      status: form.status,
    })
    form.name = data.name
    form.noticeText = data.noticeText
    form.rules = data.rules.map((rule) => ({
      no: rule.no,
      text: rule.text,
    }))
    form.startDate = data.startDate || ''
    form.endDate = data.endDate || ''
    form.status = data.status
    dirty.value = false
    ElMessage.success('活动配置已发布')
  } catch (error: any) {
    ElMessage.error(error?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

onBeforeRouteLeave(async () => {
  if (!dirty.value) return true
  try {
    await ElMessageBox.confirm(
      '有未保存的修改，确定离开吗？',
      '提示',
      { type: 'warning' },
    )
    return true
  } catch {
    return false
  }
})

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <div class="page-head">
      <div>
        <h2>活动管理</h2>
        <p>编辑首页公告、活动规则和活动时间，保存后立即生效。</p>
      </div>
      <el-button @click="load">刷新</el-button>
    </div>

    <el-row :gutter="20">
      <el-col :span="14">
        <el-card>
          <el-form label-width="100px">
            <el-form-item label="活动名称">
              <el-input
                v-model="form.name"
                maxlength="50"
                show-word-limit
                @input="markDirty"
              />
            </el-form-item>

            <el-form-item label="公告文案">
              <el-input
                v-model="form.noticeText"
                type="textarea"
                :rows="3"
                maxlength="200"
                show-word-limit
                @input="markDirty"
              />
            </el-form-item>

            <el-form-item label="活动时间">
              <el-date-picker
                v-model="form.startDate"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="开始日期"
                @change="markDirty"
              />
              <span class="date-sep">至</span>
              <el-date-picker
                v-model="form.endDate"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="结束日期"
                @change="markDirty"
              />
            </el-form-item>

            <el-form-item label="状态">
              <el-select v-model="form.status" @change="markDirty">
                <el-option label="未开始" value="upcoming" />
                <el-option label="进行中" value="ongoing" />
                <el-option label="已结束" value="ended" />
              </el-select>
            </el-form-item>

            <el-form-item label="活动规则">
              <div class="rules-editor">
                <div
                  v-for="(rule, index) in form.rules"
                  :key="index"
                  class="rule-row"
                >
                  <el-input
                    v-model="rule.no"
                    class="rule-no"
                    maxlength="8"
                    @input="markDirty"
                  />
                  <el-input
                    v-model="rule.text"
                    type="textarea"
                    :rows="2"
                    maxlength="500"
                    @input="markDirty"
                  />
                  <div class="rule-actions">
                    <el-button
                      link
                      :disabled="index === 0"
                      @click="moveRule(index, -1)"
                    >
                      上移
                    </el-button>
                    <el-button
                      link
                      :disabled="index === form.rules.length - 1"
                      @click="moveRule(index, 1)"
                    >
                      下移
                    </el-button>
                    <el-button
                      link
                      type="danger"
                      @click="removeRule(index)"
                    >
                      删除
                    </el-button>
                  </div>
                </div>
                <el-button type="primary" plain @click="addRule">
                  新增规则
                </el-button>
              </div>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="saving"
                @click="save"
              >
                保存并发布
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card class="preview-card">
          <template #header>小程序效果预览</template>
          <div class="preview-notice">
            <span>★</span>
            {{ form.noticeText || '公告文案' }}
          </div>
          <div class="preview-rules">
            <div
              v-for="(rule, index) in form.rules"
              :key="index"
              class="preview-rule"
            >
              <span class="preview-no">{{ rule.no || '01' }}</span>
              <span>{{ rule.text || '规则内容' }}</span>
            </div>
          </div>
          <p class="muted" style="margin-top: 12px">
            保存后，小程序下次打开首页即可看到新内容。
          </p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
