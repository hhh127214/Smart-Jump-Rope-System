<template>
  <div class="dashboard-page">
    <section class="dashboard-hero">
      <div class="dashboard-hero-main">
        <div class="dashboard-hero-head">
          <div>
            <div class="dashboard-eyebrow">运营总览</div>
            <h2 class="dashboard-headline">跳绳测试大数据</h2>
            <p class="dashboard-subline">
              实时监控各学校测试进展，今日已完成 <strong>{{ stats.todayTestCount || 0 }}</strong> 人次测试，
              累计测试 <strong>{{ stats.totalTestCount || 0 }}</strong> 人次，在线设备 <strong>{{ stats.onlineDeviceCount || 0 }}</strong> 台。
            </p>
          </div>
          <div class="dashboard-hero-actions">
            <button class="btn btn-primary btn-sm" @click="refresh">刷新数据</button>
          </div>
        </div>
        <div class="dashboard-chart">
          <div class="dashboard-chart-grid">
            <svg class="dashboard-chart-line" viewBox="0 0 600 180" preserveAspectRatio="none">
              <defs>
                <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="rgba(239,253,95,0.45)" />
                  <stop offset="100%" stop-color="rgba(239,253,95,0.04)" />
                </linearGradient>
              </defs>
              <path
                v-if="trendPath"
                :d="trendPath"
                fill="url(#chartGrad)"
                stroke="rgba(239,253,95,0.7)"
                stroke-width="2.5"
              />
            </svg>
            <div class="dashboard-chart-tip" v-if="stats.todayTestCount > 0">
              <strong>{{ stats.todayTestCount }}</strong>
              <span>今日测试人次</span>
            </div>
          </div>
          <div class="dashboard-chart-axis">
            <span v-for="d in trendDays" :key="d.label">{{ d.label }}</span>
          </div>
        </div>
      </div>

      <div class="dashboard-hero-side">
        <h3 class="dashboard-panel-title" style="margin-bottom:18px">系统运行状态</h3>
        <div class="dashboard-server-card">
          <div class="dashboard-server-top">
            <span class="dashboard-server-name">数据服务</span>
            <span class="dashboard-server-status running">运行中</span>
          </div>
          <div class="dashboard-server-meta">数据记录总数：{{ ((stats.schoolCount || 0) + (stats.studentCount || 0) + (stats.totalTestCount || 0)).toLocaleString() }} 条</div>
          <div class="dashboard-server-metrics">
            <div class="dashboard-server-metric">
              <strong>{{ stats.schoolCount || 0 }}</strong>
              <span>学校数</span>
            </div>
            <div class="dashboard-server-metric">
              <strong>{{ stats.studentCount || 0 }}</strong>
              <span>学生数</span>
            </div>
            <div class="dashboard-server-metric">
              <strong>{{ stats.onlineDeviceCount || 0 }}/{{ (stats.onlineDeviceCount || 0) + (stats.offlineDeviceCount || 0) }}</strong>
              <span>在线设备</span>
            </div>
          </div>
        </div>
        <div class="dashboard-server-card">
          <div class="dashboard-server-top">
            <span class="dashboard-server-name">异常监控</span>
            <span class="dashboard-server-status" :class="stats.pendingExceptionCount > 0 ? 'stopped' : 'running'">
              {{ stats.pendingExceptionCount > 0 ? '需处理' : '正常' }}
            </span>
          </div>
          <div class="dashboard-server-meta">待处理异常 {{ stats.pendingExceptionCount || 0 }} 条</div>
          <div class="dashboard-server-metrics">
            <div class="dashboard-server-metric">
              <strong>{{ stats.totalTestCount || 0 }}</strong>
              <span>累计测试</span>
            </div>
            <div class="dashboard-server-metric">
              <strong>{{ stats.pendingExceptionCount || 0 }}</strong>
              <span>待处理异常</span>
            </div>
            <div class="dashboard-server-metric">
              <strong>{{ (stats.recentRuns || []).length }}</strong>
              <span>最近场次</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="dashboard-grid">
      <div class="dashboard-panel">
        <div class="dashboard-panel-head">
          <div>
            <div class="dashboard-panel-title">最近测试记录</div>
            <div class="dashboard-panel-subtitle">最近完成的 {{ (stats.recentRuns || []).length }} 次测试场次</div>
          </div>
          <button class="btn btn-default btn-sm" @click="$router.push('/scores')">查看全部</button>
        </div>
        <div class="dashboard-activity-list">
          <div
            v-for="r in recentList"
            :key="r.run_id"
            class="activity-item"
            @click="$router.push('/scores')"
            style="cursor:pointer"
          >
            <div class="activity-item-main">
              <div class="activity-item-title">{{ r.venue_name || '考场 ' + r.venue_id }}</div>
              <div class="activity-item-meta">Run ID: {{ r.run_id }} · 时长 {{ r.duration_sec }}s</div>
            </div>
            <span style="color:rgba(34,38,56,0.6);font-size:13px;font-weight:700">{{ fmtTime(r.started_at_ms) }}</span>
          </div>
          <div v-if="!recentList.length" class="dashboard-empty">暂无测试记录，请发布任务后开始测试</div>
        </div>
      </div>

      <div class="dashboard-panel-dark">
        <div class="dashboard-panel-head">
          <div>
            <div class="dashboard-panel-title" style="color:#e4ffee">近 7 天趋势</div>
            <div class="dashboard-panel-subtitle" style="color:rgba(228,255,238,0.5)">
              累计 {{ trendTotal }} 场测试
            </div>
          </div>
        </div>
        <div class="dashboard-service-list">
          <div
            v-for="d in trendData"
            :key="d.date"
            class="service-item"
          >
            <div class="service-item-main">
              <div class="service-item-title" style="color:#e4ffee">{{ fmtTrendDate(d.date) }}</div>
              <div class="service-item-meta" style="color:rgba(228,255,238,0.5)">
                当日 {{ d.count }} 场 · {{ percentBar(d.count) }}
              </div>
            </div>
            <span style="color:#f6f76c;font-size:22px;font-weight:900">{{ d.count }}</span>
          </div>
          <div v-if="!trendData.length" class="dashboard-empty" style="color:rgba(228,255,238,0.4)">暂无趋势数据</div>
        </div>
      </div>
    </section>

    <section>
      <div class="card">
        <div class="dashboard-panel-head" style="margin-bottom:18px">
          <div>
            <div class="dashboard-panel-title">数据概览</div>
            <div class="dashboard-panel-subtitle">当前系统统计快照</div>
          </div>
        </div>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value">{{ stats.schoolCount || 0 }}</div>
            <div class="stat-label">学校总数</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.studentCount || 0 }}</div>
            <div class="stat-label">学生总数</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.todayTestCount || 0 }}</div>
            <div class="stat-label">今日测试人次</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.totalTestCount || 0 }}</div>
            <div class="stat-label">累计测试人次</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.onlineDeviceCount || 0 }} / {{ (stats.onlineDeviceCount || 0) + (stats.offlineDeviceCount || 0) }}</div>
            <div class="stat-label">在线 / 离线设备</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ stats.pendingExceptionCount || 0 }}</div>
            <div class="stat-label">待处理异常</div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { api } from "../api.js";

