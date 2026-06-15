import { createApp } from "https://unpkg.com/vue@3/dist/vue.esm-browser.prod.js";

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
  if (!raw) return "JR";
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

createApp({
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
    phaseTitle() {
      const map = {
        idle: "等待入场",
        confirming_info: "人脸识别中",
        binding: "站位绑定中",
        ready: "准备开始",
        countdown: "5 秒倒计时",
        running: "正在计数",
        result: "成绩展示",
      };
      return map[this.displayPhase] || "自动测试中";
    },
    phaseSubtitle() {
      if (this.displayPhase === "idle") return "摄像头接入后自动进入识别流程";
      if (this.displayPhase === "confirming_info") return `已识别 ${this.recognizedCount}/5 个站位`;
      if (this.displayPhase === "binding") return `请站位 ${this.flow.promptSlot || "-"} 完成指定动作`;
      if (this.displayPhase === "ready") return "五个站位绑定完成，准备统一起跳";
      if (this.displayPhase === "countdown") return "请全体同学做好准备";
      if (this.displayPhase === "running") return "系统正在实时统计五个站位的跳绳次数";
      if (this.displayPhase === "result") return "本轮测试已结束，成绩自动保存";
      return "系统正在工作中";
    },
    heroPrompt() {
      if (this.ui.countdownValue > 0) return "READY";
      if (this.flow.phase === "idle") return "AI CAMERA ONLINE";
      if (this.flow.phase === "confirming_info") return "FACE MATCHING";
      if (this.flow.phase === "binding") return `BIND SLOT ${this.flow.promptSlot || ""}`.trim();
      if (this.flow.phase === "ready") return "ALL LOCKED";
      if (this.flow.phase === "running") return "ROPE COUNTING";
      if (this.flow.phase === "result") return "RESULT SAVED";
      return "JUMP ROPE";
    },
    stageSteps() {
      const active = {
        idle: 0,
        confirming_info: 1,
        binding: 2,
        ready: 3,
        countdown: 3,
        running: 4,
        result: 5,
      }[this.displayPhase] || 0;
      return [
        { key: "cam", label: "摄像头" },
        { key: "face", label: "识别" },
        { key: "bind", label: "绑定" },
        { key: "ready", label: "倒计时" },
        { key: "run", label: "计数" },
        { key: "done", label: "结果" },
      ].map((item, index) => ({
        ...item,
        done: active > index,
        active: active === index,
      }));
    },
    recognizedCount() {
      return this.stations.filter((item) => item.hasUser).length;
    },
    topRankingText() {
      if (!this.flow.ranking.length) return "等待测试开始";
      return this.flow.ranking
        .slice(0, 3)
        .map((item, index) => `TOP${index + 1} 站位${item.slot} · ${item.count}`)
        .join(" / ");
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
    stationStatus(slotNo, raw, tracking) {
      if (this.flow.phase === "idle") {
        return { label: "等待入位", className: "is-idle" };
      }
      if (!raw.user) {
        return { label: "等待识别", className: "is-empty" };
      }
      if (tracking === "OUT_OF_ROI") {
        return { label: "请回到站位", className: "is-alert" };
      }
      if (tracking === "OCCLUDED") {
        return { label: "识别遮挡", className: "is-alert" };
      }
      if (tracking === "TRACK_LOST") {
        return { label: "重新跟踪中", className: "is-alert" };
      }
      if (this.flow.phase === "confirming_info") {
        return { label: raw.confirmedInfo ? "身份完成" : "识别成功", className: "is-recognized" };
      }
      if (this.flow.phase === "binding") {
        if (this.flow.promptSlot === slotNo) return { label: "请做动作", className: "is-binding" };
        if (raw.confirmedPosition) return { label: "绑定完成", className: "is-bound" };
        return { label: "等待绑定", className: "is-waiting" };
      }
      if (this.flow.phase === "ready" || this.ui.countdownValue > 0) {
        return { label: "准备开始", className: "is-ready" };
      }
      if (this.flow.phase === "running") {
        return { label: "正在计数", className: "is-running" };
      }
      if (this.flow.phase === "result") {
        return { label: "最终成绩", className: "is-result" };
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
        this.ensureActionTimer("recognition", 900, async () => {
          await this.startRecognition();
        });
        return;
      }
      this.clearActionTimer("recognition");

      if (this.flow.phase === "confirming_info") {
        const next = this.flow.slots.find((item) => item.user && !item.confirmedInfo);
        if (next) {
          this.ui.message = `站位 ${next.slot} 身份识别完成，自动确认中`;
          this.ensureActionTimer(`confirm_${next.slot}`, 520, async () => {
            await this.confirmInfo(next.slot);
          });
        } else {
          this.ui.message = "五个站位识别完成，正在进入绑定环节";
        }
        return;
      }
      this.stations.forEach((station) => this.clearActionTimer(`confirm_${station.slot}`));

      if (this.flow.phase === "binding") {
        const slot = Number(this.flow.promptSlot || 0);
        if (slot > 0) {
          this.ui.message = `请站位 ${slot} 完成指定动作`;
          this.ensureActionTimer(`gesture_${slot}`, 900, async () => {
            await this.confirmGesture(slot);
          });
        }
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
  template: `
    <div class="screen-root">
      <div class="ambient ambient-a"></div>
      <div class="ambient ambient-b"></div>
      <div class="ambient ambient-c"></div>

      <div class="screen-shell">
        <header class="screen-top">
          <div class="brand-block">
            <div class="brand-eyebrow">UI DESIGN STYLE</div>
            <div class="brand-title-row">
              <h1 class="brand-title-cn">五人跳绳自动测试</h1>
              <div class="brand-title-en">Jump Rope Assessment</div>
            </div>
          </div>

          <div class="top-status">
            <div class="status-chip success">
              <span class="chip-dot"></span>
              <span>摄像头 {{ camera.connected ? "已连接" : "连接中" }}</span>
            </div>
            <div class="status-chip light">模式 {{ camera.mode }}</div>
            <div class="status-chip light">时间 {{ ui.nowText }}</div>
          </div>
        </header>

        <section class="hero-board">
          <div class="hero-decor hero-decor-left"></div>
          <div class="hero-decor hero-decor-right"></div>
          <div class="hero-copy">
            <div class="hero-kicker">{{ phaseTitle }}</div>
            <div class="hero-sub">{{ phaseSubtitle }}</div>
          </div>

          <div class="hero-core">
            <div class="core-glow"></div>
            <div class="core-pill">
              <div class="core-small">AUTO FLOW</div>
              <div class="core-main">{{ heroPrompt }}</div>
              <div class="core-desc">{{ ui.message }}</div>
            </div>
          </div>

          <div class="countdown-overlay" v-if="ui.countdownValue > 0">
            <div class="countdown-number">{{ ui.countdownValue }}</div>
          </div>
        </section>

        <section class="progress-strip">
          <div
            v-for="step in stageSteps"
            :key="step.key"
            class="progress-step"
            :class="{ active: step.active, done: step.done }"
          >
            <span class="step-bullet"></span>
            <span>{{ step.label }}</span>
          </div>
        </section>

        <section class="station-grid" :class="'phase-' + displayPhase">
          <article
            v-for="station in stations"
            :key="station.slot"
            class="station-card"
            :class="[station.statusClass, { highlighted: flow.promptSlot === station.slot && flow.phase === 'binding' }]"
            :style="cardStyle(station.colors)"
          >
            <div class="station-bg-lines"></div>

            <div class="station-head">
              <div class="slot-badge">0{{ station.slot }}</div>
              <div class="station-meta">
                <div class="station-name">{{ station.user.name || "等待识别" }}</div>
                <div class="station-class">{{ station.user.className || "固定站位" }}</div>
              </div>
              <div class="station-state">{{ station.statusLabel }}</div>
            </div>

            <div class="station-visual">
              <div class="portrait-wrap">
                <img class="portrait" :src="station.portrait" :alt="'站位' + station.slot + '头像'" />
              </div>
              <div class="sport-illustration">
                <img :src="station.icon" :alt="'站位' + station.slot + '插画'" />
              </div>
            </div>

            <div class="station-body">
              <div class="station-row">
                <span>姓名</span>
                <strong>{{ station.user.name || "等待同学入位" }}</strong>
              </div>
              <div class="station-row">
                <span>学号</span>
                <strong>{{ station.user.studentId || "--" }}</strong>
              </div>
              <div class="station-row">
                <span>绑定</span>
                <strong>{{ station.confirmedPosition ? "完成" : station.confirmedInfo ? "待动作" : "待识别" }}</strong>
              </div>
            </div>

            <div class="station-count">
              <div class="count-label">{{ displayPhase === "result" ? "最终成绩" : "当前次数" }}</div>
              <div class="count-value">{{ station.count }}</div>
            </div>
          </article>
        </section>

        <footer class="bottom-panel">
          <div class="bottom-card">
            <div class="bottom-key">测试时长</div>
            <div class="bottom-value">{{ fmtMMSS(flow.durationSec) }}</div>
          </div>
          <div class="bottom-card">
            <div class="bottom-key">剩余时间</div>
            <div class="bottom-value">{{ displayPhase === "running" ? fmtMMSS(flow.remainingSec) : ui.countdownValue > 0 ? fmtMMSS(ui.countdownValue) : '--:--' }}</div>
          </div>
          <div class="bottom-card long">
            <div class="bottom-key">实时排名</div>
            <div class="bottom-value small">{{ topRankingText }}</div>
          </div>
          <div class="bottom-card">
            <div class="bottom-key">当前轮次</div>
            <div class="bottom-value">{{ flow.runId || "WAITING" }}</div>
          </div>
        </footer>
      </div>
    </div>
  `,
}).mount("#app");
