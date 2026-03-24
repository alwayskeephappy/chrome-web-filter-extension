const FILTER_STYLE_ID = "__chrome_web_filter_grayscale_style__";
let globalFilterEnabled = false;

const ICONS = {
  off: {
    16: "icons/light-16.png",
    32: "icons/light-32.png",
  },
  on: {
    16: "icons/dark-16.png",
    32: "icons/dark-32.png",
  },
};

async function setGlobalIcon(enabled) {
  await chrome.action.setIcon({
    path: enabled ? ICONS.on : ICONS.off,
  });
  await chrome.action.setTitle({
    title: enabled ? "关闭黑白滤镜" : "开启黑白滤镜",
  });
}

async function toggleTabFilter(tabId) {
  const [result] = await chrome.scripting.executeScript({
    target: { tabId },
    func: (styleId) => {
      const oldStyle = document.getElementById(styleId);
      if (oldStyle) {
        oldStyle.remove();
        return false;
      }

      const style = document.createElement("style");
      style.id = styleId;
      style.textContent =
        "html { filter: grayscale(100%) !important; -webkit-filter: grayscale(100%) !important; }";
      document.documentElement.appendChild(style);
      return true;
    },
    args: [FILTER_STYLE_ID],
  });

  return Boolean(result?.result);
}

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id) {
    return;
  }

  try {
    const enabled = await toggleTabFilter(tab.id);
    globalFilterEnabled = enabled;
    await setGlobalIcon(globalFilterEnabled);
  } catch (error) {
    await setGlobalIcon(false).catch(() => {});
    console.error("切换黑白滤镜失败:", error);
  }
});

setGlobalIcon(false).catch(() => {});
