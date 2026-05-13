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
        path: 'departments',
        name: 'Department',
        component: () => import('../pages/Department.vue'),
        meta: { title: '部门管理' }
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
  // ── 用户端路由（独立于管理员界面）──
  {
    path: '/user/login',
    name: 'UserLogin',
    component: () => import('../pages/UserLogin.vue'),
    meta: { title: '用户登录', public: true }
  },
  {
    path: '/user/chat',
    name: 'UserChat',
    component: () => import('../pages/UserChat.vue'),
    meta: { title: '智能问答', userPage: true }
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
  const appName = 'RAG系统'
  document.title = to.meta.title ? `${to.meta.title} - ${appName}` : appName
  
  const isPublicPage = to.meta.public === true
  const isUserPage = to.meta.userPage === true

  // 用户端页面：用 user_token 鉴权
  if (isUserPage) {
    const userToken = localStorage.getItem('user_token')
    if (!userToken) return next('/user/login')
    return next()
  }

  // 已登录用户访问用户登录页，跳转到问答
  if (to.path === '/user/login' && localStorage.getItem('user_token')) {
    return next('/user/chat')
  }

  // 管理员端鉴权
  const token = localStorage.getItem('token')
  if (to.meta.admin && !token) return next('/login')
  if (!isPublicPage && !token) return next('/login')
  if (token && to.path === '/login') return next('/')

  next()
})

export default router
