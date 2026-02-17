import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Target from '../views/Target.vue'
import Results from '../views/Results.vue'
import Settings from '../views/Settings.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/target/:target/:scanId',
    name: 'Target',
    component: Target
  },
  {
    path: '/results/:scanId',
    name: 'Results',
    component: Results
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
