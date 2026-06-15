<template>
  <div>
    <div class="page-header">
      <h2>任务管理</h2>
      <button class="btn btn-primary" @click="openCreate">新建任务</button>
    </div>
    <div class="card">
      <div class="form-row">
        <select v-model="filterStatus" @change="fetchList" style="width:160px">
          <option value="">全部状态</option>
          <option value="draft">草稿</option><option value="published">已发布</option>
          <option value="running">进行中</option><option value="finished">已完成</option>
          <option value="cancelled">已取消</option>
        </select>
        <input v-model="search" placeholder="搜索名称..." @keyup.enter="fetchList" style="width:200px" />
        <button class="btn btn-primary btn-sm" @click="fetchList">搜索</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>名称</th><th>测试日期</th><th>考场</th><th>时长(s)</th><th>状态</th><th style="width:200px">操作</th></tr></thead>
          <tbody>
            <tr v-for="row in list" :key="row.id">
              <td>{{ row.name }}</td><td>{{ row.test_date }}</td><td>{{ row.venue_name }}</td>
              <td>{{ row.duration_sec }}</td>
              <td><span :class="statusTag(row.status)">{{ statusLabel(row.status) }}</span></td>
              <td>
                <button class="btn btn-default btn-sm" @click="openEdit(row)">编辑</button>
                <button v-if="row.status === 'draft'" class="btn btn-primary btn-sm" style="margin-left:4px" @click="doPublish(row)">发布</button>
                <button v-if="row.status === 'published' || row.status === 'draft'" class="btn btn-warning btn-sm" style="margin-left:4px" @click="doCancel(row)">取消</button>
              </td>
            </tr>
            <tr v-if="!list.length"><td colspan="6" style="text-align:center;color:#999">暂无数据</td></tr>
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

    <div class="modal-overlay" v-if="showModal" @click.self="showModal = false">
      <div class="modal-box">
        <h3>{{ editing ? '编辑任务' : '新建任务' }}</h3>
        <div class="form-group"><label>任务名称 *</label><input v-model="form.name" /></div>
        <div class="form-row">
          <div class="form-group"><label>测试日期</label><input v-model="form.test_date" type="date" /></div>
          <div class="form-group"><label>时间段</label><input v-model="form.time_range" placeholder="08:00-10:00" /></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>时长(秒)</label><input v-model.number="form.duration_sec" type="number" /></div>
          <div class="form-group"><label>倒计时(秒)</label><input v-model.number="form.countdown_sec" type="number" /></div>
          <div class="form-group"><label>绑定动作</label><select v-model="form.binding_action"><option value="wave">挥手</option><option value="jump">跳跃</option></select></div>
        </div>
        <div class="form-group"><label>目标类型</label><select v-model="form.target_type"><option value="class">班级</option><option value="grade">年级</option><option value="school">学校</option></select></div>
        <div class="form-group"><label>考场</label><select v-model="form.venue_id"><option value="">--</option><option v-for="v in venues" :key="v.id" :value="v.id">{{ v.name }}</option></select></div>
        <div class="form-group"><label>状态</label><select v-model="form.status"><option value="draft">草稿</option><option value="published">已发布</option><option value="cancelled">已取消</option></select></div>
        <div class="modal-actions">
          <button class="btn btn-default" @click="showModal = false">取消</button>
          <button class="btn btn-primary" @click="doSave" :disabled="saving">{{ saving ? '保存中...' : '保存' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from "../api.js";

const STATUS_MAP = { draft: "草稿", published: "已发布", running: "进行中", finished: "已完成", cancelled: "已取消" };
const STATUS_TAG = { published: "tag tag-green", running: "tag tag-blue", finished: "tag tag-gray", cancelled: "tag tag-red", draft: "tag tag-orange" };

export default {
  data() {
    return { list: [], total: 0, page: 1, search: "", filterStatus: "", venues: [], showModal: false, editing: null, form: {}, saving: false };
  },
  async mounted() {
    const res = await api.venues({ page: 1, page_size: 100 });
    this.venues = res.data.list;
    this.fetchList();
  },
  methods: {
    statusLabel(s) { return STATUS_MAP[s] || s; },
    statusTag(s) { return STATUS_TAG[s] || "tag tag-gray"; },
    async fetchList() {
      try {
        const res = await api.tasks({ page: this.page, page_size: 20, search: this.search, status: this.filterStatus });
        this.list = res.data.list; this.total = res.data.total;
      } catch (e) { console.error(e); }
    },
    openCreate() { this.editing = null; this.form = { name: "", test_date: "", time_range: "", target_type: "class", target_ref: "", venue_id: "", duration_sec: 60, countdown_sec: 5, binding_action: "wave", status: "draft", device_ids: [] }; this.showModal = true; },
    openEdit(row) { this.editing = row; this.form = { ...row }; this.showModal = true; },
    async doSave() {
      this.saving = true;
      try {
        if (this.editing) await api.taskUpdate(this.editing.id, this.form);
        else await api.taskCreate(this.form);
        this.showModal = false; this.fetchList();
      } catch (e) { alert(e.message); }
      finally { this.saving = false; }
    },
    async doPublish(row) {
      try { await api.taskPublish(row.id); this.fetchList(); } catch (e) { alert(e.message); }
    },
    async doCancel(row) {
      try { await api.taskCancel(row.id); this.fetchList(); } catch (e) { alert(e.message); }
    },
  },
};
</script>
