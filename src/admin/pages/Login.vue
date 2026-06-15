<template>
  <div class="login-box">
    <h2>跳绳系统后台管理</h2>
    <div v-if="error" class="message message-error">{{ error }}</div>
    <div class="form-group">
      <label>用户名</label>
      <input v-model="username" @keyup.enter="doLogin" placeholder="请输入用户名" autofocus />
    </div>
    <div class="form-group">
      <label>密码</label>
      <input v-model="password" type="password" @keyup.enter="doLogin" placeholder="请输入密码" />
    </div>
    <button class="btn btn-primary" @click="doLogin" :disabled="loading" style="width:100%;padding:12px;font-size:15px;margin-top:8px">
      {{ loading ? '登录中...' : '登录' }}
    </button>
  </div>
</template>

<script>
import { api } from "../api.js";

export default {
  data() {
    return { username: "", password: "", error: "", loading: false };
  },
  methods: {
    async doLogin() {
      if (!this.username || !this.password) {
        this.error = "请输入用户名和密码";
        return;
      }
      this.loading = true;
      this.error = "";
      try {
        const res = await api.login({ username: this.username, password: this.password });
        const user = res.data;
        localStorage.setItem("admin_token", user.token);
        localStorage.setItem("admin_name", user.name);
        localStorage.setItem("admin_role", user.role);
        this.$router.push("/dashboard");
      } catch (e) {
        this.error = e.message;
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>
