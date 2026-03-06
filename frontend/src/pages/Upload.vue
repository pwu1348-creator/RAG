<template>
  <div class="upload-page">
    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">📄</span>
        文件上传
      </h1>
    </div>

    <div class="upload-layout">
      <!-- 上传区域在顶部，铺满宽度 -->
      <div class="upload-panel">
        <div
          class="upload-area"
          :class="{ dragging: isDragging }"
          @dragenter.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @dragover.prevent
          @drop.prevent="handleDrop"
        >
          <div class="upload-content">
            <h3 class="upload-title">拖拽文件到此处或点击下方按钮</h3>
            <p class="upload-desc">支持 PDF、Word、txt、md、Excel、PPT、图片等格式</p>
            <div class="upload-actions">
              <button class="btn btn-primary upload-btn" @click="openFileDialog">
                <span class="btn-icon">📁</span>
                选择文件
              </button>
            </div>
          </div>
          <input
            ref="fileInput"
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.md,.png,.jpg,.jpeg,.gif"
            style="display: none"
            @change="handleFileSelect"
          />
        </div>
      </div>

      <!-- 文件列表区域在下方 -->
      <div class="file-table-card">
        <div class="table-header">
          <h2 class="table-title">文件列表</h2>
          <span class="file-count">共 {{ fileList.length }} 个文件</span>
        </div>
        
        <div class="table-container" v-if="fileList.length > 0">
          <table class="file-table">
            <thead>
              <tr>
                <th class="col-index">序号</th>
                <th>文件名</th>
                <th>上传时间</th>
                <th>文件类型</th>
                <th>文件大小</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <TransitionGroup name="table-row">
                <tr v-for="(file, index) in fileList" :key="file.doc_id">
                  <td class="col-index">{{ getRowNumber(index) }}</td>
                  <td>
                    <div class="file-name-cell">
                      <div class="file-icon" :class="getFileTypeClass(file.filename)">
                        <svg viewBox="0 0 24 24" fill="currentColor">
                          <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                        </svg>
                      </div>
                      <span class="file-name">{{ file.filename }}</span>
                    </div>
                  </td>
                  <td>{{ formatDate(file.created_at) }}</td>
                  <td>
                    <span class="file-type-badge" :class="getFileTypeClass(file.filename)">
                      {{ getFileType(file.filename) }}
                    </span>
                  </td>
                  <td>{{ formatFileSize(file.file_size) }}</td>
                  <td>
                    <span class="status-badge" :class="getStatusClass(file.status)">
                      {{ getStatusText(file.status) }}
                    </span>
                  </td>
                  <td>
                    <button class="action-btn delete" @click="handleDelete(file.doc_id)" title="删除">
                      <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                      </svg>
                    </button>
                  </td>
                </tr>
              </TransitionGroup>
            </tbody>
          </table>
        </div>
        
        <!-- 分页控件 -->
        <div class="pagination" v-if="total > 0">
          <div class="pagination-info">
            <span>每页</span>
            <select v-model="pageSize" @change="handleSizeChange" class="page-size-select">
              <option :value="10">10</option>
              <option :value="50">50</option>
            </select>
            <span>条，共 {{ total }} 条</span>
          </div>
          <div class="pagination-controls">
            <button 
              class="page-btn" 
              @click="goToPage(1)" 
              :disabled="currentPage === 1"
            >
              首页
            </button>
            <button 
              class="page-btn" 
              @click="goToPage(currentPage - 1)" 
              :disabled="currentPage === 1"
            >
              上一页
            </button>
            <span class="page-numbers">
              <button 
                v-for="page in visiblePages" 
                :key="page"
                class="page-num"
                :class="{ active: page === currentPage }"
                @click="goToPage(page)"
              >
                {{ page }}
              </button>
            </span>
            <button 
              class="page-btn" 
              @click="goToPage(currentPage + 1)" 
              :disabled="currentPage === totalPages"
            >
              下一页
            </button>
            <button 
              class="page-btn" 
              @click="goToPage(totalPages)" 
              :disabled="currentPage === totalPages"
            >
              末页
            </button>
          </div>
        </div>
        
        <div class="empty-state" v-else>
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
          </svg>
          <p>暂无文件，请选择文件上传</p>
        </div>
      </div>
    </div>

    <!-- 上传通知 -->
    <Teleport to="body">
      <Transition name="notification">
        <div 
          v-if="notification.show" 
          class="upload-notification"
          :class="notification.type"
        >
          <span class="notification-icon">
            <svg v-if="notification.type === 'success'" viewBox="0 0 24 24" fill="currentColor">
              <path d="M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="currentColor">
              <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </span>
          {{ notification.message }}
        </div>
      </Transition>
    </Teleport>

    <!-- 上传弹窗 -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div class="modal-overlay" v-if="showUploadModal" @click.self="closeModal">
          <Transition name="modal-slide">
            <div class="upload-modal" v-if="showUploadModal">
              <div class="modal-header">
                <h2 class="modal-title">
                  <span class="modal-icon">📤</span>
                  上传文件
                </h2>
                <button class="modal-close" @click="closeModal">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
              </svg>
            </button>
          </div>
          
          <div class="modal-body">
            <!-- 添加文件区域 -->
            <div 
              class="add-files-area"
              :class="{ dragging: isModalDragging }"
              @dragenter.prevent="isModalDragging = true"
              @dragleave.prevent="isModalDragging = false"
              @dragover.prevent
              @drop.prevent="handleModalDrop"
              @click="$refs.modalFileInput.click()"
            >
              <input
                ref="modalFileInput"
                type="file"
                multiple
                accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.md,.png,.jpg,.jpeg,.gif"
                style="display: none"
                @change="handleModalFileSelect"
              />
              <div class="add-files-content">
                <svg class="add-icon" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
                </svg>
                <p>点击或拖拽文件到此处添加</p>
                <span class="add-hint">支持批量选择多个文件</span>
              </div>
            </div>

            <!-- 待上传文件列表 -->
            <div class="pending-files-section" v-if="pendingFiles.length > 0">
              <div class="section-header">
                <h3>待上传文件 ({{ pendingFiles.length }})</h3>
                <button class="clear-btn" @click="clearPendingFiles">清空</button>
              </div>
              <div class="pending-files-list">
                <div 
                  class="pending-file-item" 
                  v-for="(file, index) in pendingFiles" 
                  :key="index"
                  :class="{ uploading: uploadingIndex === index, done: uploadDoneIndexes.includes(index) }"
                >
                  <div class="file-info">
                    <div class="file-icon-small" :class="getFileTypeClass(file.name)">
                      <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                      </svg>
                    </div>
                    <div class="file-details">
                      <span class="file-name-small">{{ file.name }}</span>
                      <span class="file-size-small">{{ formatFileSize(file.size) }}</span>
                    </div>
                  </div>
                  <div class="file-actions">
                    <span v-if="uploadingIndex === index" class="upload-status uploading-status">
                      <svg class="spinner" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12,4V2A10,10 0 0,0 2,12H4A8,8 0 0,1 12,4Z"/>
                      </svg>
                      上传中...
                    </span>
                    <span v-else-if="uploadDoneIndexes.includes(index)" class="upload-status done-status">
                      <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z"/>
                      </svg>
                      已完成
                    </span>
                    <button 
                      v-else 
                      class="remove-btn" 
                      @click.stop="removePendingFile(index)"
                      :disabled="uploadingIndex !== null"
                    >
                      <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- 上传进度 -->
            <div class="upload-progress-section" v-if="isUploading">
              <div class="progress-info">
                <span>正在上传: {{ currentUploadName }}</span>
                <span>{{ uploadSuccessCount }}/{{ pendingFiles.length }}</span>
              </div>
              <div class="progress-bar">
                <div 
                  class="progress-fill" 
                  :style="{ width: progressPercent + '%' }"
                ></div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" @click="closeModal" :disabled="isUploading">
              取消
            </button>
            <button 
              class="btn btn-primary" 
              @click="startUpload"
              :disabled="pendingFiles.length === 0 || isUploading"
            >
              <span v-if="isUploading">
                <svg class="spinner" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12,4V2A10,10 0 0,0 2,12H4A8,8 0 0,1 12,4Z"/>
                </svg>
                上传中...
              </span>
              <span v-else>开始上传</span>
            </button>
          </div>
        </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { parserApi } from '@/api'

