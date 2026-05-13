<template>
  <div class="dept-page">
    <div class="page-header">
      <h1 class="page-title">部门管理</h1>
      <button class="btn btn-primary" @click="openAddDept">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/></svg>
        新增部门
      </button>
    </div>

    <div class="dept-layout">
      <!-- 左侧部门列表 -->
      <div class="dept-list-panel">
        <div class="panel-title">部门列表</div>
        <div class="dept-items">
          <div
            v-for="dept in departments" :key="dept.id"
            class="dept-item" :class="{ active: selectedDeptId === dept.id }"
            @click="selectDept(dept)"
          >
            <div class="dept-item-icon">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17,15H7V13H17M17,11H7V9H17M19,3H14.82C14.4,1.84 13.3,1 12,1C10.7,1 9.6,1.84 9.18,3H5A2,2 0 0,0 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5A2,2 0 0,0 19,3M12,3A1,1 0 0,1 13,4A1,1 0 0,1 12,5A1,1 0 0,1 11,4A1,1 0 0,1 12,3M19,19H5V5H19V19Z"/></svg>
            </div>
            <div class="dept-item-info">
              <div class="dept-item-name">{{ dept.name }}</div>
              <div class="dept-item-count">{{ (dept.memberUsernames || []).length }} 人</div>
            </div>
            <div class="dept-item-actions">
              <button class="icon-btn edit" @click.stop="openEditDept(dept)" title="编辑">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"/></svg>
              </button>
              <button class="icon-btn del" @click.stop="deleteDept(dept)" title="删除">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/></svg>
              </button>
            </div>
          </div>
          <div v-if="departments.length === 0" class="empty-tip">暂无部门，点击右上角新增</div>
        </div>
      </div>

      <!-- 右侧详情 -->
      <div class="dept-detail-panel" v-if="selectedDept">
        <div class="detail-header">
          <div>
            <div class="detail-title">{{ selectedDept.name }}</div>
            <div class="detail-desc">{{ selectedDept.description || '暂无描述' }}</div>
          </div>
        </div>

        <!-- 成员管理 -->
        <div class="section">
          <div class="section-header">
            <span class="section-title">成员管理</span>
            <button class="btn btn-sm btn-primary" @click="openAddMember">添加成员</button>
          </div>
          <div class="member-list" v-if="selectedDept.memberUsernames && selectedDept.memberUsernames.length > 0">
            <div class="member-item" v-for="uname in selectedDept.memberUsernames" :key="uname">
              <div class="member-avatar" :style="!getUserAvatarUrl(uname) ? { background: getAvatarColor(uname) } : {}">
                <img v-if="getUserAvatarUrl(uname)" :src="getUserAvatarUrl(uname)" class="avatar-img" />
                <span v-else>{{ uname[0].toUpperCase() }}</span>
              </div>
              <div class="member-name">{{ uname }}</div>
              <button class="icon-btn del" @click="removeMember(uname)" title="移除">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/></svg>
              </button>
            </div>
          </div>
          <div class="empty-tip" v-else>暂无成员，点击「添加成员」</div>
        </div>

        <!-- 关联知识库 -->
        <div class="section">
          <div class="section-header">
            <span class="section-title">关联知识库</span>
            <span class="section-hint">在知识库页面点击「关联部门」进行关联</span>
          </div>
          <div class="kb-tag-list" v-if="deptKBNames.length > 0">
            <span class="kb-tag" v-for="name in deptKBNames" :key="name">📚 {{ name }}</span>
          </div>
          <div class="empty-tip" v-else>暂无关联知识库</div>
        </div>
      </div>

      <!-- 未选中时 -->
      <div class="dept-detail-panel empty-panel" v-else>
        <div class="empty-state">
          <svg viewBox="0 0 24 24" fill="currentColor" class="empty-icon"><path d="M17,15H7V13H17M17,11H7V9H17M19,3H14.82C14.4,1.84 13.3,1 12,1C10.7,1 9.6,1.84 9.18,3H5A2,2 0 0,0 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5A2,2 0 0,0 19,3M12,3A1,1 0 0,1 13,4A1,1 0 0,1 12,5A1,1 0 0,1 11,4A1,1 0 0,1 12,3M19,19H5V5H19V19Z"/></svg>
          <p>请从左侧选择一个部门查看详情</p>
        </div>
      </div>
    </div>

    <!-- 新增/编辑部门弹窗 -->
    <div v-if="showDeptModal" class="modal-overlay" @click.self="showDeptModal = false">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editingDeptId ? '编辑部门' : '新增部门' }}</h2>
          <button class="close-btn" @click="showDeptModal = false">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/></svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>部门名称 <span class="req">*</span></label>
            <input v-model="deptForm.name" type="text" placeholder="请输入部门名称" class="input" @keyup.enter="saveDept" />
          </div>
          <div class="form-group">
            <label>部门描述</label>
            <textarea v-model="deptForm.description" placeholder="可选" class="input textarea" rows="3"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="showDeptModal = false">取消</button>
          <button class="btn btn-primary" @click="saveDept" :disabled="!deptForm.name.trim()">{{ editingDeptId ? '保存' : '创建' }}</button>
        </div>
      </div>
    </div>

    <!-- 添加成员弹窗 -->
    <div v-if="showAddMemberModal" class="modal-overlay" @click.self="showAddMemberModal = false">
      <div class="modal modal-wide">
        <div class="modal-header">
          <h2>添加成员到「{{ selectedDept?.name }}」</h2>
          <button class="close-btn" @click="showAddMemberModal = false">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/></svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <input v-model="memberSearch" type="text" placeholder="搜索用户名..." class="input" />
          </div>
          <div class="user-pick-list">
            <div
              v-for="u in filteredUsers" :key="u.username"
              class="user-pick-item"
              :class="{ selected: pendingMembers.includes(u.username), already: (selectedDept?.memberUsernames||[]).includes(u.username) }"
              @click="togglePendingMember(u.username)"
            >
              <div class="member-avatar sm" :style="!u.avatar_url ? { background: getAvatarColor(u.username) } : {}">
                <img v-if="u.avatar_url" :src="u.avatar_url" class="avatar-img" />
                <span v-else>{{ u.username[0].toUpperCase() }}</span>
              </div>
              <div class="user-pick-info">
                <div class="user-pick-name">{{ u.username }}</div>
                <div class="user-pick-sub">{{ u.department || '无部门' }}</div>
              </div>
              <svg v-if="pendingMembers.includes(u.username)" viewBox="0 0 24 24" fill="currentColor" class="check-icon"><path d="M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z"/></svg>
              <span v-else-if="(selectedDept?.memberUsernames||[]).includes(u.username)" class="already-tag">已在部门</span>
            </div>
            <div v-if="filteredUsers.length === 0" class="empty-tip">无匹配用户</div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="showAddMemberModal = false">取消</button>
          <button class="btn btn-primary" @click="confirmAddMembers" :disabled="pendingMembers.length === 0">
            添加{{ pendingMembers.length > 0 ? ' ' + pendingMembers.length + ' 人' : '' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <transition name="modal-fade">
      <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
        <div class="modal delete-modal">
          <div class="modal-icon-danger">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/></svg>
          </div>
          <h3>确认删除</h3>
          <p>确定要删除部门「<strong>{{ deleteTarget?.name }}</strong>」吗？此操作不可撤销。</p>
          <div class="modal-actions">
            <button class="btn btn-ghost" @click="showDeleteModal = false">取消</button>
            <button class="btn btn-danger" @click="confirmDeleteDept">确认删除</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { adminApi } from '@/api'
import { useToast } from '@/utils/toast'

const { showToast } = useToast()
const STORAGE_KEY = 'rag_departments'

// ── 部门数据 ──────────────────────────────────────────
const departments = ref([])
const selectedDeptId = ref(null)
const selectedDept = computed(() => departments.value.find(d => d.id === selectedDeptId.value) || null)

const loadDepts = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    departments.value = raw ? JSON.parse(raw) : []
  } catch { departments.value = [] }
}

