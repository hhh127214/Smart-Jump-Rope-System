import { createApp } from "vue";
import { createRouter, createWebHashHistory } from "vue-router";
import AdminApp from "./AdminApp.vue";
import "./admin.css";

// Pages
import Login from "./pages/Login.vue";
import Dashboard from "./pages/Dashboard.vue";
import Schools from "./pages/Schools.vue";
import Grades from "./pages/Grades.vue";
import Classes from "./pages/Classes.vue";
import Students from "./pages/Students.vue";
import StudentDetail from "./pages/StudentDetail.vue";
import Venues from "./pages/Venues.vue";
import Devices from "./pages/Devices.vue";
import Tasks from "./pages/Tasks.vue";
import Scores from "./pages/Scores.vue";
import ScoreDetail from "./pages/ScoreDetail.vue";
import Exceptions from "./pages/Exceptions.vue";
import Settings from "./pages/Settings.vue";
import Logs from "./pages/Logs.vue";

const routes = [
  { path: "/login", component: Login, meta: { title: "登录" } },
  { path: "/dashboard", component: Dashboard, meta: { title: "仪表盘" } },
  { path: "/schools", component: Schools, meta: { title: "学校管理" } },
  { path: "/grades", component: Grades, meta: { title: "年级管理" } },
  { path: "/classes", component: Classes, meta: { title: "班级管理" } },
  { path: "/students", component: Students, meta: { title: "学生管理" } },
  { path: "/students/:id", component: StudentDetail, meta: { title: "学生详情" } },
  { path: "/venues", component: Venues, meta: { title: "考场管理" } },
  { path: "/devices", component: Devices, meta: { title: "设备管理" } },
  { path: "/tasks", component: Tasks, meta: { title: "任务管理" } },
  { path: "/scores", component: Scores, meta: { title: "成绩管理" } },
  { path: "/scores/:id", component: ScoreDetail, meta: { title: "成绩详情" } },
  { path: "/exceptions", component: Exceptions, meta: { title: "异常管理" } },
  { path: "/settings", component: Settings, meta: { title: "系统设置" } },
  { path: "/logs", component: Logs, meta: { title: "日志管理" } },
  { path: "/", redirect: "/dashboard" },
  { path: "/:pathMatch(.*)", redirect: "/dashboard" },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

router.beforeEach((to) => {
  const token = localStorage.getItem("admin_token");
  if (to.path !== "/login" && !token) {
    return "/login";
  }
  document.title = (to.meta.title || "后台管理") + " - 跳绳系统";
});

const app = createApp(AdminApp);
app.use(router);
app.mount("#admin-app");
