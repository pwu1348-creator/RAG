<template>
  <div class="knowledge-page">
    <div class="page-header">
      <h1 class="page-title">
        <span class="title-icon">📚</span>
        知识库管理
      </h1>
    </div>

    <div class="knowledge-layout">
      <!-- 新建知识库按钮 -->
      <div class="kb-panel">
        <div class="create-area" @click="showCreateModal = true">
          <div class="create-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
            </svg>
          </div>
          <span>新建知识库</span>
        </div>
      </div>

      <!-- 知识库列表 -->
      <div class="kb-table-card">
        <div class="table-header">
          <h2 class="table-title">知识库列表</h2>
          <span class="kb-count">共 {{ total }} 个知识库</span>
        </div>
        
        <div class="table-container" v-if="knowledgeBases.length > 0">
          <table class="kb-table">
            <thead>
              <tr>
                <th class="col-index">序号</th>
                <th>知识库名称</th>
                <th>描述</th>
                <th>文档数</th>
                <th>所有者</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <TransitionGroup name="table-row">
                <tr v-for="(kb, index) in knowledgeBases" :key="kb.id">
                  <td class="col-index">{{ getRowNumber(index) }}</td>
                  <td>
                    <div class="kb-name-cell">
                      <div class="kb-icon" :style="{ background: kb.color }">
                        <svg viewBox="0 0 24 24" fill="currentColor">
                          <path d="M12,3L1,9L12,15L21,10.09V17H23V9M5,13.18V17.18L12,21L19,17.18V13.18L12,17L5,13.18Z"/>
                        </svg>
                      </div>
                      <span class="kb-name-text">{{ kb.name }}</span>
                    </div>
                  </td>
                  <td class="kb-desc-cell">{{ kb.description }}</td>
                  <td>{{ kb.docCount }}</td>
                  <td>{{ kb.ownerType === 'admin' ? '管理员' : (kb.ownerId || '-') }}</td>
                  <td>{{ kb.updateTime }}</td>
                  <td>
                    <div class="action-buttons">
                      <button class="action-btn view" @click="openKBFiles(kb)" title="查看">
                        <svg viewBox="0 0 24 24" fill="currentColor">
                          <path d="M12,4.5C7,4.5 2.73,7.61 1,12C2.73,16.39 7,19.5 12,19.5C17,19.5 21.27,16.39 23,12C21.27,7.61 17,4.5 12,4.5M12,17C9.33,17 7,14.67 7,12C7,9.33 9.33,7 12,7C14.67,7 17,9.33 17,12C17,14.67 14.67,17 12,17M12,9C10.34,9 9,10.34 9,12C9,13.66 10.34,15 12,15C13.66,15 15,13.66 15,12C15,10.34 13.66,9 12,9Z"/>
                        </svg>
                      </button>
                      <button class="action-btn delete" @click="handleDeleteKB(kb.id)" title="删除">
                        <svg viewBox="0 0 24 24" fill="currentColor">
                          <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              </TransitionGroup>
            </tbody>
          </table>
        </div>
        
        <!-- 分页 -->
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
            <button class="page-btn" @click="goToPage(1)" :disabled="currentPage === 1">首页</button>
            <button class="page-btn" @click="goToPage(currentPage - 1)" :disabled="currentPage === 1">上一页</button>
            <span class="page-numbers">
              <button v-for="page in visiblePages" :key="page" class="page-num" :class="{ active: page === currentPage }" @click="goToPage(page)">{{ page }}</button>
            </span>
            <button class="page-btn" @click="goToPage(currentPage + 1)" :disabled="currentPage === totalPages">下一页</button>
            <button class="page-btn" @click="goToPage(totalPages)" :disabled="currentPage === totalPages">末页</button>
          </div>
        </div>
        
        <div class="empty-state" v-else>
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12,3L1,9L12,15L21,10.09V17H23V9M5,13.18V17.18L12,21L19,17.18V13.18L12,17L5,13.18Z"/>
          </svg>
          <p>暂无知识库，请创建知识库</p>
        </div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
          <Transition name="modal-slide">
            <div class="confirm-modal" v-if="showDeleteModal">
              <div class="confirm-header">
                <h3>确认删除</h3>
              </div>
              <div class="confirm-body">
                <p>确定要删除知识库 "{{ deleteKBName }}" 吗？</p>
                <p class="warning-text">此操作不可恢复</p>
              </div>
              <div class="confirm-footer">
                <button class="btn btn-secondary" @click="showDeleteModal = false">取消</button>
                <button class="btn btn-danger" @click="confirmDeleteKB">删除</button>
              </div>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>

    <!-- 创建知识库模态框 -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
          <Transition name="modal-slide">
            <div class="modal-content" v-if="showCreateModal">
              <div class="modal-header">
                <h3>新建知识库</h3>
                <button class="close-btn" @click="showCreateModal = false">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
                  </svg>
                </button>
              </div>
              <div class="modal-body">
                <div class="form-group">
                  <label>知识库名称</label>
                  <input type="text" v-model="newKB.name" placeholder="请输入知识库名称" @keyup.enter="handleCreateKB" />
                </div>
                <div class="form-group">
                  <label>描述</label>
                  <textarea v-model="newKB.description" placeholder="请输入知识库描述（可选）" rows="3"></textarea>
                </div>
                <div class="form-group">
                  <label>知识库所有者</label>
                  <select v-model="newKB.owner_id" class="owner-select">
                    <option value="">管理员</option>
                    <option value="user1">用户1</option>
                    <option value="user2">用户2</option>
                    <option value="user3">用户3</option>
                  </select>
                </div>
              </div>
              <div class="modal-footer">
                <button class="btn btn-secondary" @click="showCreateModal = false">取消</button>
                <button class="btn btn-primary" @click="handleCreateKB" :disabled="!newKB.name.trim()">创建</button>
              </div>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>

    <!-- 知识库文件管理弹窗 -->
    <Teleport to="body">
      <div v-if="showKBFilesModal" class="modal-overlay" @click.self="showKBFilesModal = false">
        <Transition name="modal-slide">
          <div class="modal-content kb-files-modal" v-if="showKBFilesModal">
            <div class="modal-header">
              <h3>知识库文件 - {{ currentKB?.name }}</h3>
              <button class="close-btn" @click="closeKBFilesModal">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
                </svg>
              </button>
            </div>
            <div class="modal-body">
              <div class="kb-files-toolbar">
                <button class="btn btn-primary" @click="openLinkFileModal">添加文件</button>
                <button class="btn btn-secondary" @click="handleBatchParse" :disabled="selectedFiles.length === 0">批量解析 ({{ selectedFiles.length }})</button>
              </div>
              <div class="kb-files-container">
                <div class="kb-files-list" v-if="kbFilesList.length > 0">
                  <div v-for="file in kbFilesList" :key="file.doc_id" class="kb-file-item">
                    <div class="file-checkbox">
                      <input type="checkbox" :value="file.doc_id" v-model="selectedFiles" />
                    </div>
                    <div class="file-info">
                      <div class="file-name-row">
                        <span class="file-name">{{ file.filename }}</span>
                        <span class="file-status" :class="file.kb_status || file.status">{{ 
                          (file.kb_status || file.status) === 'completed' ? '已完成' : 
                          (file.kb_status || file.status) === 'processing' ? '解析中' : 
                          (file.kb_status || file.status) === 'failed' ? '失败' : '待解析' 
                        }}</span>
                      </div>
                      <div class="file-progress">
                        <div class="progress-bar">
                          <div class="progress-fill" :class="file.kb_status || file.status" 
                               :style="{ width: (file.kb_progress || ((file.kb_status || file.status) === 'completed' ? 100 : 
                                                (file.kb_status || file.status) === 'processing' ? 30 : 0)) + '%' }"></div>
                        </div>
                      </div>
                    </div>
                    <div class="file-actions">
                      <button v-if="(file.kb_status || file.status) !== 'completed'" 
                              class="btn-parse" @click="handleParseFile(file.doc_id)">解析</button>
                      <span v-else class="btn-done">已完成</span>
                      <button class="action-btn delete" @click="handleRemoveFile(file.doc_id)" title="移除">
                        <svg viewBox="0 0 24 24" fill="currentColor">
                          <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
                <div v-else class="empty-tip">暂无文件，请点击"添加文件"按钮关联文件</div>
                <div class="kb-files-pagination">
                  <div class="pagination-info">
                    <span>共 {{ kbFilesTotal }} 条</span>
                  </div>
                  <div class="pagination-controls">
                    <button class="page-btn" @click="goToKBFilesPage(kbFilesPage - 1)" :disabled="kbFilesPage === 1">上一页</button>
                    <span class="page-num">{{ kbFilesPage }} / {{ Math.max(1, Math.ceil(kbFilesTotal / kbFilesPageSize)) }}</span>
                    <button class="page-btn" @click="goToKBFilesPage(kbFilesPage + 1)" :disabled="kbFilesPage >= Math.max(1, Math.ceil(kbFilesTotal / kbFilesPageSize))">下一页</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Teleport>

    <!-- 添加文件关联弹窗 -->
    <Teleport to="body">
      <div v-if="showLinkFileModal" class="modal-overlay" @click.self="showLinkFileModal = false">
        <Transition name="modal-slide">
          <div class="modal-content" v-if="showLinkFileModal">
            <div class="modal-header">
              <h3>添加文件到知识库</h3>
              <button class="close-btn" @click="showLinkFileModal = false">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
                </svg>
              </button>
            </div>
            <div class="modal-body">
              <div class="unlinked-files-list" v-if="unlinkedFiles.length > 0">
                <div v-for="file in unlinkedFiles" :key="file.doc_id" class="unlinked-file-item">
                  <span class="file-name">{{ file.filename }}</span>
                  <button class="btn btn-sm btn-primary" @click="handleAssociateFile(file.doc_id)">关联</button>
                </div>
              </div>
              <div v-else class="empty-tip">暂无未关联的文件</div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" @click="showLinkFileModal = false">关闭</button>
            </div>
          </div>
        </Transition>
      </div>
    </Teleport>
    <Teleport to="body">
      <Transition name="notification">
        <div v-if="notification.show" class="upload-notification" :class="notification.type">
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { knowledgeApi } from '../api/knowledge'

