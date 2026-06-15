<template>
  <div>
    <div class="page-header">
      <h2>异常管理</h2>
      <button class="btn btn-primary" @click="batchResolve" :disabled="!selected.length">批量处理</button>
    </div>
    <div class="card">
      <div class="form-row">
      <select v-model="filterType" @change="fetchList" style="width:140px">
        <option value="">全部类型</option><option value="system">系统异常</option><option value="device">设备异常</option>
        <option value="recognition">识别异常</option><option value="counting">计数异常</option><option value="student">学生异常</option>
      </select>
      <select v-model="filterLevel" @change="fetchList" style="width:120px">
        <option value="">全部等级</option><option value="info">提示</option><option value="warning">警告</option><option value="critical">严重</option>
      </select>
      <select v-model="filterStatus" @change="fetchList" style="width:120px">
        <option value="">全部状态</option><option value="unresolved">未处理</option><option value="resolved">已处理</option>
      </select>
      <button class="btn btn-primary btn-sm" @click="fetchList">筛选</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th style="width:30px"><input type="checkbox" @change="toggleAll" /></th>
            <th>类型</th><th>等级</th><th>描述</th><th>状态</th><th>备注</th><th>时间</th><th style="width:80px">操作</th>
          </tr></thead>
          <tbody>
            <tr v-for="row in list" :key="row.id">
              <td><input type="checkbox" :value="row.id" v-model="selected" :disabled="row.status === 'resolved'" /></td>
              <td><span :class="'tag tag-blue'">{{ row.type }}</span></td>
              <td><span :class="levelTag(row.level)">{{ levelLabel(row.level) }}</span></td>
              <td>{{ row.description }}</td>
              <td><span :class="row.status === 'resolved' ? 'tag tag-green' : 'tag tag-red'">{{ row.status === 'resolved' ? '已处理' : '未处理' }}</span></td>
              <td>{{ row.handle_remark || '-' }}</td>
              <td>{{ fmtTime(row.created_at_ms) }}</td>
              <td>
                <button v-if="row.status !== 'resolved'" class="btn btn-primary btn-sm" @click="doResolve(row)">处理</button>
              </td>
            </tr>
            <tr v-if="!list.length"><td colspan="8" style="text-align:center;color:#999">暂无异常</td></tr>
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
    return { list: [], total: 0, page: 1, filterType: "", filterLevel: "", filterStatus: "", selected: [] };
  },
  mounted() { this.fetchList(); },
  methods: {
    async fetchList() {
      try {
        const res = await api.exceptions({ page: this.page, page_size: 20, type: this.filterType, level: this.filterLevel, status: this.filterStatus });
        this.list = res.data.list; this.total = res.data.total;
      } catch (e) { console.error(e); }
    },
    levelLabel(l) { return { info: "提示", warning: "警告", critical: "严重" }[l] || l; },
    levelTag(l) { return { info: "tag tag-blue", warning: "tag tag-orange", critical: "tag tag-red" }[l] || "tag"; },
    toggleAll(e) { this.selected = e.target.checked ? this.list.filter(r => r.status !== 'resolved').map(r => r.id) : []; },
    async doResolve(row) {
      try { await api.exceptionResolve(row.id, { remark: "已人工处理" }); this.fetchList(); } catch (e) { alert(e.message); }
    },
    async batchResolve() {
      try { await api.exceptionBatchResolve({ ids: this.selected }); this.selected = []; this.fetchList(); } catch (e) { alert(e.message); }
    },
    fmtTime(ms) { return ms ? new Date(ms).toLocaleString("zh-CN") : "-"; },
  },
};
</script>
