/**
 * API 统一导出
 */

// Parser Service - 文件解析服务 (端口 8001)
export * from './parser'
export { default as parserApi } from './parser'

// Admin Service - 管理员服务 (端口 8001)
export * from './admin'

// User Service - 用户服务 (端口 8001)
export * from './user'

// Knowledge Service - 知识库服务 (端口 8001)
export * from './knowledge'

// QA Service - 问答检索服务 (端口 8002)
export * from './qa'
export { default as qaApi } from './qa'