const knowledgeBases = ref([])
const loading = ref(false)
const showCreateModal = ref(false)
const newKB = ref({ name: '', description: '', owner_id: '' })
const currentKB = ref(null)

const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

const showDeleteModal = ref(false)
const deleteKBId = ref(null)
const deleteKBName = ref('')

const showKBFilesModal = ref(false)
const kbFilesList = ref([])
const kbFilesLoading = ref(false)
const selectedFiles = ref([])
const kbFilesPage = ref(1)
const kbFilesPageSize = ref(10)
const kbFilesTotal = ref(0)
const kbFilesPolling = ref(null)
const unlinkedFiles = ref([])
const showLinkFileModal = ref(false)

const notification = ref({ show: false, message: '', type: 'success' })

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
  loadKnowledgeBases()
}

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    loadKnowledgeBases()
  }
}

const showNotification = (message, type = 'success') => {
  notification.value = { show: true, message, type }
  setTimeout(() => {
    notification.value.show = false
  }, 1500)
}

const loadKnowledgeBases = async () => {
  loading.value = true
  try {
    const res = await knowledgeApi.getList({ page: currentPage.value, size: pageSize.value })
    if (res.code === 200 && res.data && res.data.knowledge_bases) {
      knowledgeBases.value = res.data.knowledge_bases.map((kb, index) => ({
        id: kb.kb_id,
        name: kb.name,
        description: kb.description || '暂无描述',
        docCount: kb.doc_count || 0,
        chunkCount: kb.total_chunks || 0,
        status: kb.status || 'active',
        updateTime: kb.updated_at ? formatTime(kb.updated_at) : '刚刚',
        ownerId: kb.owner_id,
        ownerType: kb.owner_type,
        color: getColorByIndex(index),
      }))
      total.value = res.data.total || 0
    }
  } catch (err) {
    console.error('Failed to load knowledge bases:', err)
  } finally {
    loading.value = false
  }
}