const isDragging = ref(false)
const isModalDragging = ref(false)
const isUploading = ref(false)
const showUploadModal = ref(false)
const fileInput = ref(null)
const modalFileInput = ref(null)
const fileList = ref([])
const pendingFiles = ref([])
const uploadingIndex = ref(null)
const uploadDoneIndexes = ref([])
const uploadSuccessCount = ref(0)
const failedCount = ref(0)

const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const visiblePages = computed(() => {
  const pages = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)
  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

const getRowNumber = (index) => {
  return (currentPage.value - 1) * pageSize.value + index + 1
}

const handleSizeChange = () => {
  currentPage.value = 1
  fetchFileList()
}

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    fetchFileList()
  }
}

const currentUploadName = computed(() => {
  if (uploadingIndex.value !== null && pendingFiles.value[uploadingIndex.value]) {
    return pendingFiles.value[uploadingIndex.value].name
  }
  return ''
})

const progressPercent = computed(() => {
  if (pendingFiles.value.length === 0) return 0
  return Math.round((uploadDoneIndexes.value.length / pendingFiles.value.length) * 100)
})

const openFileDialog = () => {
  fileInput.value.click()
}

const handleDrop = (e) => {
  isDragging.value = false
  const droppedFiles = Array.from(e.dataTransfer.files)
  if (droppedFiles.length > 0) {
    addFilesToPending(droppedFiles)
  }
}

