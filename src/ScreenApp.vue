<script>
const PALETTE = [
  ["#ff8f8f", "#ffcb7d"],
  ["#7be7b8", "#68d9ff"],
  ["#ffb5ff", "#ffdc6e"],
  ["#8de2ff", "#7ed6a1"],
  ["#ffd08a", "#ff9bd6"],
];

function fmtMMSS(sec) {
  const safe = Math.max(0, Math.floor(Number(sec) || 0));
  const mm = String(Math.floor(safe / 60)).padStart(2, "0");
  const ss = String(safe % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}

async function apiFetch(path, options = {}) {
  const res = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const text = await res.text();
  let json = {};
  try {
    json = text ? JSON.parse(text) : {};
  } catch {
    json = {};
  }
  if (!res.ok) {
    const err = new Error(json?.error || `HTTP_${res.status}`);
    err.status = res.status;
    err.body = json;
    throw err;
  }
  return json;
}

function initialsOf(name) {
  const raw = typeof name === "string" ? name.trim() : "";
  if (!raw) return "待识";
  return raw.length >= 2 ? raw.slice(-2) : raw.slice(0, 1);
}

function makePortrait(name, index) {
  const tone = PALETTE[index % PALETTE.length];
  const label = initialsOf(name);
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="${tone[0]}"/>
          <stop offset="100%" stop-color="${tone[1]}"/>
        </linearGradient>
      </defs>
      <rect width="160" height="160" rx="34" fill="url(#bg)"/>
      <circle cx="80" cy="58" r="26" fill="rgba(255,255,255,0.88)"/>
      <path d="M34 136c7-28 29-44 46-44s39 16 46 44" fill="rgba(255,255,255,0.88)"/>
      <circle cx="122" cy="34" r="12" fill="rgba(255,255,255,0.28)"/>
      <circle cx="42" cy="34" r="7" fill="rgba(255,255,255,0.18)"/>
      <text x="80" y="148" text-anchor="middle" font-size="20" font-weight="800" fill="rgba(33,35,44,0.64)" font-family="Arial, sans-serif">${label}</text>
    </svg>
  `;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function makeSportIcon(index) {
  const shapes = [
    '<path d="M60 26l14 10-14 11-10 18 17 7 8-17 15-4-2-15-13-7z" fill="rgba(39,42,57,0.86)"/>',
    '<path d="M44 70c6-23 24-38 45-38 17 0 27 6 34 17l-10 6c-5-7-12-11-24-11-15 0-27 10-31 28z" fill="rgba(39,42,57,0.86)"/>',
    '<path d="M44 36h42l16 30-15 34H46l-12-24z" fill="rgba(39,42,57,0.86)"/>',
    '<circle cx="60" cy="40" r="12" fill="rgba(39,42,57,0.86)"/><path d="M58 52l20 15 18 34H79L66 76 49 96H34l20-28z" fill="rgba(39,42,57,0.86)"/>',
    '<path d="M32 92c12-35 37-58 67-58 16 0 28 7 37 16l-9 8c-8-7-16-12-28-12-23 0-43 18-53 46z" fill="rgba(39,42,57,0.86)"/>',
  ];
  const tone = PALETTE[index % PALETTE.length];
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 120">
      <defs>
        <linearGradient id="tone" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="${tone[0]}"/>
          <stop offset="100%" stop-color="${tone[1]}"/>
        </linearGradient>
      </defs>
      <rect x="10" y="10" width="140" height="100" rx="26" fill="url(#tone)" opacity="0.26"/>
      <circle cx="126" cy="35" r="18" fill="rgba(255,255,255,0.5)"/>
      ${shapes[index % shapes.length]}
    </svg>
  `;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

export default {
  data() {
    return {
      camera: {
        mode: "SIM",
        index: 0,
        connected: false,
      },
      flow: {
        phase: "idle",
        promptSlot: 0,
        durationSec: 30,
        remainingSec: 0,
        runId: "",
        counts: [0, 0, 0, 0, 0],
        ranking: [],
        slotStatus: ["OK", "OK", "OK", "OK", "OK"],
        slots: [],
      },
      ui: {
        message: "正在连接设备",
        nowText: "",
        pollId: 0,
        clockId: 0,
        actionTimers: {},
        countdownId: 0,
        countdownValue: 0,
        startingTest: false,
      },
    };
  },
  computed: {
    displayPhase() {
      if (this.ui.countdownValue > 0) return "countdown";
      return this.flow.phase || "idle";
    },
    recognizedCount() {
      return this.stations.filter((item) => item.hasUser).length;
    },
    boundCount() {
      return (this.flow.slots || []).filter((s) => s.confirmedPosition).length;
    },
    topRankingText() {
      if (!this.flow.ranking.length) return "等待测试开始";
      return this.flow.ranking
        .slice(0, 3)
        .map((item, index) => `第${index + 1}名 站位${item.slot} · ${item.count}`)
        .join(" / ");
    },
    showBindingOverlay() {
      return this.flow.phase === "binding";
    },
    showCountdownOverlay() {
      return Number(this.ui.countdownValue || 0) > 0;
    },
    stations() {
      return Array.from({ length: 5 }, (_, index) => {
        const slotNo = index + 1;
        const raw = (this.flow.slots || []).find((item) => Number(item.slot) === slotNo) || {};
        const user = raw.user || {};
        const colors = PALETTE[index % PALETTE.length];
        const portrait = makePortrait(user.name || `站位${slotNo}`, index);
        const icon = makeSportIcon(index);
        const count = Number((this.flow.counts || [])[index] || 0);
        const tracking = String((this.flow.slotStatus || [])[index] || "OK");
        const statusInfo = this.stationStatus(slotNo, raw, tracking);
        return {
          slot: slotNo,
          user,
          hasUser: Boolean(user && user.name),
          count,
          portrait,
          icon,
          colors,
          tracking,
          confirmedInfo: Boolean(raw.confirmedInfo),
          confirmedPosition: Boolean(raw.confirmedPosition),
          statusLabel: statusInfo.label,
          statusClass: statusInfo.className,
        };
      });
    },
  },
  methods: {
    fmtMMSS,
    updateClock() {
      const now = new Date();
      const hh = String(now.getHours()).padStart(2, "0");
      const mm = String(now.getMinutes()).padStart(2, "0");
      const ss = String(now.getSeconds()).padStart(2, "0");
      this.ui.nowText = `${hh}:${mm}:${ss}`;
    },
    stationStatus(_slotNo, raw, tracking) {
      if (this.flow.phase === "idle") {
        return { label: "准备中", className: "is-idle" };
      }
      if (!raw.user) {
        return { label: "等待入位", className: "is-idle" };
      }
      if (tracking === "OUT_OF_ROI") {
        return { label: "请就位哦", className: "is-alert" };
      }
      if (tracking === "OCCLUDED") {
        return { label: "有点挡到了", className: "is-alert" };
      }
      if (tracking === "TRACK_LOST") {
        return { label: "正在找你", className: "is-alert" };
      }
      if (this.flow.phase === "confirming_info") {
        return { label: raw.confirmedInfo ? "认出你啦" : "识别中...", className: raw.confirmedInfo ? "is-bound" : "is-binding" };
      }
      if (this.flow.phase === "binding") {
        if (raw.confirmedPosition) return { label: "绑定完成", className: "is-bound" };
        return { label: "做动作中", className: "is-binding" };
      }
      if (this.flow.phase === "ready" || this.ui.countdownValue > 0) {
        return { label: "准备起跳", className: "is-ready" };
      }
      if (this.flow.phase === "running") {
        return { label: "计数中", className: "is-running" };
      }
      if (this.flow.phase === "result") {
        return { label: "本轮完成", className: "is-result" };
      }
      return { label: "已就绪", className: "is-ready" };
    },
    cardStyle(colors) {
      return {
        "--tone-a": colors[0],
        "--tone-b": colors[1],
      };
    },
    ensureActionTimer(key, delay, fn) {
      if (this.ui.actionTimers[key]) return;
      this.ui.actionTimers[key] = window.setTimeout(async () => {
        this.clearActionTimer(key);
        await fn();
      }, delay);
    },
    clearActionTimer(key) {
      if (!this.ui.actionTimers[key]) return;
      window.clearTimeout(this.ui.actionTimers[key]);
      this.ui.actionTimers[key] = 0;
    },
    clearAllActionTimers() {
      Object.keys(this.ui.actionTimers).forEach((key) => this.clearActionTimer(key));
    },
    cancelCountdown() {
      if (this.ui.countdownId) {
        window.clearInterval(this.ui.countdownId);
        this.ui.countdownId = 0;
      }
      this.ui.countdownValue = 0;
      this.ui.startingTest = false;
    },
    applyFlowState(metrics = {}) {
      this.flow.phase = metrics.phase || this.flow.phase;
      this.flow.runId = metrics.runId || this.flow.runId || "";
      this.flow.durationSec = Number(metrics.durationSec || this.flow.durationSec || 30);
      this.flow.remainingSec = Number(metrics.remainingSec || 0);
      this.flow.promptSlot = Number(metrics.promptSlot || 0);
      this.flow.counts = Array.isArray(metrics.counts) ? metrics.counts : this.flow.counts;
      this.flow.ranking = Array.isArray(metrics.ranking) ? metrics.ranking : this.flow.ranking;
      this.flow.slotStatus = Array.isArray(metrics.slotStatus) ? metrics.slotStatus : this.flow.slotStatus;
      if (Array.isArray(metrics.slots)) this.flow.slots = metrics.slots;
    },
    async loadCameraConfig() {
      try {
        const json = await apiFetch("/api/camera/config", { method: "GET" });
        const config = json?.config || {};
        this.camera.mode = String(config.mode || "SIM");
        this.camera.index = Number(config.index || 0);
        this.camera.connected = true;
      } catch {
        this.camera.connected = false;
      }
    },
    async refreshMetrics() {
      try {
        const metrics = await apiFetch("/api/test/metrics", { method: "GET" });
        this.applyFlowState(metrics);
        this.camera.connected = true;
        this.driveAutomation();
      } catch {
        this.camera.connected = false;
        this.ui.message = "摄像头连接异常，请检查服务";
      }
    },
    async resetSystem() {
      try {
        const json = await apiFetch("/api/system/reset", { method: "POST", body: JSON.stringify({}) });
        if (json?.state) this.applyFlowState(json.state);
      } catch {
        this.ui.message = "系统重置失败";
      }
    },
    async startRecognition() {
      try {
        this.ui.message = "正在自动识别五个站位";
        const json = await apiFetch("/api/recognition/start", { method: "POST", body: JSON.stringify({}) });
        this.flow.phase = "confirming_info";
        this.flow.promptSlot = 0;
        this.flow.remainingSec = 0;
        this.flow.runId = "";
        this.flow.counts = [0, 0, 0, 0, 0];
        this.flow.slotStatus = ["OK", "OK", "OK", "OK", "OK"];
        this.flow.ranking = [];
        this.flow.slots = Array.isArray(json?.slots) ? json.slots : [];
      } catch {
        this.ui.message = "识别启动失败";
      }
    },
    async confirmInfo(slot) {
      try {
        const json = await apiFetch("/api/slots/confirm_info", {
          method: "POST",
          body: JSON.stringify({ slot, confirmed: true }),
        });
        if (json?.state) this.applyFlowState(json.state);
      } catch {
        this.ui.message = `站位 ${slot} 信息确认失败`;
      }
    },
    async confirmGesture(slot) {
      try {
        const json = await apiFetch("/api/binding/gesture", {
          method: "POST",
          body: JSON.stringify({ slot }),
        });
        if (json?.state) this.applyFlowState(json.state);
      } catch (err) {
        if (err?.body?.promptSlot) {
          this.ui.message = `请等待站位 ${err.body.promptSlot} 先完成动作`;
          return;
        }
        this.ui.message = `站位 ${slot} 绑定失败`;
      }
    },
    async beginTest() {
      if (this.ui.startingTest) return;
      this.ui.startingTest = true;
      try {
        await apiFetch("/api/test/start", {
          method: "POST",
          body: JSON.stringify({ durationSec: this.flow.durationSec || 30 }),
        });
        await this.refreshMetrics();
        this.ui.message = "测试开始，系统正在计数";
      } catch {
        this.ui.message = "测试启动失败";
      } finally {
        this.ui.startingTest = false;
      }
    },
    async beginCountdown() {
      if (this.ui.countdownId || this.flow.phase !== "ready") return;
      this.ui.countdownValue = 5;
      this.ui.message = "全部绑定完成，5 秒后开始";
      this.ui.countdownId = window.setInterval(async () => {
        if (this.flow.phase !== "ready") {
          this.cancelCountdown();
          return;
        }
        this.ui.countdownValue -= 1;
        if (this.ui.countdownValue <= 0) {
          this.cancelCountdown();
          await this.beginTest();
        }
      }, 1000);
    },
    async driveAutomation() {
      if (this.flow.phase !== "ready") {
        this.cancelCountdown();
      }

      if (this.flow.phase === "idle") {
        this.ensureActionTimer("recognition", 5000, async () => {
          await this.startRecognition();
        });
        return;
      }
      this.clearActionTimer("recognition");

      if (this.flow.phase === "confirming_info") {
        const unconfirmed = this.flow.slots.filter((item) => item.user && !item.confirmedInfo);
        if (unconfirmed.length) {
          this.ui.message = `人脸识别中 ${this.recognizedCount}/5`;
          unconfirmed.forEach((item) => {
            this.ensureActionTimer(`confirm_${item.slot}`, 1500, async () => {
              await this.confirmInfo(item.slot);
            });
          });
        } else {
          this.ui.message = "全部站位识别完成，进入绑定";
        }
        return;
      }
      this.stations.forEach((station) => this.clearActionTimer(`confirm_${station.slot}`));

      if (this.flow.phase === "binding") {
        this.ui.message = "请所有同学举起右手完成手势绑定";
        const unbound = this.flow.slots.filter((item) => item.user && !item.confirmedPosition);
        unbound.forEach((item) => {
          this.ensureActionTimer(`gesture_${item.slot}`, 2000, async () => {
            await this.confirmGesture(item.slot);
          });
        });
        return;
      }
      this.stations.forEach((station) => this.clearActionTimer(`gesture_${station.slot}`));

      if (this.flow.phase === "ready") {
        await this.beginCountdown();
        return;
      }

      if (this.flow.phase === "running") {
        this.ui.message = "五个站位实时计数中";
        return;
      }

      if (this.flow.phase === "result") {
        this.ui.message = "本轮成绩展示中，即将进入下一组";
        this.ensureActionTimer("resetAfterResult", 9000, async () => {
          await this.resetSystem();
          await this.refreshMetrics();
        });
      } else {
        this.clearActionTimer("resetAfterResult");
      }
    },
  },
  mounted() {
    this.updateClock();
    this.ui.clockId = window.setInterval(() => this.updateClock(), 1000);
    this.loadCameraConfig();
    this.refreshMetrics();
    this.ui.pollId = window.setInterval(() => this.refreshMetrics(), 280);
  },
  beforeUnmount() {
    if (this.ui.pollId) window.clearInterval(this.ui.pollId);
    if (this.ui.clockId) window.clearInterval(this.ui.clockId);
    this.clearAllActionTimers();
    this.cancelCountdown();
  },
};
</script>

<template>
  <div class="screen-root" :class="'phase-' + flow.phase">
    <div class="ambient ambient-a"></div>
    <div class="ambient ambient-b"></div>
    <div class="ambient ambient-c"></div>

    <div class="screen-shell">
      <section class="station-grid" :class="'phase-' + displayPhase">
        <article
          v-for="station in stations"
          :key="station.slot"
          class="station-card"
          :class="[station.statusClass]"
          :style="cardStyle(station.colors)"
        >
          <div class="station-bg-lines"></div>

          <div class="station-head">
            <div class="slot-badge">站位 {{ station.slot }}</div>
            <div class="station-state">{{ station.statusLabel }}</div>
          </div>

          <div class="station-portrait-wrap">
            <div class="portrait-wrap">
              <img class="portrait" :src="station.portrait" :alt="'站位' + station.slot + '头像'" />
            </div>
          </div>

          <div class="station-info">
            <div class="station-name">{{ station.user.name || "等待识别" }}</div>
            <div class="station-student-id">{{ station.user.studentId || "--" }}</div>
          </div>

          <div class="station-count">
            <div class="count-label">{{ displayPhase === "result" ? "最终成绩" : "当前次数" }}</div>
            <div class="count-value">{{ station.count }}</div>
          </div>
        </article>
      </section>

    </div>

    <div v-if="showBindingOverlay || showCountdownOverlay" class="center-stage-overlay">
      <div v-if="showBindingOverlay" class="binding-stage-card">
        <div class="overlay-tag">站位绑定</div>
        <div class="binding-stage-number">{{ boundCount }}/5 已完成</div>
        <div class="overlay-text">请所有同学举起右手完成手势绑定</div>
      </div>

      <div v-else class="countdown-stage-card">
        <div class="overlay-tag">统一准备起跳</div>
        <div class="countdown-stage-number">{{ ui.countdownValue }}</div>
        <div class="overlay-text">请全体同学保持准备姿态</div>
      </div>
    </div>
  </div>
</template>