const handleCreateKB = async () => {
  if (!newKB.value.name.trim()) return
  try {
    const params = {
      name: newKB.value.name,
      description: newKB.value.description
    }
    if (newKB.value.owner_id) {
      params.owner_id = newKB.value.owner_id
    }
    await knowledgeApi.create(params)
    showNotification('知识库创建成功', 'success')
    showCreateModal.value = false
    newKB.value = { name: '', description: '', owner_id: '' }
    await loadKnowledgeBases()
  } catch (err) {
    console.error('Failed to create knowledge base:', err)
    showNotification('知识库创建失败', 'error')
  }
}

const handleDeleteKB = (id) => {
  const kb = knowledgeBases.value.find(k => k.id === id)
  deleteKBId.value = id
  deleteKBName.value = kb ? kb.name : ''
  showDeleteModal.value = true
}

const confirmDeleteKB = async () => {
  try {
    await knowledgeApi.delete(deleteKBId.value)
    showNotification('知识库删除成功', 'success')
    showDeleteModal.value = false
    loadKnowledgeBases()
  } catch (err) {
    console.error('Failed to delete knowledge base:', err)
    showNotification('知识库删除失败', 'error')
  }
}

const getStatusText = (status) => {
  const map = {
    active: '正常',
    building: '构建中',
    error: '异常',
  }
  return map[status] || status
}