const handleFileSelect = (e) => {
  const selectedFiles = Array.from(e.target.files)
  if (selectedFiles.length > 0) {
    addFilesToPending(selectedFiles)
  }
  e.target.value = ''
}

const handleModalDrop = (e) => {
  isModalDragging.value = false
  const droppedFiles = Array.from(e.dataTransfer.files)
  if (droppedFiles.length > 0) {
    addFilesToPending(droppedFiles)
  }
}

const handleModalFileSelect = (e) => {
  const selectedFiles = Array.from(e.target.files)
  if (selectedFiles.length > 0) {
    addFilesToPending(selectedFiles)
  }
  e.target.value = ''
}

const addFilesToPending = (files) => {
  const newFiles = files.map(file => ({
    name: file.name,
    size: file.size,
    type: file.type,
    file: file
  }))
  pendingFiles.value = [...pendingFiles.value, ...newFiles]
  showUploadModal.value = true
}

const removePendingFile = (index) => {
  pendingFiles.value.splice(index, 1)
}

const clearPendingFiles = () => {
  pendingFiles.value = []
  uploadDoneIndexes.value = []
}

const closeModal = () => {
  if (!isUploading.value) {
    showUploadModal.value = false
    clearPendingFiles()
  }
}

const startUpload = async () => {
  if (pendingFiles.value.length === 0 || isUploading.value) return

  isUploading.value = true
  uploadingIndex.value = 0
  uploadDoneIndexes.value = []
  uploadSuccessCount.value = 0
  failedCount.value = 0

  for (let i = 0; i < pendingFiles.value.length; i++) {
    uploadingIndex.value = i
    try {
      await parserApi.upload(pendingFiles.value[i].file)
      uploadDoneIndexes.value.push(i)
      uploadSuccessCount.value++
    } catch (error) {
      console.error(`文件 ${pendingFiles.value[i].name} 上传失败:`, error)
      failedCount.value++
    }
  }

  isUploading.value = false
  uploadingIndex.value = null

  if (uploadSuccessCount.value > 0) {
    showNotification(`已上传 ${uploadSuccessCount.value} 个文件`, 'success')
  } else if (failedCount.value > 0) {
    showNotification(`上传失败 ${failedCount.value} 个文件`, 'error')
  }

  setTimeout(() => {
    clearPendingFiles()
    fetchFileList()
    showUploadModal.value = false
  }, 2000)
}

const notification = ref({ show: false, message: '', type: 'success' })

const showNotification = (message, type = 'success') => {
  notification.value = { show: true, message, type }
  setTimeout(() => {
    notification.value.show = false
  }, 1500)
}

const fetchFileList = async () => {
  try {
    const res = await parserApi.getDocumentList({ 
      page: currentPage.value, 
      size: pageSize.value 
    })
    if (res.data) {
      fileList.value = res.data.documents || []
      total.value = res.data.total || 0
    }
  } catch (error) {
    console.error('获取文件列表失败:', error)
  }
}

const handleDelete = async (docId) => {
  try {
    await parserApi.deleteDocument(docId)
    showNotification('文件删除成功', 'success')
    setTimeout(() => {
      fetchFileList()
    }, 500)
  } catch (error) {
    console.error('文件删除失败:', error)
    showNotification('文件删除失败', 'error')
  }
}

const getFileType = (filename) => {
  if (!filename) return '-'
  const ext = filename.split('.').pop().toLowerCase()
  const typeMap = {
    'pdf': 'PDF',
    'doc': 'Word',
    'docx': 'Word',
    'txt': '文本',
    'md': 'Markdown',
    'xls': 'Excel',
    'xlsx': 'Excel',
    'ppt': 'PPT',
    'pptx': 'PPT',
    'png': '图片',
    'jpg': '图片',
    'jpeg': '图片',
    'gif': '图片',
  }
  return typeMap[ext] || ext.toUpperCase()
}

