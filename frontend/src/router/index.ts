import { createRouter, createWebHistory } from 'vue-router'
import WorkspaceShellView from '../views/WorkspaceShellView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'workspace',
      component: WorkspaceShellView,
    },
  ],
})

export default router