const formatTime = (timeStr) => {
  if (!timeStr) return '刚刚'
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

const getFileType = (filename) => {
  if (!filename) return 'file'
  const ext = filename.split('.').pop().toLowerCase()
  if (ext === 'pdf') return 'pdf'
  if (['doc', 'docx'].includes(ext)) return 'word'
  if (['md', 'markdown'].includes(ext)) return 'markdown'
  return 'file'
}

const getColorByIndex = (index) => {
  const colors = [
    'linear-gradient(135deg, #a8e6cf 0%, #88d8b0 100%)',
    'linear-gradient(135deg, #7fcdcd 0%, #5cb8b2 100%)',
    'linear-gradient(135deg, #b4e7ce 0%, #98d8c8 100%)',
    'linear-gradient(135deg, #e8d5c4 0%, #d4c4b0 100%)',
  ]
  return colors[index % colors.length]
}

const openKBFiles = async (kb) => {
  currentKB.value = kb
  kbFilesPage.value = 1
  selectedFiles.value = []
  showKBFilesModal.value = true
  if (kbFilesPolling.value) {
    clearInterval(kbFilesPolling.value)
    kbFilesPolling.value = null
  }
  await loadKBFiles(kb.id)
}

const closeKBFilesModal = () => {
  showKBFilesModal.value = false
  if (kbFilesPolling.value) {
    clearInterval(kbFilesPolling.value)
    kbFilesPolling.value = null
  }
}

const loadKBFiles = async (kbId) => {
  kbFilesLoading.value = true
  try {
    const res = await knowledgeApi.getDocuments(kbId, { page: kbFilesPage.value, size: kbFilesPageSize.value })
    if (res.code === 200 && res.data) {
      kbFilesList.value = res.data.documents || []
      kbFilesTotal.value = res.data.total || 0
      
      const hasProcessing = (res.data.documents || []).some(f => 
        f.kb_status === 'processing' || f.status === 'processing'
      )
      
      if (hasProcessing && !kbFilesPolling.value) {
        kbFilesPolling.value = setInterval(() => loadKBFiles(kbId), 5000)
      } else if (!hasProcessing && kbFilesPolling.value) {
        clearInterval(kbFilesPolling.value)
        kbFilesPolling.value = null
      }
    }
  } catch (err) {
    console.error('Failed to load KB files:', err)
  } finally {
    kbFilesLoading.value = false
  }
}

const loadUnlinkedFiles = async () => {
  try {
    const res = await knowledgeApi.getUnlinkedFiles({ page: 1, size: 100 })
    if (res.code === 200 && res.data) {
      unlinkedFiles.value = res.data.documents || []
    }
  } catch (err) {
    console.error('Failed to load unlinked files:', err)
  }
}

const openLinkFileModal = async () => {
  showLinkFileModal.value = true
  await loadUnlinkedFiles()
}

const goToKBFilesPage = async (page) => {
  kbFilesPage.value = page
  await loadKBFiles(currentKB.value.id)
}

const handleAssociateFile = async (docId) => {
  try {
    await knowledgeApi.associateFile(currentKB.value.id, docId)
    showNotification('文件关联成功', 'success')
    await loadKBFiles(currentKB.value.id)
    await loadUnlinkedFiles()
  } catch (err) {
    console.error('Failed to associate file:', err)
    showNotification('文件关联失败', 'error')
  }
}

const handleParseFile = async (docId) => {
  try {
    await knowledgeApi.parseDocument(currentKB.value.id, docId)
    showNotification('解析已启动', 'success')
    await loadKBFiles(currentKB.value.id)
  } catch (err) {
    console.error('Failed to parse file:', err)
    showNotification('解析启动失败', 'error')
  }
}

const handleRemoveFile = async (docId) => {
  try {
    await knowledgeApi.removeFile(currentKB.value.id, docId)
    showNotification('文件已移除', 'success')
    await loadKBFiles(currentKB.value.id)
  } catch (err) {
    console.error('Failed to remove file:', err)
    showNotification('文件移除失败', 'error')
  }
}

const handleBatchParse = async () => {
  if (selectedFiles.value.length === 0) return
  try {
    for (const docId of selectedFiles.value) {
      await knowledgeApi.parseDocument(currentKB.value.id, docId)
    }
    showNotification('已启动批量解析', 'success')
    selectedFiles.value = []
    await loadKBFiles(currentKB.value.id)
  } catch (err) {
    console.error('Failed to batch parse:', err)
    showNotification('批量解析失败', 'error')
  }
}

onMounted(() => {
  loadKnowledgeBases()
})
</script>

<style scoped>
.knowledge-page {
  padding: 32px;
  max-width: 1200px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--gray-800);
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.title-icon {
  font-size: 32px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--gray-500);
}

