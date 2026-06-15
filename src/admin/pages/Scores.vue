<template>
  <div>
    <div class="page-header">
      <h2>成绩管理</h2>
      <div class="page-header-actions">
        <button class="btn btn-success" @click="batchApprove" :disabled="!selected.length">批量确认</button>
      </div>
    </div>
    <div class="card">
      <div class="form-row">
        <input v-model="search" placeholder="搜索姓名/学号..." @keyup.enter="fetchList" style="width:200px" />
        <button class="btn btn-primary btn-sm" @click="fetchList">搜索</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr>
            <th style="width:30px"><input type="checkbox" @change="toggleAll" /></th>
            <th>学号</th><th>姓名</th><th>班级</th><th>考场</th><th>站位</th><th>次数</th><th>审核</th><th>测试时间</th><th style="width:80px">操作</th>
          </tr></thead>
          <tbody>
            <tr v-for="row in list" :key="row.id">
              <td><input type="checkbox" :value="row.id" v-model="selected" /></td>
              <td>{{ row.student_no }}</td>
              <td><a @click="$router.push(`/scores/${row.id}`)" style="color:#1890ff;cursor:pointer">{{ row.student_name }}</a></td>
              <td>{{ row.class_name }}</td><td>{{ row.venue_name }}</td><td>{{ row.slot }}</td>
              <td><strong>{{ row.final_count }}</strong></td>
              <td><span :class="reviewTag(row.review_status)">{{ row.review_status || '未审核' }}</span></td>
              <td>{{ fmtTime(row.tested_at_ms) }}</td>
              <td><button class="btn btn-default btn-sm" @click="$router.push(`/scores/${row.id}`)">详情</button></td>
            </tr>
            <tr v-if="!list.length"><td colspan="9" style="text-align:center;color:#999">暂无数据</td></tr>
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
    return { list: [], total: 0, page: 1, search: "", selected: [] };
  },
  mounted() { this.fetchList(); },
  methods: {
    async fetchList() {
      try {
        const res = await api.scores({ page: this.page, page_size: 20, search: this.search });
        this.list = res.data.list; this.total = res.data.total;
      } catch (e) { console.error(e); }
    },
    toggleAll(e) { this.selected = e.target.checked ? this.list.map(r => r.id) : []; },
    async batchApprove() {
      if (!this.selected.length) return;
      try {
        await api.scoreBatchReview({ ids: this.selected, review_status: "approved" });
        this.selected = [];
        this.fetchList();
      } catch (e) { alert(e.message); }
    },
    reviewTag(s) {
      if (s === "approved") return "tag tag-green";
      if (s === "rejected") return "tag tag-red";
      if (s === "pending") return "tag tag-orange";
      return "tag tag-gray";
    },
    fmtTime(ms) { return ms ? new Date(ms).toLocaleString("zh-CN") : "-"; },
  },
};
</script>
