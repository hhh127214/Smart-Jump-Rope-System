<template>
  <div>
    <div class="page-header">
      <h2>成绩详情</h2>
      <button class="btn btn-default" @click="$router.back()">返回</button>
    </div>
    <div v-if="score" class="card detail-section">
      <h3>基本信息</h3>
      <div class="info-grid">
        <div class="info-item"><span class="info-label">学生：</span><span class="info-value">{{ score.student_name }} ({{ score.student_no }})</span></div>
        <div class="info-item"><span class="info-label">班级：</span><span class="info-value">{{ score.class_name }}</span></div>
        <div class="info-item"><span class="info-label">考场：</span><span class="info-value">{{ score.venue_name }}</span></div>
        <div class="info-item"><span class="info-label">任务：</span><span class="info-value">{{ score.task_name || '-' }}</span></div>
        <div class="info-item"><span class="info-label">站位：</span><span class="info-value">{{ score.slot }}</span></div>
        <div class="info-item"><span class="info-label">最终次数：</span><span class="info-value"><strong>{{ score.final_count }}</strong></span></div>
        <div class="info-item"><span class="info-label">时长：</span><span class="info-value">{{ score.duration_sec }}秒</span></div>
        <div class="info-item"><span class="info-label">测试时间：</span><span class="info-value">{{ fmtTime(score.tested_at_ms) }}</span></div>
        <div class="info-item"><span class="info-label">审核状态：</span><span class="info-value">
          <span :class="reviewTag(score.review_status)">{{ score.review_status || '未审核' }}</span>
        </span></div>
      </div>
    </div>

    <div v-if="slots && slots.length" class="card detail-section">
      <h3>5站位详情</h3>
      <div class="table-wrap">
        <table>
          <thead><tr><th>站位</th><th>学生</th><th>计数</th></tr></thead>
          <tbody>
            <tr v-for="s in slots" :key="s.id">
              <td>{{ s.slot }}</td><td>{{ s.student_name || s.user_id }}</td><td>{{ s.count }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card detail-section">
      <h3>审核操作</h3>
      <div class="form-row">
        <button class="btn btn-success" @click="doReview('approved')">确认有效</button>
        <button class="btn btn-danger" @click="doReview('rejected')">标记异常</button>
      </div>
      <div v-if="msg" class="message" :class="msgType">{{ msg }}</div>
    </div>
  </div>
</template>

<script>
import { api } from "../api.js";

export default {
  data() {
    return { score: null, slots: [], exceptions: [], msg: "", msgType: "message-success" };
  },
  async mounted() {
    try {
      const res = await api.scoreDetail(this.$route.params.id);
      this.score = res.data.score;
      this.slots = res.data.slots || [];
      this.exceptions = res.data.exceptions || [];
    } catch (e) { console.error(e); }
  },
  methods: {
    async doReview(status) {
      try {
        await api.scoreReview(this.$route.params.id, { review_status: status });
        this.msg = status === "approved" ? "成绩已确认有效" : "已标记为异常";
        this.msgType = status === "approved" ? "message-success" : "message-error";
        const res = await api.scoreDetail(this.$route.params.id);
        this.score = res.data.score;
      } catch (e) { alert(e.message); }
    },
    reviewTag(s) {
      if (s === "approved") return "tag tag-green";
      if (s === "rejected") return "tag tag-red";
      return "tag tag-gray";
    },
    fmtTime(ms) { return ms ? new Date(ms).toLocaleString("zh-CN") : "-"; },
  },
};
</script>
