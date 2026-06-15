<template>
  <div>
    <div class="page-header">
      <h2>年级管理</h2>
      <button class="btn btn-primary" @click="openCreate">新增年级</button>
    </div>
    <div class="card">
      <div class="form-row">
        <select v-model="schoolId" @change="fetchList" style="width:200px">
          <option value="">全部学校</option>
          <option v-for="s in schools" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>
        <input v-model="search" placeholder="搜索名称..." @keyup.enter="fetchList" style="width:200px" />
        <button class="btn btn-primary btn-sm" @click="fetchList">搜索</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>名称</th><th>所属学校</th><th>排序</th><th>状态</th><th>创建时间</th><th style="width:140px">操作</th></tr></thead>
          <tbody>
            <tr v-for="row in list" :key="row.id">
              <td>{{ row.name }}</td><td>{{ row.school_name }}</td><td>{{ row.sort_order }}</td>
              <td><span :class="row.status === 'enabled' ? 'tag tag-green' : 'tag tag-gray'">{{ row.status === 'enabled' ? '启用' : '停用' }}</span></td>
              <td>{{ fmtTime(row.created_at_ms) }}</td>
              <td>
                <button class="btn btn-default btn-sm" @click="openEdit(row)">编辑</button>
                <button class="btn btn-danger btn-sm" style="margin-left:4px" @click="doDelete(row)">删除</button>
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
        <h3>{{ editing ? '编辑年级' : '新增年级' }}</h3>
        <div class="form-group"><label>所属学校 *</label><select v-model="form.school_id"><option v-for="s in schools" :key="s.id" :value="s.id">{{ s.name }}</option></select></div>
        <div class="form-group"><label>名称 *</label><input v-model="form.name" /></div>
        <div class="form-group"><label>排序</label><input v-model.number="form.sort_order" type="number" /></div>
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
    return { list: [], total: 0, page: 1, search: "", schoolId: "", schools: [], showModal: false, editing: null, form: {}, saving: false };
  },
  async mounted() {
    const res = await api.schools({ page: 1, page_size: 100 });
    this.schools = res.data.list;
    this.fetchList();
  },
  methods: {
    async fetchList() {
      try {
        const res = await api.grades({ page: this.page, page_size: 20, search: this.search, school_id: this.schoolId });
        this.list = res.data.list; this.total = res.data.total;
      } catch (e) { console.error(e); }
    },
    openCreate() { this.editing = null; this.form = { school_id: this.schools[0]?.id || "", name: "", sort_order: 0, status: "enabled" }; this.showModal = true; },
    openEdit(row) { this.editing = row; this.form = { ...row }; this.showModal = true; },
    async doSave() {
      this.saving = true;
      try {
        if (this.editing) await api.gradeUpdate(this.editing.id, this.form);
        else await api.gradeCreate(this.form);
        this.showModal = false; this.fetchList();
      } catch (e) { alert(e.message); }
      finally { this.saving = false; }
    },
    async doDelete(row) {
      if (!confirm(`确定删除年级"${row.name}"？`)) return;
      try { await api.gradeDelete(row.id); this.fetchList(); } catch (e) { alert(e.message); }
    },
    fmtTime(ms) { return ms ? new Date(ms).toLocaleString("zh-CN") : "-"; },
  },
};
</script>
