import { createRouter, createWebHistory } from 'vue-router'
import { useSessionStore } from './stores/session'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'role', component: () => import('./views/RolePickerView.vue') },
    { path: '/handoffs', name: 'list', component: () => import('./views/HandoffListView.vue') },
    { path: '/handoffs/new', name: 'new', component: () => import('./views/NewHandoffView.vue'), meta: { role: 'sender' } },
    { path: '/handoffs/:id(\\d+)', name: 'handoff', component: () => import('./views/HandoffView.vue'), props: (r) => ({ id: Number(r.params.id) }) },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to) => {
  const session = useSessionStore()
  if (to.name !== 'role' && !session.role) return { name: 'role' }
  if (to.meta.role && to.meta.role !== session.role) return { name: 'list' }
})