.header-actions .btn svg {
  width: 20px;
  height: 20px;
}

/* 模态框 */
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

.modal-content {
  background: white;
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 480px;
  box-shadow: var(--shadow-xl);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--gray-200);
}

.modal-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--gray-400);
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: var(--gray-100);
  color: var(--gray-600);
}

.close-btn svg {
  width: 20px;
  height: 20px;
}

.modal-body {
  padding: 24px;
}

.modal-body .form-group {
  margin-bottom: 20px;
}

.modal-body .form-group:last-child {
  margin-bottom: 0;
}

.modal-body .form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-700);
  margin-bottom: 8px;
}

.modal-body .form-group input,
.modal-body .form-group textarea,
.modal-body .form-group select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  font-size: 14px;
  color: var(--gray-800);
  background: white;
  transition: border-color 0.2s ease;
  box-sizing: border-box;
}

.modal-body .form-group input:focus,
.modal-body .form-group textarea:focus,
.modal-body .form-group select:focus {
  outline: none;
  border-color: var(--primary);
}

.modal-body .form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--gray-200);
}

.modal-footer .btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.kb-card {
  cursor: pointer;
}

/* 列表布局 */
.knowledge-layout {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.kb-panel {
  width: 100%;
}

.create-area {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(16, 185, 129, 0.1));
  border: 2px dashed rgba(34, 197, 94, 0.3);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.3s ease;
}

.create-area:hover {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(16, 185, 129, 0.15));
  border-color: rgba(34, 197, 94, 0.5);
}

.create-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius);
  background: linear-gradient(135deg, #22c55e, #10b981);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.create-icon svg {
  width: 24px;
  height: 24px;
}

.create-area span {
  font-size: 16px;
  font-weight: 500;
  color: #166534;
}

/* 列表卡片 */
.kb-table-card {
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
  overflow: hidden;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--gray-200);
}

.table-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--gray-800);
}

.kb-count {
  font-size: 14px;
  color: var(--gray-500);
}

/* 表格 */
.table-container {
  overflow-x: auto;
}

.kb-table {
  width: 100%;
  border-collapse: collapse;
}

.kb-table th {
  padding: 14px 16px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-500);
  background: var(--gray-50);
  border-bottom: 1px solid var(--gray-200);
}

.kb-table td {
  padding: 16px;
  border-bottom: 1px solid var(--gray-100);
  color: var(--gray-700);
}

.kb-table tbody tr {
  transition: background-color 0.2s ease;
}

.kb-table tbody tr:hover {
  background: rgba(34, 197, 94, 0.04);
}

.col-index {
  width: 60px;
  text-align: center;
  color: var(--gray-400);
}

.kb-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.kb-name-cell .kb-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.kb-name-cell .kb-icon svg {
  width: 18px;
  height: 18px;
}

.kb-name-text {
  font-weight: 500;
  color: var(--gray-800);
}

.kb-desc-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--gray-500);
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn svg {
  width: 18px;
  height: 18px;
}

.action-btn.view {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
}

.action-btn.view:hover {
  background: rgba(34, 197, 94, 0.2);
}

.action-btn.delete {
  background: rgba(229, 115, 115, 0.1);
  color: #dc2626;
}

.action-btn.delete:hover {
  background: rgba(229, 115, 115, 0.2);
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-top: 1px solid var(--gray-200);
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
  border-radius: var(--radius-sm);
  font-size: 14px;
  outline: none;
}

.owner-select {
  padding: 10px 14px;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  font-size: 14px;
  outline: none;
  background: white;
  cursor: pointer;
}

.owner-select:focus {
  border-color: var(--primary);
}

.page-size-select:focus {
  border-color: #22c55e;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.page-btn {
  padding: 6px 12px;
  border: 1px solid var(--gray-300);
  background: white;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  background: var(--gray-50);
  border-color: #22c55e;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  gap: 4px;
  margin: 0 8px;
}