const saveDepts = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(departments.value))
}

const selectDept = (dept) => { selectedDeptId.value = dept.id }

// ── 部门 CRUD ─────────────────────────────────────────
const showDeptModal = ref(false)
const editingDeptId = ref(null)
const deptForm = reactive({ name: '', description: '' })

const openAddDept = () => {
  editingDeptId.value = null
  deptForm.name = ''
  deptForm.description = ''
  showDeptModal.value = true
}

const openEditDept = (dept) => {
  editingDeptId.value = dept.id
  deptForm.name = dept.name
  deptForm.description = dept.description || ''
  showDeptModal.value = true
}

const saveDept = () => {
  if (!deptForm.name.trim()) return
  if (editingDeptId.value) {
    const idx = departments.value.findIndex(d => d.id === editingDeptId.value)
    if (idx !== -1) {
      departments.value[idx].name = deptForm.name.trim()
      departments.value[idx].description = deptForm.description.trim()
    }
  } else {
    const newDept = {
      id: Date.now().toString(),
      name: deptForm.name.trim(),
      description: deptForm.description.trim(),
      memberUsernames: [],
      kbIds: [],
      createdAt: new Date().toISOString()
    }
    departments.value.push(newDept)
    selectedDeptId.value = newDept.id
  }
  saveDepts()
  showDeptModal.value = false
}

