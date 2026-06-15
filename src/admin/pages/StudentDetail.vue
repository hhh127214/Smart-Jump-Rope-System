<template>
  <div>
    <div class="page-header">
      <h2>学生详情</h2>
      <button class="btn btn-default" @click="$router.back()">返回</button>
    </div>
    <div v-if="student" class="card detail-section">
      <h3>基本信息</h3>
      <div class="info-grid">
        <div class="info-item"><span class="info-label">学号：</span><span class="info-value">{{ student.student_no }}</span></div>
        <div class="info-item"><span class="info-label">姓名：</span><span class="info-value">{{ student.name }}</span></div>
        <div class="info-item"><span class="info-label">性别：</span><span class="info-value">{{ student.gender }}</span></div>
        <div class="info-item"><span class="info-label">出生日期：</span><span class="info-value">{{ student.birth_date || '-' }}</span></div>
        <div class="info-item"><span class="info-label">学校：</span><span class="info-value">{{ student.school_name || '-' }}</span></div>
        <div class="info-item"><span class="info-label">年级：</span><span class="info-value">{{ student.grade_name || '-' }}</span></div>
        <div class="info-item"><span class="info-label">班级：</span><span class="info-value">{{ student.class_name }}</span></div>
        <div class="info-item"><span class="info-label">人脸状态：</span>
          <span :class="student.face_status === 'ready' ? 'tag tag-green' : 'tag tag-orange'">{{ student.face_status === 'ready' ? '已录入' : '待录入' }}</span>
        </div>
      </div>
    </div>

    <div class="card detail-section">
      <h3>历史成绩</h3>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Run ID</th><th>站位</th><th>次数</th><th>审核状态</th><th>测试时间</th></tr></thead>
          <tbody>
            <tr v-for="s in scores" :key="s.id">
              <td>{{ s.run_id }}</td><td>{{ s.slot }}</td><td>{{ s.final_count }}</td>
              <td><span :class="tagClass(s.review_status)">{{ s.review_status || '-' }}</span></td>
              <td>{{ fmtTime(s.tested_at_ms) }}</td>
            </tr>
            <tr v-if="!scores.length"><td colspan="5" style="text-align:center;color:#999">暂无成绩</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from "../api.js";

export default {
  data() {
    return { student: null, faces: [], scores: [] };
  },
  async mounted() {
    try {
      const res = await api.studentDetail(this.$route.params.id);
      this.student = res.data.student;
      this.faces = res.data.faces || [];
      this.scores = res.data.scores || [];
    } catch (e) { console.error(e); }
  },
  methods: {
    fmtTime(ms) { return ms ? new Date(ms).toLocaleString("zh-CN") : "-"; },
    tagClass(status) {
      if (status === "approved") return "tag tag-green";
      if (status === "rejected") return "tag tag-red";
      return "tag tag-gray";
    },
  },
};
</script>
