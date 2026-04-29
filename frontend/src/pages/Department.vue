<template>
  <div class="dept-page">
    <div class="page-header">
      <h1 class="page-title">部门管理</h1>
      <button class="btn btn-primary" @click="openAdd">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/></svg>
        新增部门
      </button>
    </div>

    <!-- 新增/编辑弹窗 -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editingId ? '编辑部门' : '新增部门' }}</h2>
          <button class="close-btn" @click="closeModal">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/></svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>部门名称 <span class="required">*</span></label>
            <input
              v-model="form.name"
              type="text"
              placeholder="请输入部门名称"
              class="input"
              @keyup.enter="handleSave"
            />
          </div>
          <div class="form-group">
            <label>部门描述</label>
            <textarea
              v-model="form.description"
              placeholder="请输入部门描述（可选）"
              class="input textarea"
              rows="3"
            ></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="closeModal">取消</button>
          <button class="btn btn-primary" @click="handleSave" :disabled="!form.name.trim()">
            {{ editingId ? '保存修改' : '确认添加' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 部门列表 -->
    <div class="dept-list" v-if="departments.length > 0">
      <div class="dept-card" v-for="dept in departments" :key="dept.id">
        <div class="dept-info">
          <div class="dept-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12,3L1,9L12,15L21,10.09V17H23V9M5,13.18V17.18L12,21L19,17.18V13.18L12,17L5,13.18Z"/>
            </svg>
          </div>
          <div class="dept-detail">
            <div class="dept-name">{{ dept.name }}</div>
            <div class="dept-desc" v-if="dept.description">{{ dept.description }}</div>
            <div class="dept-meta">创建于 {{ formatDate(dept.createdAt) }}</div>
          </div>
        </div>
        <div class="dept-actions">
          <button class="action-btn edit" @click="openEdit(dept)" title="编辑">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z"/>
            </svg>
          </button>
          <button class="action-btn delete" @click="handleDelete(dept)" title="删除">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="empty-state" v-else>
      <svg viewBox="0 0 24 24" fill="currentColor" class="empty-icon">
        <path d="M12,3L1,9L12,15L21,10.09V17H23V9M5,13.18V17.18L12,21L19,17.18V13.18L12,17L5,13.18Z"/>
      </svg>
      <p>暂无部门，点击右上角新增</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

const STORAGE_KEY = 'rag_departments'

const departments = ref([])
const showModal = ref(false)
const editingId = ref(null)

const form = reactive({
  name: '',
  description: ''
})

const loadDepts = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    departments.value = raw ? JSON.parse(raw) : []
  } catch {
    departments.value = []
  }
}

const saveDepts = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(departments.value))
}

const openAdd = () => {
  editingId.value = null
  form.name = ''
  form.description = ''
  showModal.value = true
}

const openEdit = (dept) => {
  editingId.value = dept.id
  form.name = dept.name
  form.description = dept.description || ''
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const handleSave = () => {
  if (!form.name.trim()) return

  if (editingId.value) {
    const idx = departments.value.findIndex(d => d.id === editingId.value)
    if (idx !== -1) {
      departments.value[idx].name = form.name.trim()
      departments.value[idx].description = form.description.trim()
    }
  } else {
    departments.value.push({
      id: Date.now().toString(),
      name: form.name.trim(),
      description: form.description.trim(),
      createdAt: new Date().toISOString()
    })
  }

  saveDepts()
  closeModal()
}

const handleDelete = (dept) => {
  if (!confirm(`确认删除部门「${dept.name}」？`)) return
  departments.value = departments.value.filter(d => d.id !== dept.id)
  saveDepts()
}

const formatDate = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

onMounted(loadDepts)
</script>

<style scoped>
.dept-page {
  padding: 32px;
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--gray-800);
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn svg {
  width: 18px;
  height: 18px;
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-dark, #0d9488);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-ghost {
  background: var(--gray-100);
  color: var(--gray-700);
}

.btn-ghost:hover {
  background: var(--gray-200);
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: var(--radius-xl);
  width: 480px;
  max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--gray-100);
}

.modal-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--gray-800);
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--gray-100);
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--gray-500);
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--gray-200);
}

.close-btn svg {
  width: 18px;
  height: 18px;
}

.modal-body {
  padding: 24px;
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 16px 24px;
  border-top: 1px solid var(--gray-100);
}

.form-group {
  margin-bottom: 20px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-700);
  margin-bottom: 8px;
}

.required {
  color: #ef4444;
}

.input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid var(--gray-200);
  border-radius: var(--radius);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
  font-family: inherit;
}

.input:focus {
  border-color: var(--primary);
}

.textarea {
  resize: vertical;
  min-height: 80px;
}

/* 部门列表 */
.dept-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.dept-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  background: white;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow);
  transition: box-shadow 0.2s;
}

.dept-card:hover {
  box-shadow: var(--shadow-md, 0 4px 16px rgba(0,0,0,0.1));
}

.dept-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.dept-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, rgba(168, 230, 207, 0.4) 0%, rgba(127, 205, 205, 0.4) 100%);
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-dark);
  flex-shrink: 0;
}

.dept-icon svg {
  width: 24px;
  height: 24px;
}

.dept-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: 2px;
}

.dept-desc {
  font-size: 13px;
  color: var(--gray-500);
  margin-bottom: 2px;
}

.dept-meta {
  font-size: 12px;
  color: var(--gray-400);
}

.dept-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.action-btn svg {
  width: 18px;
  height: 18px;
}

.action-btn.edit {
  background: rgba(127, 205, 205, 0.15);
  color: var(--primary-dark);
}

.action-btn.edit:hover {
  background: rgba(127, 205, 205, 0.3);
}

.action-btn.delete {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.action-btn.delete:hover {
  background: rgba(239, 68, 68, 0.2);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--gray-400);
}

.empty-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  opacity: 0.4;
}

.empty-state p {
  font-size: 15px;
}
</style>
