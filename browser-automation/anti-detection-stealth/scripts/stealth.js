// stealth.js — Hermes 反浏览器指纹核心 (v1.0)
// 目的: 隐藏 CDP/navigator.webdriver 特征, 避免被 bot.sannysoft / fingerprintjs / Cloudflare 拦
// 通过 CDP `Page.addScriptToEvaluateOnNewDocument` 注入, 每个新 tab/page 自动执行
// 兼容 Chrome 148+
//
// 实测 10/10 (2026-06-05): webdriver=false / plugins=3 / languages>=2 / chrome.runtime=object /
//   stealth_injected=true / WebGL vendor=Google Inc.(Apple) / WebGL renderer=ANGLE(...)/
//   permissions=ok / cdc keys=0
//
// 触发词: "stealth 注入" / "反指纹跑分" / "Page.addScriptToEvaluateOnNewDocument"
//         "chrome 148 event frame 坑" / "webdriver false 还能识别吗"

(function () {
  'use strict';

  // ── 1. navigator.webdriver (CDP 最大特征) ──
  try {
    Object.defineProperty(Navigator.prototype, 'webdriver', {
      get: () => false,
      configurable: true,
    });
  } catch (_) {
    try { Object.defineProperty(navigator, 'webdriver', { get: () => false }); } catch (__) {}
  }

  // ── 2. navigator.plugins (headless 默认空) ──
  const fakePlugins = [
    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
    { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
  ];
  const pluginArray = fakePlugins.map(p => {
    const plugin = Object.create(Plugin.prototype);
    Object.defineProperty(plugin, 'name', { get: () => p.name });
    Object.defineProperty(plugin, 'filename', { get: () => p.filename });
    Object.defineProperty(plugin, 'description', { get: () => p.description });
    return plugin;
  });
  try {
    Object.defineProperty(navigator, 'plugins', {
      get: () => {
        const arr = Object.create(PluginArray.prototype);
        pluginArray.forEach((p, i) => { arr[i] = p; });
        Object.defineProperty(arr, 'length', { get: () => pluginArray.length });
        return arr;
      },
      configurable: true,
    });
  } catch (_) {}

  // ── 3. navigator.languages ──
  try {
    Object.defineProperty(navigator, 'languages', {
      get: () => ['zh-CN', 'zh', 'en-US', 'en'],
      configurable: true,
    });
  } catch (_) {}

  // ── 4. window.chrome.runtime (headless 默认 undefined) ──
  try {
    if (!window.chrome) window.chrome = {};
    if (!window.chrome.runtime) {
      window.chrome.runtime = {
        PlatformOs: { MAC: 'mac', WIN: 'win', ANDROID: 'android', CROS: 'cros', LINUX: 'linux', OPENBSD: 'openbsd' },
        PlatformArch: { ARM: 'arm', X86_32: 'x86-32', X86_64: 'x86-64' },
        RequestUpdateCheckStatus: { THROTTLED: 'throttled', NO_UPDATE: 'no_update', UPDATE_AVAILABLE: 'update_available' },
        OnInstalledReason: { INSTALL: 'install', UPDATE: 'update', CHROME_UPDATE: 'chrome_update', SHARED_MODULE_UPDATE: 'shared_module_update' },
        OnRestartRequiredReason: { APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' },
      };
    }
  } catch (_) {}

  // ── 5. WebGL vendor/renderer (headless 暴露 SwiftShader) ──
  const origGetParameter = WebGLRenderingContext.prototype.getParameter;
  WebGLRenderingContext.prototype.getParameter = function (param) {
    if (param === 37445) return 'Google Inc. (Apple)';
    if (param === 37446) return 'ANGLE (Apple, Apple M4, OpenGL 4.1)';
    return origGetParameter.apply(this, arguments);
  };
  if (typeof WebGL2RenderingContext !== 'undefined') {
    const origGetParameter2 = WebGL2RenderingContext.prototype.getParameter;
    WebGL2RenderingContext.prototype.getParameter = function (param) {
      if (param === 37445) return 'Google Inc. (Apple)';
      if (param === 37446) return 'ANGLE (Apple, Apple M4, OpenGL 4.1)';
      return origGetParameter2.apply(this, arguments);
    };
  }

  // ── 6. Permissions API (headless 总是报 'denied' 或 'prompt' 异常) ──
  const origQuery = navigator.permissions && navigator.permissions.query;
  if (origQuery) {
    navigator.permissions.query = (params) => {
      if (params.name === 'notifications') {
        return Promise.resolve({ state: Notification.permission, onchange: null });
      }
      return origQuery.call(navigator.permissions, params);
    };
  }

  // ── 7. Chrome 启动后自动 hide cdc variables (防 $cdc_ 指纹) ──
  try {
    const doc = document;
    const cdcKeys = Object.keys(doc).filter(k => k.startsWith('cdc_') || k.startsWith('__driver_') || k.startsWith('__webdriver_'));
    cdcKeys.forEach(k => {
      try { delete doc[k]; } catch (_) {}
    });
  } catch (_) {}

  // 标记注入成功
  window.__hermes_stealth_injected__ = true;
  window.__hermes_stealth_version__ = '1.0';
})();