.page-num {
  width: 32px;
  height: 32px;
  border: 1px solid var(--gray-300);
  background: white;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-num:hover {
  border-color: #22c55e;
  background: rgba(34, 197, 94, 0.05);
}

.page-num.active {
  background: #22c55e;
  border-color: #22c55e;
 }

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-state svg {
  width: 64px;
  height: 64px;
  color: var(--gray-300);
  margin-bottom: 16px;
}

.empty-state p {
  color: var(--gray-500);
  font-size: 15px;
}

/* 确认删除弹窗 */
.confirm-modal {
  background: white;
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 400px;
  overflow: hidden;
}

.confirm-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--gray-200);
}

.confirm-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--gray-800);
}

.confirm-body {
  padding: 24px;
}

.confirm-body p {
  color: var(--gray-700);
  margin-bottom: 8px;
}

.warning-text {
  color: #dc2626;
  font-size: 14px;
}

.confirm-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--gray-200);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-danger {
  background: #dc2626;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: var(--radius);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-danger:hover {
  background: #b91c1c;
}

/* 动画 */
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

/* 通知 */
.upload-notification {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  padding: 14px 24px;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 10px;
  z-index: 9999;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.upload-notification.success {
  background: #22c55e;
  color: white;
}

.upload-notification.error {
  background: #dc2626;
  color: white;
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
  transform: translateY(20px);
}

.notification-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.kb-files-modal {
  max-width: 900px;
  width: 900px;
  height: 600px;
  display: flex;
  flex-direction: column;
}

.kb-files-modal .modal-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.kb-files-toolbar {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}

.kb-files-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.kb-files-list {
  flex: 1;
  overflow-y: auto;
  min-height: 200px;
}

.kb-files-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-top: 1px solid var(--gray-200);
  margin-top: 12px;
}

.kb-files-pagination .pagination-info {
  font-size: 13px;
  color: var(--gray-500);
}

.kb-files-pagination .pagination-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.kb-files-pagination .page-btn {
  padding: 6px 12px;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-sm);
  background: white;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.kb-files-pagination .page-btn:hover:not(:disabled) {
  border-color: var(--primary);
  color: var(--primary);
}

.kb-files-pagination .page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.kb-files-pagination .page-num {
  font-size: 13px;
  color: var(--gray-600);
}

.file-checkbox {
  flex-shrink: 0;
  margin-right: 12px;
}

.file-checkbox input {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.kb-file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-md);
  margin-bottom: 10px;
  transition: all 0.2s ease;
}

.kb-file-item:hover {
  border-color: var(--primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.kb-file-item:last-child {
  margin-bottom: 0;
}

.file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-name-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-name {
  font-size: 14px;
  color: var(--gray-700);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
  flex-shrink: 0;
}

.file-status.pending {
  background: #F3F4F6;
  color: #6B7280;
}

.file-status.processing {
  background: #FEF3C7;
  color: #D97706;
}

.file-status.completed {
  background: #D1FAE5;
  color: #059669;
}

.file-status.failed {
  background: #FEE2E2;
  color: #DC2626;
}

.file-progress {
  width: 100%;
}

.progress-bar {
  height: 4px;
  background: var(--gray-200);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.progress-fill.pending {
  background: var(--gray-400);
}

.progress-fill.processing {
  background: linear-gradient(90deg, #F59E0B 0%, #FBBF24 100%);
}

.progress-fill.completed {
  background: linear-gradient(90deg, #10B981 0%, #34D399 100%);
}

.progress-fill.failed {
  background: #EF4444;
}

.btn-parse {
  padding: 6px 16px;
  background: #10B981;
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-parse:hover {
  background: #059669;
}

.btn-done {
  padding: 6px 16px;
  background: var(--gray-100);
  color: var(--gray-500);
  border-radius: var(--radius-sm);
  font-size: 13px;
}

.file-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.file-actions .action-btn {
  width: 28px;
  height: 28px;
  padding: 4px;
}

.file-actions .action-btn.parse {
  color: #3B82F6;
}

.file-actions .action-btn.parse:hover {
  background: #DBEAFE;
}

.unlinked-files-list {
  max-height: 300px;
  overflow-y: auto;
}

.unlinked-file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-md);
  margin-bottom: 8px;
  transition: all 0.2s ease;
}

.unlinked-file-item:hover {
  background: var(--gray-50);
  border-color: var(--primary);
}

.unlinked-file-item:last-child {
  margin-bottom: 0;
}

.empty-tip {
  text-align: center;
  padding: 40px 20px;
  color: var(--gray-400);
  font-size: 14px;
}

.btn-sm {
  padding: 4px 12px;
  font-size: 12px;
}
</style>