const showDeleteModal = ref(false)
const deleteTarget = ref(null)

const deleteDept = (dept) => {
  deleteTarget.value = dept
  showDeleteModal.value = true
}

const confirmDeleteDept = () => {
  const dept = deleteTarget.value
  if (!dept) return
  departments.value = departments.value.filter(d => d.id !== dept.id)
  if (selectedDeptId.value === dept.id) selectedDeptId.value = null
  saveDepts()
  showDeleteModal.value = false
  deleteTarget.value = null
  showToast(`部门「${dept.name}」已删除`, 'success')
}

// ── 成员管理 ──────────────────────────────────────────
const showAddMemberModal = ref(false)
const memberSearch = ref('')
const pendingMembers = ref([])
const allUsers = ref([])

const openAddMember = async () => {
  pendingMembers.value = []
  memberSearch.value = ''
  await loadAllUsers()
  showAddMemberModal.value = true
}

const loadAllUsers = async () => {
  try {
    const res = await adminApi.getUserList({ page: 1, size: 200 })
    allUsers.value = res?.data?.users || res?.data?.items || []
  } catch { allUsers.value = [] }
}

const filteredUsers = computed(() => {
  const q = memberSearch.value.trim().toLowerCase()
  return allUsers.value.filter(u => !q || u.username.toLowerCase().includes(q))
})

const togglePendingMember = (uname) => {
  if ((selectedDept.value?.memberUsernames || []).includes(uname)) return
  const idx = pendingMembers.value.indexOf(uname)
  if (idx === -1) pendingMembers.value.push(uname)
  else pendingMembers.value.splice(idx, 1)
}

const confirmAddMembers = () => {
  const dept = departments.value.find(d => d.id === selectedDeptId.value)
  if (!dept) return
  if (!dept.memberUsernames) dept.memberUsernames = []
  for (const uname of pendingMembers.value) {
    if (!dept.memberUsernames.includes(uname)) dept.memberUsernames.push(uname)
  }
  saveDepts()
  showAddMemberModal.value = false
}

const removeMember = (uname) => {
  const dept = departments.value.find(d => d.id === selectedDeptId.value)
  if (!dept) return
  dept.memberUsernames = (dept.memberUsernames || []).filter(u => u !== uname)
  saveDepts()
}

// ── 头像相关 ──────────────────────────────────────────
const getUserAvatarUrl = (username) => {
  const user = allUsers.value.find(u => u.username === username)
  return user?.avatar_url || ''
}

