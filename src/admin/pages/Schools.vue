<template>
  <div>
    <div class="page-header">
      <h2>学校管理</h2>
      <button class="btn btn-primary" @click="openCreate">新增学校</button>
    </div>
    <div class="card">
      <div class="form-row">
        <input v-model="search" placeholder="搜索名称/编号..." @keyup.enter="fetchList" style="width:240px" />
        <button class="btn btn-primary btn-sm" @click="fetchList">搜索</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>名称</th><th>编号</th><th>联系人</th><th>电话</th><th>状态</th><th>创建时间</th><th style="width:140px">操作</th></tr></thead>
          <tbody>
            <tr v-for="row in list" :key="row.id">
              <td>{{ row.name }}</td><td>{{ row.code }}</td>
              <td>{{ row.contact_name }}</td><td>{{ row.contact_phone }}</td>
              <td><span :class="row.status === 'enabled' ? 'tag tag-green' : 'tag tag-gray'">{{ row.status === 'enabled' ? '启用' : '停用' }}</span></td>
              <td>{{ fmtTime(row.created_at_ms) }}</td>
              <td>
                <button class="btn btn-default btn-sm" @click="openEdit(row)">编辑</button>
                <button class="btn btn-danger btn-sm" style="margin-left:4px" @click="doDelete(row)">删除</button>
              </td>
            </tr>
            <tr v-if="!list.length"><td colspan="7" style="text-align:center;color:#999">暂无数据</td></tr>
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

    <!-- Modal -->
    <div class="modal-overlay" v-if="showModal" @click.self="showModal = false">
      <div class="modal-box">
        <h3>{{ editing ? '编辑学校' : '新增学校' }}</h3>
        <div class="form-group"><label>名称 *</label><input v-model="form.name" /></div>
        <div class="form-group"><label>编号 *</label><input v-model="form.code" /></div>
        <div class="form-group"><label>联系人</label><input v-model="form.contact_name" /></div>
        <div class="form-group"><label>联系电话</label><input v-model="form.contact_phone" /></div>
        <div class="form-group"><label>状态</label><select v-model="form.status"><option value="enabled">启用</option><option value="disabled">停用</option></select></div>
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

export default {
  data() {
    return { list: [], total: 0, page: 1, search: "", showModal: false, editing: null, form: {}, saving: false };
  },
  mounted() { this.fetchList(); },
  methods: {
    async fetchList() {
      try {
        const res = await api.schools({ page: this.page, page_size: 20, search: this.search });
        this.list = res.data.list; this.total = res.data.total;
      } catch (e) { console.error(e); }
    },
    openCreate() { this.editing = null; this.form = { name: "", code: "", contact_name: "", contact_phone: "", status: "enabled" }; this.showModal = true; },
    openEdit(row) { this.editing = row; this.form = { ...row }; this.showModal = true; },
    async doSave() {
      this.saving = true;
      try {
        if (this.editing) await api.schoolUpdate(this.editing.id, this.form);
        else await api.schoolCreate(this.form);
        this.showModal = false; this.fetchList();
      } catch (e) { alert(e.message); }
      finally { this.saving = false; }
    },
    async doDelete(row) {
      if (!confirm(`确定删除学校"${row.name}"？`)) return;
      try { await api.schoolDelete(row.id); this.fetchList(); } catch (e) { alert(e.message); }
    },
    fmtTime(ms) { return ms ? new Date(ms).toLocaleString("zh-CN") : "-"; },
  },
};
</script>
