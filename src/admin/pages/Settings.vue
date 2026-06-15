<template>
  <div>
    <div class="page-header"><h2>系统设置</h2></div>
    <div v-if="msg" class="message" :class="msgType">{{ msg }}</div>
    <div class="card">
      <h3 style="margin-bottom:16px">考试参数</h3>
      <div class="form-row">
        <div class="form-group"><label>默认测试时长(秒)</label><input v-model.number="form.durationSec" type="number" /></div>
        <div class="form-group"><label>倒计时秒数</label><input v-model.number="form.countdownSec" type="number" /></div>
        <div class="form-group"><label>绑定动作</label><select v-model="form.bindingAction"><option value="wave">挥手</option><option value="jump">跳跃</option></select></div>
        <div class="form-group"><label>结果停留(秒)</label><input v-model.number="form.resultStaySec" type="number" /></div>
      </div>
    </div>
    <div class="card">
      <h3 style="margin-bottom:16px">业务规则</h3>
      <div class="form-row">
        <div class="form-group"><label>每组最大人数</label><input v-model.number="form.groupSize" type="number" /></div>
        <div class="form-group"><label>人脸质量最低分</label><input v-model.number="form.faceQualityMin" type="number" /></div>
        <div class="form-group"><label>设备离线阈值(秒)</label><input v-model.number="form.deviceOfflineThresholdSec" type="number" /></div>
      </div>
    </div>
    <button class="btn btn-primary" @click="doSave" :disabled="saving">{{ saving ? '保存中...' : '保存设置' }}</button>
  </div>
</template>

<script>
import { api } from "../api.js";

export default {
  data() {
    return {
      form: { durationSec: 60, countdownSec: 5, bindingAction: "wave", resultStaySec: 15, groupSize: 5, faceQualityMin: 80, deviceOfflineThresholdSec: 20 },
      msg: "", msgType: "message-success", saving: false,
    };
  },
  async mounted() {
    try {
      const res = await api.settings();
      const s = res.data;
      const ep = s.exam_params || {};
      const br = s.business_rules || {};
      this.form = { ...this.form, ...ep, ...br };
    } catch (e) { console.error(e); }
  },
  methods: {
    async doSave() {
      this.saving = true;
      try {
        await api.settingsUpdate({
          exam_params: { durationSec: this.form.durationSec, countdownSec: this.form.countdownSec, bindingAction: this.form.bindingAction, resultStaySec: this.form.resultStaySec },
          business_rules: { groupSize: this.form.groupSize, faceQualityMin: this.form.faceQualityMin, deviceOfflineThresholdSec: this.form.deviceOfflineThresholdSec, autoMarkExceptionScore: true, autoAddRetest: true },
        });
        this.msg = "设置已保存"; this.msgType = "message-success";
      } catch (e) { this.msg = e.message; this.msgType = "message-error"; }
      finally { this.saving = false; }
    },
  },
};
</script>
