<template>
  <router-view />
</template>

<script setup lang="ts">
</script>

<style>
:root {
  color-scheme: light;
  --app-bg:
    radial-gradient(circle at top left, rgba(96, 165, 250, 0.18), transparent 32%),
    radial-gradient(circle at top right, rgba(99, 102, 241, 0.16), transparent 26%),
    linear-gradient(180deg, #f8fbff 0%, #edf3fb 54%, #eaf1fa 100%);
  --surface-bg: rgba(255, 255, 255, 0.92);
  --surface-border: rgba(219, 234, 254, 0.92);
  --surface-shadow: 0 20px 50px rgba(15, 23, 42, 0.08);
  --surface-shadow-strong: 0 28px 72px rgba(15, 23, 42, 0.12);
  --text-primary: #0f172a;
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  font-family: "Noto Sans SC", "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: var(--app-bg);
  color: var(--text-primary);
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

button,
input,
textarea,
select {
  font: inherit;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    background 0.18s ease,
    color 0.18s ease,
    transform 0.18s ease,
    opacity 0.18s ease;
}

#app {
  min-height: 100vh;
}

::selection {
  background: rgba(29, 78, 216, 0.16);
  color: var(--text-primary);
}
</style>