const getFileTypeClass = (filename) => {
  if (!filename) return 'default'
  const ext = filename.split('.').pop().toLowerCase()
  const typeMap = {
    'pdf': 'pdf',
    'doc': 'word',
    'docx': 'word',
    'txt': 'text',
    'md': 'text',
    'xls': 'excel',
    'xlsx': 'excel',
    'ppt': 'ppt',
    'pptx': 'ppt',
    'png': 'image',
    'jpg': 'image',
    'jpeg': 'image',
    'gif': 'image',
  }
  return typeMap[ext] || 'default'
}

const getStatusClass = (status) => {
  const statusMap = {
    'pending': 'pending',
    'processing': 'processing',
    'completed': 'completed',
    'failed': 'failed'
  }
  return statusMap[status] || 'pending'
}

const getStatusText = (status) => {
  const statusMap = {
    'pending': '等待中',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return statusMap[status] || status
}

const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(() => {
  fetchFileList()
})
</script>

<style scoped>
.upload-page {
  padding: 32px;
}

.page-header {
  margin-bottom: 28px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--gray-800);
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 32px;
}

.upload-layout {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.upload-panel {
  width: 100%;
  margin-bottom: 16px;
}

.upload-area {
  background: #fff;
  border: 2px dashed #c0e4cf;
  border-radius: var(--radius-lg);
  padding: 48px;
  text-align: center;
  transition: all 0.3s ease;
  margin-top: 8px;
}

.upload-area.dragging {
  border-color: var(--primary);
  background: rgba(168, 230, 207, 0.1);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.upload-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--gray-700);
  margin: 0;
}

.upload-desc {
  font-size: 14px;
  color: var(--gray-500);
  margin: 0;
}

.upload-actions {
  display: flex;
  gap: 16px;
  margin-top: 8px;
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  font-size: 15px;
}

.btn-icon {
  font-size: 18px;
}

.file-table-card {
  background: #fff;
  border-radius: var(--radius-lg);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  padding: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.table-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0;
}

.file-count {
  font-size: 14px;
  color: var(--gray-500);
}

.table-container {
  overflow-x: auto;
}

.file-table {
  width: 100%;
  border-collapse: collapse;
}

.file-table th,
.file-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--gray-200);
}

.file-table th {
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-600);
  background: var(--gray-50);
}

.file-table tbody tr:hover {
  background: var(--gray-50);
}

.file-name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.file-icon svg {
  width: 20px;
  height: 20px;
}

.file-icon.pdf {
  background: #ffeaea;
  color: #f44336;
}

.file-icon.word {
  background: #e3f2fd;
  color: #2196f3;
}

.file-icon.excel {
  background: #e8f5e9;
  color: #4caf50;
}

.file-icon.ppt {
  background: #fff3e0;
  color: #ff9800;
}

.file-icon.text {
  background: #f5f5f5;
  color: #757575;
}

.file-icon.image {
  background: #fce4ec;
  color: #e91e63;
}

.file-icon.default {
  background: var(--gray-100);
  color: var(--gray-600);
}

.file-name {
  font-weight: 500;
  color: var(--gray-700);
}