const getAvatarColor = (username) => {
  const colors = ['#667eea', '#f56565', '#48bb78', '#ed8936', '#9f7aea', '#38b2ac', '#e53e3e', '#3182ce']
  let hash = 0
  for (let i = 0; i < (username || '').length; i++) {
    hash = username.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

// ── 关联知识库展示 ────────────────────────────────────
const deptKBNames = computed(() => {
  if (!selectedDept.value) return []
  const kbIds = selectedDept.value.kbIds || []
  if (kbIds.length === 0) return []
  try {
    const kbMap = JSON.parse(localStorage.getItem('rag_kb_names') || '{}')
    return kbIds.map(id => kbMap[id] || id)
  } catch { return kbIds }
})

onMounted(() => {
  loadDepts()
  // 预加载用户列表，用于显示成员头像
  loadAllUsers()
})
</script>

<style scoped>
.dept-page { padding: 32px; max-width: 1100px; margin: 0 auto; }

.page-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 28px;
}
.page-title { font-size: 28px; font-weight: 700; color: var(--gray-800); }

.btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 10px 20px; border-radius: var(--radius); font-size: 14px;
  font-weight: 500; cursor: pointer; border: none; transition: all 0.2s;
}
.btn svg { width: 18px; height: 18px; }
.btn-primary { background: var(--primary); color: white; }
.btn-primary:hover:not(:disabled) { background: var(--primary-dark, #0d9488); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-ghost { background: var(--gray-100); color: var(--gray-700); }
.btn-ghost:hover { background: var(--gray-200); }
.btn-sm { padding: 6px 14px; font-size: 13px; }

/* 布局 */
.dept-layout { display: flex; gap: 24px; min-height: 500px; }

/* 左侧列表 */
.dept-list-panel {
  width: 260px; flex-shrink: 0;
  background: white; border-radius: var(--radius-xl); box-shadow: var(--shadow);
  overflow: hidden; display: flex; flex-direction: column;
}
.panel-title {
  padding: 16px 20px; font-size: 14px; font-weight: 600;
  color: var(--gray-600); border-bottom: 1px solid var(--gray-100);
}
.dept-items { flex: 1; overflow-y: auto; padding: 8px; }

.dept-item {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 12px; border-radius: var(--radius); cursor: pointer;
  transition: all 0.2s; margin-bottom: 4px;
}
.dept-item:hover { background: rgba(127,205,205,0.1); }
.dept-item.active { background: rgba(127,205,205,0.2); }

.dept-item-icon {
  width: 36px; height: 36px; border-radius: var(--radius-sm);
  background: linear-gradient(135deg, rgba(168,230,207,0.4), rgba(127,205,205,0.4));
  display: flex; align-items: center; justify-content: center;
  color: var(--primary-dark); flex-shrink: 0;
}
.dept-item-icon svg { width: 18px; height: 18px; }
.dept-item-info { flex: 1; min-width: 0; }
.dept-item-name { font-size: 14px; font-weight: 500; color: var(--gray-800); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dept-item-count { font-size: 12px; color: var(--gray-400); margin-top: 2px; }
.dept-item-actions { display: flex; gap: 4px; opacity: 0; transition: opacity 0.2s; }
.dept-item:hover .dept-item-actions { opacity: 1; }

/* 右侧详情 */
.dept-detail-panel {
  flex: 1; background: white; border-radius: var(--radius-xl);
  box-shadow: var(--shadow); padding: 28px; overflow-y: auto;
}
.empty-panel { display: flex; align-items: center; justify-content: center; }

.detail-header { margin-bottom: 28px; padding-bottom: 20px; border-bottom: 1px solid var(--gray-100); }
.detail-title { font-size: 22px; font-weight: 700; color: var(--gray-800); margin-bottom: 6px; }
.detail-desc { font-size: 14px; color: var(--gray-500); }

.section { margin-bottom: 32px; }
.section-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px;
}
.section-title { font-size: 16px; font-weight: 600; color: var(--gray-700); }
.section-hint { font-size: 12px; color: var(--gray-400); }

/* 成员列表 */
.member-list { display: flex; flex-direction: column; gap: 8px; }
.member-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px; background: var(--gray-50);
  border-radius: var(--radius); transition: background 0.2s;
}
.member-item:hover { background: rgba(127,205,205,0.1); }
.member-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark, #0d9488));
  color: white; display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 600; flex-shrink: 0; overflow: hidden;
}
.member-avatar.sm { width: 32px; height: 32px; font-size: 13px; }
.avatar-img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; }
.member-name { flex: 1; font-size: 14px; color: var(--gray-700); font-weight: 500; }

/* 知识库标签 */
.kb-tag-list { display: flex; flex-wrap: wrap; gap: 8px; }
.kb-tag {
  padding: 6px 14px; background: rgba(127,205,205,0.15);
  border: 1px solid rgba(127,205,205,0.4); border-radius: var(--radius-full, 999px);
  font-size: 13px; color: var(--primary-dark);
}