export default {
  data() {
    return {
      stats: {},
      trendData: [],
    };
  },
  computed: {
    recentList() {
      return (this.stats.recentRuns || []).slice(0, 5);
    },
    trendTotal() {
      return this.trendData.reduce((sum, d) => sum + d.count, 0);
    },
    trendDays() {
      return this.trendData.map((d) => {
        const date = new Date(d.date);
        return { label: `${date.getMonth() + 1}/${date.getDate()}` };
      });
    },
    trendPath() {
      if (!this.trendData.length) return "";
      const maxCount = Math.max(...this.trendData.map((d) => d.count), 1);
      const w = 600;
      const h = 180;
      const pad = 0;
      const n = this.trendData.length;
      const stepX = (w - pad * 2) / Math.max(n - 1, 1);

      const points = this.trendData.map((d, i) => {
        const x = pad + i * stepX;
        const y = h - pad - (d.count / maxCount) * (h - pad * 2 - 16);
        return [x, y];
      });

      const first = points[0];
      const last = points[points.length - 1];
      const line = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p[0]} ${p[1]}`).join(" ");
      return `${line} L ${last[0]} ${h} L ${first[0]} ${h} Z`;
    },
  },
  async mounted() {
    await this.refresh();
  },
  methods: {
    async refresh() {
      try {
        const [statsRes, trendRes] = await Promise.all([
          api.dashboardStats(),
          api.dashboardTrend(7),
        ]);
        this.stats = statsRes.data;
        this.trendData = trendRes.data || [];
      } catch (e) {
        console.error(e);
      }
    },
    fmtTime(ms) {
      if (!ms) return "-";
      const d = new Date(ms);
      const hh = String(d.getHours()).padStart(2, "0");
      const mm = String(d.getMinutes()).padStart(2, "0");
      return `${hh}:${mm}`;
    },
    fmtTrendDate(ts) {
      const d = new Date(ts);
      const m = d.getMonth() + 1;
      const day = d.getDate();
      const weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
      return `${m}月${day}日 ${weekdays[d.getDay()]}`;
    },
    percentBar(count) {
      const max = Math.max(...this.trendData.map((d) => d.count), 1);
      const pct = Math.round((count / max) * 100);
      const filled = Math.round(pct / 5);
      return "▮".repeat(Math.max(filled, 1)) + "▯".repeat(Math.max(20 - filled, 0));
    },
  },
};
</script>
