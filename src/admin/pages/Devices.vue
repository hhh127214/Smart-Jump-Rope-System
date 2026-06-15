<template>
  <div>
    <div class="page-header">
      <h2>设备管理</h2>
      <button class="btn btn-primary" @click="openCreate">新增设备</button>
    </div>
    <div class="card">
      <div class="form-row">
        <select v-model="venueId" @change="fetchList" style="width:200px">
          <option value="">全部考场</option>
          <option v-for="v in venues" :key="v.id" :value="v.id">{{ v.name }}</option>
        </select>
        <input v-model="search" placeholder="搜索名称/编号..." @keyup.enter="fetchList" style="width:200px" />
        <button class="btn btn-primary btn-sm" @click="fetchList">搜索</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>编号</th><th>名称</th><th>类型</th><th>考场</th><th>IP</th><th>版本</th><th>状态</th><th>心跳时间</th><th style="width:140px">操作</th></tr></thead>
          <tbody>
            <tr v-for="row in list" :key="row.id">
              <td>{{ row.device_no }}</td><td>{{ row.name }}</td>
              <td><span :class="'tag tag-blue'">{{ typeLabel(row.type) }}</span></td>
              <td>{{ row.venue_name }}</td><td>{{ row.ip_address }}</td><td>{{ row.version }}</td>
              <td><span :class="row.status === 'online' ? 'tag tag-green' : 'tag tag-gray'">{{ row.status === 'online' ? '在线' : '离线' }}</span></td>
              <td>{{ fmtTime(row.last_heartbeat_at_ms) }}</td>
              <td>
                <button class="btn btn-default btn-sm" @click="openEdit(row)">编辑</button>
                <button class="btn btn-danger btn-sm" style="margin-left:4px" @click="doDelete(row)">删除</button>
              </td>
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

    <div class="modal-overlay" v-if="showModal" @click.self="showModal = false">
      <div class="modal-box">
        <h3>{{ editing ? '编辑设备' : '新增设备' }}</h3>
        <div class="form-group"><label>所属考场 *</label><select v-model="form.venue_id"><option v-for="v in venues" :key="v.id" :value="v.id">{{ v.name }}</option></select></div>
        <div class="form-group"><label>设备编号 *</label><input v-model="form.device_no" /></div>
        <div class="form-group"><label>名称 *</label><input v-model="form.name" /></div>
        <div class="form-group"><label>类型</label><select v-model="form.type"><option value="camera">摄像头</option><option value="screen">大屏</option><option value="host">识别主机</option></select></div>
        <div class="form-group"><label>IP地址</label><input v-model="form.ip_address" /></div>
        <div class="form-group"><label>版本</label><input v-model="form.version" /></div>
        <div class="form-group"><label>状态</label><select v-model="form.status"><option value="online">在线</option><option value="offline">离线</option></select></div>
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

function typeLabel(t) {
  if (t === "camera") return "摄像头";
  if (t === "screen") return "大屏";
  if (t === "host") return "识别主机";
  return t;
}

export default {
  data() {
    return { list: [], total: 0, page: 1, search: "", venueId: "", venues: [], showModal: false, editing: null, form: {}, saving: false };
  },
  async mounted() {
    const res = await api.venues({ page: 1, page_size: 100 });
    this.venues = res.data.list;
    this.fetchList();
  },
  methods: {
    typeLabel,
    async fetchList() {
      try {
        const res = await api.devices({ page: this.page, page_size: 20, search: this.search, venue_id: this.venueId });
        this.list = res.data.list; this.total = res.data.total;
      } catch (e) { console.error(e); }
    },
    openCreate() { this.editing = null; this.form = { venue_id: this.venues[0]?.id || "", device_no: "", name: "", type: "camera", ip_address: "", version: "1.0.0", status: "offline" }; this.showModal = true; },
    openEdit(row) { this.editing = row; this.form = { ...row }; this.showModal = true; },
    async doSave() {
      this.saving = true;
      try {
        if (this.editing) await api.deviceUpdate(this.editing.id, this.form);
        else await api.deviceCreate(this.form);
        this.showModal = false; this.fetchList();
      } catch (e) { alert(e.message); }
      finally { this.saving = false; }
    },
    async doDelete(row) {
      if (!confirm(`确定删除设备"${row.name}"？`)) return;
      try { await api.deviceDelete(row.id); this.fetchList(); } catch (e) { alert(e.message); }
    },
    fmtTime(ms) { return ms ? new Date(ms).toLocaleString("zh-CN") : "-"; },
  },
};
</script>
