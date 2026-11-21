<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getRewards,
  updateReward,
  uploadRewardImage,
} from '../api/admin'
import type { RewardAdmin } from '../api/types'

const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const rewards = ref<RewardAdmin[]>([])
const dialogVisible = ref(false)
const editingId = ref('')

const form = reactive({
  name: '',
  couponCost: '',
  imageUrl: '',
  sortOrder: 0,
  active: true,
})

async function load() {
  loading.value = true
  try {
    const data = await getRewards()
    rewards.value = data.list || []
  } catch (error: any) {
    ElMessage.error(error?.message || '加载奖励配置失败')
  } finally {
    loading.value = false
  }
}

function openEdit(row: RewardAdmin) {
  editingId.value = row.id
  form.name = row.name
  form.couponCost = row.couponCost
  form.imageUrl = row.imageUrl || ''
  form.sortOrder = row.sortOrder
  form.active = row.active
  dialogVisible.value = true
}

function closeDialog() {
  if (saving.value || uploading.value) return
  dialogVisible.value = false
}

async function uploadImage(options: any) {
  const file = options.file as File
  if (!file) return
  if (file.size > 10 * 1024 * 1024) {
    const error = new Error('图片不能超过 10MB')
    ElMessage.warning(error.message)
    if (options.onError) options.onError(error)
    return
  }

  uploading.value = true
  try {
    const data = await uploadRewardImage(file)
    form.imageUrl = data.imageUrl
    ElMessage.success('图片已上传，保存后生效')
    if (options.onSuccess) options.onSuccess(data)
  } catch (error: any) {
    ElMessage.error(error?.message || '图片上传失败')
    if (options.onError) options.onError(error)
  } finally {
    uploading.value = false
  }
}

function removeImage() {
  form.imageUrl = ''
}

function validate() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写奖励名称')
    return false
  }
  if (!/^\d+(\.\d{1,2})?$/.test(form.couponCost.trim())) {
    ElMessage.warning('所需兑换券最多保留 2 位小数')
    return false
  }
  if (Number(form.couponCost) <= 0) {
    ElMessage.warning('所需兑换券必须大于 0')
    return false
  }
  if (form.sortOrder < 0) {
    ElMessage.warning('排序不能小于 0')
    return false
  }
  return true
}

async function save() {
  if (!validate()) return
  saving.value = true
  try {
    await updateReward(editingId.value, {
      name: form.name.trim(),
      couponCost: form.couponCost.trim(),
      imageUrl: form.imageUrl || null,
      sortOrder: Number(form.sortOrder) || 0,
      active: form.active,
    })
    ElMessage.success('奖励配置已保存')
    dialogVisible.value = false
    await load()
  } catch (error: any) {
    ElMessage.error(error?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <div class="page-head">
      <div>
        <h2>奖励管理</h2>
        <p>
          配置首页三档奖品的名称、所需兑换券和方形展示图；排序越小越靠前。
        </p>
      </div>
      <el-button @click="load">刷新</el-button>
    </div>

    <el-card>
      <el-table :data="rewards" row-key="id">
        <el-table-column label="展示图" width="110">
          <template #default="{ row }">
            <el-image
              v-if="row.imageUrl"
              :src="row.imageUrl"
              fit="cover"
              class="reward-admin-image"
            />
            <div v-else class="reward-admin-placeholder">奖</div>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="奖励名称" min-width="160" />
        <el-table-column label="所需兑换券" width="130">
          <template #default="{ row }">
            {{ row.couponCost }}
          </template>
        </el-table-column>
        <el-table-column prop="sortOrder" label="排序" width="90" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.active ? 'success' : 'info'">
              {{ row.active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">
              编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      title="编辑奖励"
      width="520px"
      :close-on-click-modal="false"
      @close="closeDialog"
    >
      <el-form label-width="100px">
        <el-form-item label="奖励名称">
          <el-input v-model="form.name" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="所需兑换券">
          <el-input v-model="form.couponCost" placeholder="例如 1.00" />
        </el-form-item>
        <el-form-item label="展示图">
          <div class="reward-image-field">
            <el-image
              v-if="form.imageUrl"
              :src="form.imageUrl"
              fit="cover"
              class="reward-admin-image"
            />
            <div v-else class="reward-admin-placeholder">奖</div>
            <div class="reward-image-actions">
              <el-upload
                action="#"
                :show-file-list="false"
                accept="image/*"
                :http-request="uploadImage"
              >
                <el-button
                  type="primary"
                  plain
                  :loading="uploading"
                >
                  上传方图
                </el-button>
              </el-upload>
              <el-button
                v-if="form.imageUrl"
                link
                type="danger"
                @click="removeImage"
              >
                移除
              </el-button>
            </div>
          </div>
          <div class="muted">
            任意尺寸自动居中裁剪为 400×400，JPEG 压缩，最大 10MB。
          </div>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sortOrder" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button :disabled="saving || uploading" @click="closeDialog">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="saving"
          :disabled="uploading"
          @click="save"
        >
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.reward-admin-image {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  display: block;
}
.reward-admin-placeholder {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  background: #fff3ee;
  color: #e93b33;
  font-size: 20px;
  font-weight: 700;
  line-height: 56px;
  text-align: center;
}
.reward-image-field {
  display: flex;
  align-items: center;
  gap: 14px;
}
.reward-image-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
