<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getRewardRedemption } from '../api/admin'
import type { RewardLookup } from '../api/types'

const code = ref('')
const loading = ref(false)
const searched = ref(false)
const result = ref<RewardLookup | null>(null)

function formatTime(value: string | null | undefined) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

function statusLabel(status: string) {
  if (status === 'registered') return '已报名'
  if (status === 'cancelled') return '已取消'
  return status
}

function typeLabel(type: string) {
  if (type === 'exchange') return '步数兑换'
  if (type === 'reward') return '奖品兑换'
  if (type === 'challenge_deposit') return '挑战保证金'
  if (type === 'refund') return '退款'
  if (type === 'adjust') return '调整'
  return type
}

async function search() {
  const value = code.value.trim()
  if (!value) {
    ElMessage.warning('请输入兑换码')
    return
  }
  loading.value = true
  searched.value = true
  try {
    result.value = await getRewardRedemption(value)
  } catch (error: any) {
    result.value = null
    ElMessage.error(error?.message || '查询失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <h2>奖励查询</h2>
        <p>
          输入兑换码查看获奖人、奖励名称，以及报名、兑换券和步数明细。
        </p>
      </div>
    </div>

    <el-card class="search-card">
      <div class="search-row">
        <el-input
          v-model="code"
          placeholder="请输入兑换码，例如 LR-ABCDEFGH"
          clearable
          maxlength="32"
          @keyup.enter="search"
        />
        <el-button type="primary" :loading="loading" @click="search">
          查询
        </el-button>
      </div>
      <div class="muted">
        查询不区分大小写和连字符；每次查询会写入管理员审计日志。
      </div>
    </el-card>

    <template v-if="result">
      <el-card class="lookup-card">
        <template #header>兑换信息</template>
        <div class="code-banner">{{ result.redemption.code }}</div>
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">奖励名称</span>
            <span class="detail-value">{{ result.redemption.rewardName }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">扣除兑换券</span>
            <span class="detail-value">{{ result.redemption.couponCost }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">所属活动</span>
            <span class="detail-value">{{ result.redemption.activityName }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">兑换时间</span>
            <span class="detail-value">
              {{ formatTime(result.redemption.createdAt) }}
            </span>
          </div>
        </div>
      </el-card>

      <el-card class="lookup-card">
        <template #header>兑换人（兑换时快照）</template>
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">姓名</span>
            <span class="detail-value">{{ result.redeemer.realName }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">手机号</span>
            <span class="detail-value">
              {{ result.redeemer.phone || result.redeemer.phoneMasked }}
            </span>
          </div>
          <div class="detail-item">
            <span class="detail-label">工作单位</span>
            <span class="detail-value">{{ result.redeemer.company }}</span>
          </div>
        </div>
      </el-card>

      <el-card class="lookup-card">
        <template #header>当前报名状态</template>
        <div v-if="result.registration" class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">姓名</span>
            <span class="detail-value">{{ result.registration.realName }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">手机号</span>
            <span class="detail-value">
              {{
                result.registration.phone ||
                result.registration.phoneMasked
              }}
            </span>
          </div>
          <div class="detail-item">
            <span class="detail-label">工作单位</span>
            <span class="detail-value">{{ result.registration.company }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">状态</span>
            <span class="detail-value">
              <el-tag
                :type="
                  result.registration.status === 'registered'
                    ? 'success'
                    : 'info'
                "
              >
                {{ statusLabel(result.registration.status) }}
              </el-tag>
            </span>
          </div>
          <div class="detail-item">
            <span class="detail-label">报名时间</span>
            <span class="detail-value">
              {{ formatTime(result.registration.createdAt) }}
            </span>
          </div>
          <div class="detail-item">
            <span class="detail-label">更新时间</span>
            <span class="detail-value">
              {{ formatTime(result.registration.updatedAt) }}
            </span>
          </div>
        </div>
        <div v-else class="empty-tip">当前报名记录不存在</div>
      </el-card>

      <el-card class="lookup-card">
        <template #header>用户与兑换券账户</template>
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">用户 ID</span>
            <span class="detail-value">{{ result.user.id }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">昵称</span>
            <span class="detail-value">{{ result.user.nickname || '-' }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">用户创建时间</span>
            <span class="detail-value">
              {{ formatTime(result.user.createdAt) }}
            </span>
          </div>
          <div class="detail-item">
            <span class="detail-label">当前余额</span>
            <span class="detail-value strong">
              {{ result.couponAccount.balance }}
            </span>
          </div>
          <div class="detail-item">
            <span class="detail-label">累计获得</span>
            <span class="detail-value">
              {{ result.couponAccount.totalEarned }}
            </span>
          </div>
          <div class="detail-item">
            <span class="detail-label">累计消耗</span>
            <span class="detail-value">
              {{ result.couponAccount.totalSpent }}
            </span>
          </div>
        </div>
      </el-card>

      <el-card class="lookup-card">
        <template #header>步数明细</template>
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">今日步数</span>
            <span class="detail-value">
              {{ result.stepSummary.todaySteps }}
            </span>
          </div>
          <div class="detail-item">
            <span class="detail-label">今日已兑换步数</span>
            <span class="detail-value">
              {{ result.stepSummary.todayExchangedSteps }}
            </span>
          </div>
          <div class="detail-item">
            <span class="detail-label">今日可兑步数</span>
            <span class="detail-value">
              {{ result.stepSummary.todayConvertibleSteps }}
            </span>
          </div>
          <div class="detail-item">
            <span class="detail-label">累计步数</span>
            <span class="detail-value">
              {{ result.stepSummary.totalSteps }}
            </span>
          </div>
          <div class="detail-item">
            <span class="detail-label">累计已兑换步数</span>
            <span class="detail-value">
              {{ result.stepSummary.totalExchangedSteps }}
            </span>
          </div>
          <div class="detail-item">
            <span class="detail-label">每日上限 / 每券步数</span>
            <span class="detail-value">
              {{ result.stepSummary.dailyCapSteps }} /
              {{ result.stepSummary.stepsPerCoupon }}
            </span>
          </div>
        </div>

        <el-table
          :data="result.dailySteps"
          size="small"
          class="detail-table"
        >
          <el-table-column prop="statDate" label="日期" width="130" />
          <el-table-column prop="steps" label="步数" />
          <el-table-column prop="exchangedSteps" label="已兑换步数" />
        </el-table>
      </el-card>

      <el-card class="lookup-card">
        <template #header>该用户奖品兑换记录</template>
        <el-table :data="result.redemptions" size="small">
          <el-table-column prop="code" label="兑换码" min-width="150" />
          <el-table-column prop="rewardName" label="奖励名称" min-width="140" />
          <el-table-column prop="couponCost" label="扣除兑换券" width="120" />
          <el-table-column label="兑换时间" min-width="170">
            <template #default="{ row }">
              {{ formatTime(row.createdAt) }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card class="lookup-card">
        <template #header>最近兑换券流水</template>
        <el-table :data="result.ledger" size="small">
          <el-table-column label="类型" width="110">
            <template #default="{ row }">
              {{ typeLabel(row.type) }}
            </template>
          </el-table-column>
          <el-table-column label="金额" width="100">
            <template #default="{ row }">
              <span
                :class="Number(row.amount) >= 0 ? 'amount-in' : 'amount-out'"
              >
                {{ Number(row.amount) >= 0 ? '+' : '' }}{{ row.amount }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="balanceAfter" label="余额" width="100" />
          <el-table-column label="时间" min-width="170">
            <template #default="{ row }">
              {{ formatTime(row.createdAt) }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>

    <el-card v-else-if="searched && !loading" class="lookup-card">
      <div class="empty-tip">未查询到兑换记录</div>
    </el-card>
  </div>
</template>

<style scoped>
.search-card {
  margin-bottom: 18px;
}
.search-row {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}
.search-row .el-input {
  max-width: 420px;
}
.lookup-card {
  margin-bottom: 18px;
}
.code-banner {
  margin-bottom: 18px;
  padding: 16px 20px;
  border-radius: 10px;
  background: #fff3ee;
  color: #e93b33;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 2px;
}
.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px 24px;
}
.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.detail-label {
  color: #909399;
  font-size: 12px;
}
.detail-value {
  color: #303133;
  font-size: 14px;
  word-break: break-all;
}
.detail-value.strong {
  color: #e93b33;
  font-size: 18px;
  font-weight: 700;
}
.detail-table {
  margin-top: 18px;
}
.empty-tip {
  padding: 24px 0;
  color: #909399;
  text-align: center;
}
.amount-in {
  color: #e93b33;
}
.amount-out {
  color: #3f8f5f;
}
</style>
