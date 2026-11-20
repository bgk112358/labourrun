<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getChallenge, updateChallenge } from '../api/admin'
import type { ChallengeRule } from '../api/types'

const loading = ref(false)
const saving = ref(false)
const dirty = ref(false)

const form = reactive({
  title: '',
  startDate: '',
  endDate: '' as string | null,
  targetSteps: 12000,
  depositCoupons: '0.00',
  participantCount: 0,
  rules: [] as ChallengeRule[],
  status: 'upcoming',
})

function markDirty() {
  dirty.value = true
}

function addRule() {
  form.rules.push({ title: '', content: '' })
  markDirty()
}

function removeRule(index: number) {
  if (form.rules.length <= 1) {
    ElMessage.warning('至少保留一条挑战规则')
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
    const data = await getChallenge()
    form.title = data.title
    form.startDate = data.startDate
    form.endDate = data.endDate || ''
    form.targetSteps = data.targetSteps
    form.depositCoupons = data.depositCoupons
    form.participantCount = data.participantCount
    form.rules = data.rules.map((rule) => ({
      title: rule.title,
      content: rule.content,
    }))
    form.status = data.status
    dirty.value = false
  } catch (error: any) {
    ElMessage.error(error?.message || '加载挑战配置失败')
  } finally {
    loading.value = false
  }
}

function validate() {
  if (form.title.trim().length < 2) {
    ElMessage.warning('挑战名称至少 2 个字符')
    return false
  }
  if (!form.startDate) {
    ElMessage.warning('请选择挑战开始日期')
    return false
  }
  if (form.endDate && form.startDate > form.endDate) {
    ElMessage.warning('开始日期不能晚于结束日期')
    return false
  }
  if (!Number.isInteger(form.targetSteps) || form.targetSteps < 1) {
    ElMessage.warning('目标步数必须是正整数')
    return false
  }
  if (!/^\d+(\.\d{1,2})?$/.test(form.depositCoupons)) {
    ElMessage.warning('保证金最多保留 2 位小数')
    return false
  }
  if (
    !Number.isInteger(form.participantCount) ||
    form.participantCount < 0
  ) {
    ElMessage.warning('参与人数必须是非负整数')
    return false
  }
  if (form.rules.length < 1 || form.rules.length > 20) {
    ElMessage.warning('挑战规则需要 1–20 条')
    return false
  }
  for (const rule of form.rules) {
    if (!rule.title.trim() || !rule.content.trim()) {
      ElMessage.warning('每条挑战规则都需要标题和内容')
      return false
    }
  }
  return true
}

async function save() {
  if (!validate()) return
  saving.value = true
  try {
    const data = await updateChallenge({
      title: form.title.trim(),
      startDate: form.startDate,
      endDate: form.endDate || null,
      targetSteps: form.targetSteps,
      depositCoupons: form.depositCoupons,
      participantCount: form.participantCount,
      rules: form.rules.map((rule) => ({
        title: rule.title.trim(),
        content: rule.content.trim(),
      })),
      status: form.status,
    })
    form.title = data.title
    form.startDate = data.startDate
    form.endDate = data.endDate || ''
    form.targetSteps = data.targetSteps
    form.depositCoupons = data.depositCoupons
    form.participantCount = data.participantCount
    form.rules = data.rules.map((rule) => ({
      title: rule.title,
      content: rule.content,
    }))
    form.status = data.status
    dirty.value = false
    ElMessage.success('挑战配置已发布')
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
        <h2>挑战管理</h2>
        <p>编辑步数挑战的目标、保证金和详细规则，保存后立即生效。</p>
      </div>
      <el-button @click="load">刷新</el-button>
    </div>

    <el-row :gutter="20">
      <el-col :span="14">
        <el-card>
          <el-form label-width="110px">
            <el-form-item label="挑战名称">
              <el-input
                v-model="form.title"
                maxlength="50"
                show-word-limit
                @input="markDirty"
              />
            </el-form-item>

            <el-form-item label="挑战时间">
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

            <el-form-item label="目标步数">
              <el-input-number
                v-model="form.targetSteps"
                :min="1"
                :max="100000"
                :step="1000"
                @change="markDirty"
              />
            </el-form-item>

            <el-form-item label="保证金">
              <el-input
                v-model="form.depositCoupons"
                placeholder="0.00"
                style="width: 180px"
                @input="markDirty"
              >
                <template #append>兑换券</template>
              </el-input>
            </el-form-item>

            <el-form-item label="参与人数">
              <el-input-number
                v-model="form.participantCount"
                :min="0"
                :step="1"
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

            <el-form-item label="详细规则">
              <div class="rules-editor">
                <div
                  v-for="(rule, index) in form.rules"
                  :key="index"
                  class="rule-row challenge-rule"
                >
                  <el-input
                    v-model="rule.title"
                    placeholder="规则标题"
                    maxlength="50"
                    @input="markDirty"
                  />
                  <el-input
                    v-model="rule.content"
                    type="textarea"
                    :rows="2"
                    maxlength="1000"
                    placeholder="规则内容"
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
          <div class="challenge-preview">
            <div class="challenge-title">
              {{ form.title || '步数挑战' }}
            </div>
            <div class="challenge-line">
              {{ form.startDate || '开始日期' }}开始
            </div>
            <div class="challenge-line">
              目标步数
              <strong>{{ form.targetSteps }}</strong>
              步
            </div>
            <div class="challenge-line">
              挑战保证金 {{ form.depositCoupons }} 兑换券
            </div>
            <div class="challenge-line">
              已有 {{ form.participantCount }} 人参加
            </div>
          </div>
          <div class="preview-rules">
            <div
              v-for="(rule, index) in form.rules"
              :key="index"
              class="preview-rule"
            >
              <span class="preview-no">{{ index + 1 }}</span>
              <span>
                <strong>{{ rule.title || '规则标题' }}</strong>
                <br />
                {{ rule.content || '规则内容' }}
              </span>
            </div>
          </div>
          <p class="muted" style="margin-top: 12px">
            保存后，小程序下次打开步数宝或“更多”页即可看到新内容。
          </p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
