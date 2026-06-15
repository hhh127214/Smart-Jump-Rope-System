<template>
  <div>
    <div class="page-header">
      <h2>班级管理</h2>
      <button class="btn btn-primary" @click="openCreate">新增班级</button>
    </div>
    <div class="card">
      <div class="form-row">
        <select v-model="gradeId" @change="fetchList" style="width:200px">
          <option value="">全部年级</option>
          <option v-for="g in grades" :key="g.id" :value="g.id">{{ g.school_name }} - {{ g.name }}</option>
        </select>
        <input v-model="search" placeholder="搜索名称..." @keyup.enter="fetchList" style="width:200px" />
        <button class="btn btn-primary btn-sm" @click="fetchList">搜索</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>名称</th><th>所属年级</th><th>学校</th><th>班主任</th><th>学生数</th><th>状态</th><th>创建时间</th><th style="width:160px">操作</th></tr></thead>
          <tbody>
            <tr v-for="row in list" :key="row.id">
              <td>{{ row.name }}</td><td>{{ row.grade_name }}</td><td>{{ row.school_name }}</td><td>{{ row.teacher_name }}</td>
              <td>{{ row.student_count }}</td>
              <td><span :class="row.status === 'enabled' ? 'tag tag-green' : 'tag tag-gray'">{{ row.status === 'enabled' ? '启用' : '停用' }}</span></td>
              <td>{{ fmtTime(row.created_at_ms) }}</td>
              <td>
                <button class="btn btn-default btn-sm" @click="openEdit(row)">编辑</button>
                <button class="btn btn-primary btn-sm" style="margin-left:4px" @click="$router.push(`/students?class_id=${row.id}`)">学生</button>
                <button class="btn btn-danger btn-sm" style="margin-left:4px" @click="doDelete(row)">删除</button>
              </td>
            </tr>
            <tr v-if="!list.length"><td colspan="8" style="text-align:center;color:#999">暂无数据</td></tr>
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
        <h3>{{ editing ? '编辑班级' : '新增班级' }}</h3>
        <div class="form-group"><label>所属年级 *</label><select v-model="form.grade_id"><option v-for="g in grades" :key="g.id" :value="g.id">{{ g.school_name }} - {{ g.name }}</option></select></div>
        <div class="form-group"><label>名称 *</label><input v-model="form.name" /></div>
        <div class="form-group"><label>班主任</label><input v-model="form.teacher_name" /></div>
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
    return { list: [], total: 0, page: 1, search: "", gradeId: "", grades: [], showModal: false, editing: null, form: {}, saving: false };
  },
  async mounted() {
    const res = await api.grades({ page: 1, page_size: 200 });
    this.grades = res.data.list;
    this.fetchList();
  },
  methods: {
    async fetchList() {
      try {
        const res = await api.classes({ page: this.page, page_size: 20, search: this.search, grade_id: this.gradeId });
        this.list = res.data.list; this.total = res.data.total;
      } catch (e) { console.error(e); }
    },
    openCreate() { this.editing = null; this.form = { grade_id: this.grades[0]?.id || "", name: "", teacher_name: "", status: "enabled" }; this.showModal = true; },
    openEdit(row) { this.editing = row; this.form = { ...row }; this.showModal = true; },
    async doSave() {
      this.saving = true;
      try {
        if (this.editing) await api.classUpdate(this.editing.id, this.form);
        else await api.classCreate(this.form);
        this.showModal = false; this.fetchList();
      } catch (e) { alert(e.message); }
      finally { this.saving = false; }
    },
    async doDelete(row) {
      if (!confirm(`确定删除班级"${row.name}"？`)) return;
      try { await api.classDelete(row.id); this.fetchList(); } catch (e) { alert(e.message); }
    },
    fmtTime(ms) { return ms ? new Date(ms).toLocaleString("zh-CN") : "-"; },
  },
};
</script>
