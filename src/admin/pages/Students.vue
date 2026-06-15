<template>
  <div>
    <div class="page-header">
      <h2>学生管理</h2>
      <div class="page-header-actions">
        <button class="btn btn-primary" @click="openCreate">新增学生</button>
      </div>
    </div>
    <div class="card">
      <div class="form-row">
        <select v-model="classId" @change="fetchList" style="width:200px">
          <option value="">全部班级</option>
          <option v-for="c in classes" :key="c.id" :value="c.id">{{ c.school_name }} - {{ c.grade_name }} - {{ c.name }}</option>
        </select>
        <input v-model="search" placeholder="搜索姓名/学号..." @keyup.enter="fetchList" style="width:200px" />
        <button class="btn btn-primary btn-sm" @click="fetchList">搜索</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>学号</th><th>姓名</th><th>性别</th><th>班级</th><th>人脸状态</th><th>状态</th><th>创建时间</th><th style="width:140px">操作</th></tr></thead>
          <tbody>
            <tr v-for="row in list" :key="row.id">
              <td>{{ row.student_no }}</td>
              <td><a @click="$router.push(`/students/${row.id}`)" style="color:#1890ff;cursor:pointer">{{ row.name }}</a></td>
              <td>{{ row.gender }}</td><td>{{ row.class_name }}</td>
              <td><span :class="row.face_status === 'ready' ? 'tag tag-green' : 'tag tag-orange'">{{ row.face_status === 'ready' ? '已录入' : '待录入' }}</span></td>
              <td><span :class="row.status === 'active' ? 'tag tag-green' : 'tag tag-gray'">{{ row.status === 'active' ? '在读' : '停用' }}</span></td>
              <td>{{ fmtTime(row.created_at_ms) }}</td>
              <td>
                <button class="btn btn-default btn-sm" @click="openEdit(row)">编辑</button>
                <button class="btn btn-danger btn-sm" style="margin-left:4px" @click="doDelete(row)">停用</button>
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
        <h3>{{ editing ? '编辑学生' : '新增学生' }}</h3>
        <div class="form-group"><label>学号 *</label><input v-model="form.student_no" /></div>
        <div class="form-group"><label>姓名 *</label><input v-model="form.name" /></div>
        <div class="form-group"><label>性别</label><select v-model="form.gender"><option value="男">男</option><option value="女">女</option></select></div>
        <div class="form-group"><label>出生日期</label><input v-model="form.birth_date" type="date" /></div>
        <div class="form-group"><label>所属班级 *</label><select v-model="form.class_id"><option v-for="c in classes" :key="c.id" :value="c.id">{{ c.school_name }} - {{ c.grade_name }} - {{ c.name }}</option></select></div>
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
    return { list: [], total: 0, page: 1, search: "", classId: "", classes: [], showModal: false, editing: null, form: {}, saving: false };
  },
  async mounted() {
    const res = await api.classes({ page: 1, page_size: 200 });
    this.classes = res.data.list;
    if (this.$route.query.class_id) {
      this.classId = this.$route.query.class_id;
    }
    this.fetchList();
  },
  methods: {
    async fetchList() {
      try {
        const res = await api.students({ page: this.page, page_size: 20, search: this.search, class_id: this.classId });
        this.list = res.data.list; this.total = res.data.total;
      } catch (e) { console.error(e); }
    },
    openCreate() { this.editing = null; this.form = { student_no: "", name: "", gender: "男", birth_date: "", class_id: this.classes[0]?.id || "" }; this.showModal = true; },
    openEdit(row) {
      this.editing = row;
      this.form = {
        student_no: row.student_no, name: row.name, gender: row.gender,
        birth_date: row.birth_date || "", class_id: row.class_id,
      };
      this.showModal = true;
    },
    async doSave() {
      this.saving = true;
      try {
        if (this.editing) await api.studentUpdate(this.editing.id, this.form);
        else await api.studentCreate(this.form);
        this.showModal = false; this.fetchList();
      } catch (e) { alert(e.message); }
      finally { this.saving = false; }
    },
    async doDelete(row) {
      if (!confirm(`确定停用学生"${row.name}"？停用后历史成绩保留。`)) return;
      try { await api.studentDelete(row.id); this.fetchList(); } catch (e) { alert(e.message); }
    },
    fmtTime(ms) { return ms ? new Date(ms).toLocaleString("zh-CN") : "-"; },
  },
};
</script>
