<template>
  <div class="admin-layout" v-if="!isLoginPage">
    <div class="admin-shell">
      <aside class="admin-sidebar">
        <div class="sidebar-brand">
          <span class="sidebar-brand-mark">JS</span>
          <div>
            <div class="sidebar-brand-name">Jump Rope</div>
            <div class="sidebar-brand-sub">智能测试后台</div>
          </div>
        </div>
        <nav class="sidebar-nav">
          <router-link to="/dashboard" class="nav-item">
            <span class="nav-icon">&#9632;</span>
            <span>仪表盘</span>
          </router-link>
          <div class="nav-group-title">基础数据</div>
          <router-link to="/schools" class="nav-item">
            <span class="nav-icon">&#9633;</span>
            <span>学校管理</span>
          </router-link>
          <router-link to="/grades" class="nav-item">
            <span class="nav-icon">&#9679;</span>
            <span>年级管理</span>
          </router-link>
          <router-link to="/classes" class="nav-item">
            <span class="nav-icon">&#9670;</span>
            <span>班级管理</span>
          </router-link>
          <router-link to="/students" class="nav-item">
            <span class="nav-icon">&#9702;</span>
            <span>学生管理</span>
          </router-link>
          <div class="nav-group-title">测试管理</div>
          <router-link to="/venues" class="nav-item">
            <span class="nav-icon">&#9635;</span>
            <span>考场管理</span>
          </router-link>
          <router-link to="/devices" class="nav-item">
            <span class="nav-icon">&#9881;</span>
            <span>设备管理</span>
          </router-link>
          <router-link to="/tasks" class="nav-item">
            <span class="nav-icon">&#9776;</span>
            <span>任务管理</span>
          </router-link>
          <router-link to="/scores" class="nav-item">
            <span class="nav-icon">&#9733;</span>
            <span>成绩管理</span>
          </router-link>
          <router-link to="/exceptions" class="nav-item">
            <span class="nav-icon">&#9888;</span>
            <span>异常管理</span>
          </router-link>
          <div class="nav-group-title">系统</div>
          <router-link to="/settings" class="nav-item">
            <span class="nav-icon">&#9874;</span>
            <span>系统设置</span>
          </router-link>
          <router-link to="/logs" class="nav-item">
            <span class="nav-icon">&#9998;</span>
            <span>日志管理</span>
          </router-link>
        </nav>
        <div class="sidebar-user">
          <div class="sidebar-user-meta">
            <span class="sidebar-user-avatar">{{ userInitial }}</span>
            <div>
              <div class="sidebar-user-name">{{ userName }}</div>
              <div class="sidebar-user-role">{{ userRoleText }}</div>
            </div>
          </div>
          <button class="btn-text" @click="doLogout">退出</button>
        </div>
      </aside>

      <div class="admin-main-shell">
        <header class="admin-topbar">
          <div>
            <div class="topbar-kicker">{{ currentSection }}</div>
            <h1 class="topbar-title">{{ currentTitle }}</h1>
          </div>
          <div class="topbar-tools">
            <div class="topbar-chip">{{ todayText }}</div>
            <div class="topbar-chip topbar-chip-dark">后台管理</div>
            <div class="topbar-profile">
              <span class="topbar-profile-avatar">{{ userInitial }}</span>
              <div>
                <div class="topbar-profile-name">{{ userName }}</div>
                <div class="topbar-profile-role">{{ userRoleText }}</div>
              </div>
            </div>
          </div>
        </header>

        <main class="admin-main">
          <router-view />
        </main>
      </div>
    </div>
  </div>
  <div v-else class="admin-login-page">
    <router-view />
  </div>
</template>

<script>
export default {
  data() {
    return {
      userName: "",
    };
  },
  computed: {
    isLoginPage() {
      return this.$route.path === "/login";
    },
    currentTitle() {
      return this.$route.meta?.title || "后台管理";
    },
    currentSection() {
      if (this.$route.path.startsWith("/dashboard")) return "运营总览";
      if (["/schools", "/grades", "/classes", "/students"].some((item) => this.$route.path.startsWith(item))) return "基础数据";
      if (["/venues", "/devices", "/tasks", "/scores", "/exceptions"].some((item) => this.$route.path.startsWith(item))) return "测试管理";
      return "系统配置";
    },
    userRoleText() {
      const role = localStorage.getItem("admin_role") || "admin";
      const map = {
        admin: "管理员",
      };
      return map[role] || "系统用户";
    },
    userInitial() {
      return (this.userName || "管理员").slice(0, 1);
    },
    todayText() {
      return new Date().toLocaleDateString("zh-CN", {
        year: "numeric",
        month: "long",
        day: "numeric",
      });
    },
  },
  mounted() {
    this.userName = localStorage.getItem("admin_name") || "管理员";
  },
  methods: {
    doLogout() {
      localStorage.removeItem("admin_token");
      localStorage.removeItem("admin_name");
      localStorage.removeItem("admin_role");
      this.$router.push("/login");
    },
  },
};
</script>
