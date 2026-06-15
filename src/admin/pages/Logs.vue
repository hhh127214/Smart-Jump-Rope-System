<template>
  <div>
    <div class="page-header">
      <h2>操作日志</h2>
    </div>
    <div class="card">
      <div class="form-row">
        <select v-model="filterModule" @change="fetchList" style="width:120px">
          <option value="">全部模块</option>
          <option value="auth">认证</option><option value="school">学校</option><option value="grade">年级</option>
          <option value="class">班级</option><option value="student">学生</option><option value="face">人脸</option>
          <option value="venue">考场</option><option value="device">设备</option><option value="task">任务</option>
          <option value="score">成绩</option><option value="exception">异常</option><option value="settings">设置</option>
          <option value="system">系统</option>
        </select>
        <button class="btn btn-primary btn-sm" @click="fetchList">搜索</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>模块</th><th>操作</th><th>目标</th><th>详情</th><th>时间</th></tr></thead>
          <tbody>
            <tr v-for="row in list" :key="row.id">
              <td><span :class="'tag tag-blue'">{{ row.module }}</span></td>
              <td>{{ row.action }}</td><td>{{ row.target }}</td>
              <td><code style="font-size:11px;max-width:200px;overflow:hidden;text-overflow:ellipsis;display:inline-block;white-space:nowrap">{{ row.detail_json }}</code></td>
              <td>{{ fmtTime(row.created_at_ms) }}</td>
            </tr>
            <tr v-if="!list.length"><td colspan="5" style="text-align:center;color:#999">暂无日志</td></tr>
          </tbody>
        </table>
      </div>
      <div class="pagination">
        <span>共 {{ total }} 条</span>
        <button :disabled="page <= 1" @click="page--; fetchList()">上一页</button>
        <span>{{ page }}</span>
        <button :disabled="page * 20 >= total" @click="page++; fetchList()">下一页</button>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from "../api.js";

export default {
  data() {
    return { list: [], total: 0, page: 1, filterModule: "" };
  },
  mounted() { this.fetchList(); },
  methods: {
    async fetchList() {
      try {
        const res = await api.operationLogs({ page: this.page, page_size: 20, module: this.filterModule });
        this.list = res.data.list; this.total = res.data.total;
      } catch (e) { console.error(e); }
    },
    fmtTime(ms) { return ms ? new Date(ms).toLocaleString("zh-CN") : "-"; },
  },
};
</script>