.file-type-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.file-type-badge.pdf { background: #ffeaea; color: #f44336; }
.file-type-badge.word { background: #e3f2fd; color: #2196f3; }
.file-type-badge.excel { background: #e8f5e9; color: #4caf50; }
.file-type-badge.ppt { background: #fff3e0; color: #ff9800; }
.file-type-badge.text { background: #f5f5f5; color: #757575; }
.file-type-badge.image { background: #fce4ec; color: #e91e63; }

.status-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.pending { background: #f5f5f5; color: #757575; }
.status-badge.processing { background: #fff3e0; color: #ff9800; }
.status-badge.completed { background: #e8f5e9; color: #4caf50; }
.status-badge.failed { background: #ffeaea; color: #f44336; }

.action-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
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

.action-btn.delete {
  background: #ffeaea;
  color: #f44336;
}

.action-btn.delete:hover {
  background: #ffcdd2;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--gray-400);
}

.empty-state svg {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state p {
  font-size: 15px;
  margin: 0;
}

/* Modal Styles */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-slide-enter-active,
.modal-slide-leave-active {
  transition: all 0.3s ease;
}

.modal-slide-enter-from {
  opacity: 0;
  transform: translateY(-20px);
}

.modal-slide-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.upload-modal {
  background: #fff;
  border-radius: 16px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--gray-200);
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.modal-icon {
  font-size: 22px;
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--gray-100);
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.modal-close:hover {
  background: var(--gray-200);
}

.modal-close svg {
  width: 18px;
  height: 18px;
  color: var(--gray-600);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}

.add-files-area {
  border: 2px dashed #c0e4cf;
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 20px;
}

.add-files-area:hover,
.add-files-area.dragging {
  border-color: var(--primary);
  background: rgba(168, 230, 207, 0.1);
}

.add-files-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.add-icon {
  width: 40px;
  height: 40px;
  color: var(--primary);
}

.add-files-content p {
  margin: 0;
  font-size: 15px;
  color: var(--gray-700);
}

.add-hint {
  font-size: 13px;
  color: var(--gray-500);
}

.pending-files-section {
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--gray-700);
  margin: 0;
}

.clear-btn {
  border: none;
  background: none;
  color: #f44336;
  font-size: 13px;
  cursor: pointer;
}

.clear-btn:hover {
  text-decoration: underline;
}

.pending-files-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--gray-200);
  border-radius: 8px;
}

.pending-file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid var(--gray-100);
  transition: background 0.2s;
}

.pending-file-item:last-child {
  border-bottom: none;
}

.pending-file-item:hover {
  background: var(--gray-50);
}

.pending-file-item.uploading {
  background: #fff3e0;
}

.pending-file-item.done {
  background: #e8f5e9;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.file-icon-small {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--gray-100);
}

.file-icon-small svg {
  width: 16px;
  height: 16px;
  color: var(--gray-600);
}

.file-icon-small.pdf { background: #ffeaea; }
.file-icon-small.pdf svg { color: #f44336; }
.file-icon-small.word { background: #e3f2fd; }
.file-icon-small.word svg { color: #2196f3; }
.file-icon-small.excel { background: #e8f5e9; }
.file-icon-small.excel svg { color: #4caf50; }

.file-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.file-name-small {
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-700);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size-small {
  font-size: 12px;
  color: var(--gray-500);
}

.file-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.upload-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.upload-status svg {
  width: 14px;
  height: 14px;
}

.uploading-status {
  color: #ff9800;
}

.done-status {
  color: #4caf50;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.remove-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: #ffeaea;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-btn:hover {
  background: #ffcdd2;
}

.remove-btn svg {
  width: 14px;
  height: 14px;
  color: #f44336;
}

.remove-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.upload-progress-section {
  background: var(--gray-50);
  border-radius: 8px;
  padding: 12px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--gray-700);
  margin-bottom: 8px;
}

.progress-bar {
  height: 6px;
  background: var(--gray-200);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--primary);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--gray-200);
}

.btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #4caf50;
}

.btn-secondary {
  background: var(--gray-100);
  color: var(--gray-700);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--gray-200);
}

.col-index {
  width: 60px;
  text-align: center;
}

.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0 0;
  border-top: 1px solid var(--gray-200);
  margin-top: 16px;
}

.pagination-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--gray-600);
}

.page-size-select {
  padding: 4px 8px;
  border: 1px solid var(--gray-300);
  border-radius: 4px;
  font-size: 14px;
  background: #fff;
  cursor: pointer;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.page-btn {
  padding: 6px 12px;
  border: 1px solid var(--gray-300);
  background: #fff;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: var(--gray-50);
  border-color: var(--primary);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  gap: 4px;
}

.page-num {
  min-width: 32px;
  height: 32px;
  border: 1px solid var(--gray-300);
  background: #fff;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.page-num:hover {
  border-color: var(--primary);
}

.page-num.active {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}

.table-row-enter-active,
.table-row-leave-active {
  transition: all 0.3s ease;
}

.table-row-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.table-row-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.upload-notification {
  position: fixed;
  top: 20%;
  left: 50%;
  transform: translateX(-50%);
  padding: 14px 24px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 10px;
  z-index: 2000;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.upload-notification.success {
  background: #4caf50;
  color: #fff;
}

.upload-notification.error {
  background: #f44336;
  color: #fff;
}

.notification-icon {
  display: flex;
  align-items: center;
}

.notification-icon svg {
  width: 20px;
  height: 20px;
}

.notification-enter-active,
.notification-leave-active {
  transition: all 0.5s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translate(-50%, -20px);
}

.notification-leave-to {
  opacity: 0;
  transform: translate(-50%, -40px);
}
</style>
