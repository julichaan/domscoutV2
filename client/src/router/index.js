import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Target from '../views/Target.vue'
import Results from '../views/Results.vue'

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
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
