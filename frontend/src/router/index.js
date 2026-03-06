import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../components/Layout.vue'
import Home from '../pages/Home.vue'
import UserManagement from '../pages/UserManagement.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: '',
        name: 'Home',
        component: Home,
        meta: { title: '首页' }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: UserManagement,
        meta: { title: '用户管理' }
      },
      {
        path: 'users/add',
        name: 'AddUser',
        component: () => import('../pages/AddUser.vue'),
        meta: { title: '新增用户' }
      },
      {
        path: 'users/edit/:id',
        name: 'EditUser',
        component: () => import('../pages/EditUser.vue'),
        meta: { title: '编辑用户' }
      },
      {
        path: 'parser',
        name: 'Upload',
        component: () => import('../pages/Upload.vue'),
        meta: { title: '文件上传' }
      },
      {
        path: 'qa',
        name: 'QA',
        component: () => import('../pages/QA.vue'),
        meta: { title: '问答检索' }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('../pages/Knowledge.vue'),
        meta: { title: '知识库' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../pages/Settings.vue'),
        meta: { title: '系统设置' }
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../pages/Login.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/admin/dashboard',
    name: 'AdminDashboard',
    component: () => import('../pages/AdminDashboard.vue'),
    meta: { title: '管理后台', admin: true }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../pages/NotFound.vue'),
    meta: { title: '页面不存在' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  const appName = localStorage.getItem('locale') === 'en' ? 'RAG System' : 'RAG系统'
  document.title = to.meta.title ? `${to.meta.title} - ${appName}` : appName
  
  // 检查是否是公开页面
  const isPublicPage = to.meta.public === true
  
  // 检查登录token
  const token = localStorage.getItem('token')
  
  // 管理员权限检查
  if (to.meta.admin && !token) {
    return next('/login')
  }
  
  // 非公开页面需要登录
  if (!isPublicPage && !token) {
    return next('/login')
  }
  
  // 已登录用户访问登录页，重定向到首页
  if (token && to.path === '/login') {
    return next('/')
  }
  
  next()
})

export default router
