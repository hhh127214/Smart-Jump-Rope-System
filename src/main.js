import { createApp } from "vue";
import ScreenApp from "./ScreenApp.vue";
import "./screen.css";

function normalizePath() {
  const { pathname, search, hash } = window.location;

  if (pathname !== "/" && !pathname.startsWith("/screen")) {
    window.history.replaceState({}, "", `/screen${search}${hash}`);
  }
}

normalizePath();
createApp(ScreenApp).mount("#app");