/* 图标按钮 */
.icon-btn {
  width: 28px; height: 28px; border: none; border-radius: var(--radius-sm);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.icon-btn svg { width: 15px; height: 15px; }
.icon-btn.edit { background: rgba(127,205,205,0.15); color: var(--primary-dark); }
.icon-btn.edit:hover { background: rgba(127,205,205,0.3); }
.icon-btn.del { background: rgba(239,68,68,0.1); color: #ef4444; }
.icon-btn.del:hover { background: rgba(239,68,68,0.2); }

/* 弹窗 */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal {
  background: white; border-radius: var(--radius-xl);
  width: 480px; max-width: 90vw; max-height: 85vh;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2); display: flex; flex-direction: column;
}
.modal-wide { width: 560px; }
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px; border-bottom: 1px solid var(--gray-100); flex-shrink: 0;
}
.modal-header h2 { font-size: 18px; font-weight: 600; color: var(--gray-800); }
.close-btn {
  width: 32px; height: 32px; border: none; background: var(--gray-100);
  border-radius: var(--radius-sm); cursor: pointer; display: flex;
  align-items: center; justify-content: center; color: var(--gray-500);
}
.close-btn:hover { background: var(--gray-200); }
.close-btn svg { width: 18px; height: 18px; }
.modal-body { padding: 24px; overflow-y: auto; flex: 1; }
.modal-footer {
  display: flex; gap: 12px; justify-content: flex-end;
  padding: 16px 24px; border-top: 1px solid var(--gray-100); flex-shrink: 0;
}

.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 14px; font-weight: 500; color: var(--gray-700); margin-bottom: 8px; }
.req { color: #ef4444; }
.input {
  width: 100%; padding: 10px 14px; border: 2px solid var(--gray-200);
  border-radius: var(--radius); font-size: 14px; outline: none;
  transition: border-color 0.2s; box-sizing: border-box; font-family: inherit;
}
.input:focus { border-color: var(--primary); }
.textarea { resize: vertical; min-height: 80px; }

/* 用户选择列表 */
.user-pick-list { display: flex; flex-direction: column; gap: 6px; max-height: 320px; overflow-y: auto; }
.user-pick-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 12px; border-radius: var(--radius); cursor: pointer;
  border: 2px solid transparent; transition: all 0.15s;
}
.user-pick-item:hover:not(.already) { background: rgba(127,205,205,0.1); }
.user-pick-item.selected { background: rgba(127,205,205,0.15); border-color: var(--primary); }
.user-pick-item.already { opacity: 0.5; cursor: not-allowed; }
.user-pick-info { flex: 1; }
.user-pick-name { font-size: 14px; font-weight: 500; color: var(--gray-800); }
.user-pick-sub { font-size: 12px; color: var(--gray-400); margin-top: 2px; }
.check-icon { width: 18px; height: 18px; color: var(--primary); flex-shrink: 0; }
.already-tag {
  font-size: 11px; padding: 2px 8px; background: var(--gray-100);
  color: var(--gray-400); border-radius: 999px;
}

/* 空状态 */
.empty-state { text-align: center; color: var(--gray-400); }
.empty-icon { width: 56px; height: 56px; margin: 0 auto 12px; opacity: 0.3; display: block; }
.empty-state p { font-size: 15px; }
.empty-tip { padding: 20px; text-align: center; font-size: 13px; color: var(--gray-400); }

/* 删除确认弹窗 */
.modal-fade-enter-active, .modal-fade-leave-active {
  transition: opacity 0.25s ease;
}
.modal-fade-enter-active .delete-modal, .modal-fade-leave-active .delete-modal {
  transition: transform 0.25s ease, opacity 0.25s ease;
}
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
.modal-fade-enter-from .delete-modal { transform: translateY(-16px) scale(0.96); opacity: 0; }
.modal-fade-leave-to .delete-modal { transform: translateY(-12px) scale(0.96); opacity: 0; }

.delete-modal {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 380px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
  text-align: center;
  padding: 32px;
}
.modal-icon-danger {
  width: 56px; height: 56px; margin: 0 auto 16px;
  background: #fee2e2; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
}
.modal-icon-danger svg { width: 28px; height: 28px; color: #ef4444; }
.delete-modal h3 { font-size: 18px; font-weight: 600; color: var(--gray-800); margin-bottom: 8px; }
.delete-modal p { color: var(--gray-600); font-size: 14px; margin-bottom: 24px; line-height: 1.5; }
.delete-modal p strong { color: var(--gray-800); }
.modal-actions { display: flex; gap: 12px; justify-content: center; }
.btn-danger { background: #ef4444; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; transition: background 0.2s; }
.btn-danger:hover { background: #dc2626; }
</style>
