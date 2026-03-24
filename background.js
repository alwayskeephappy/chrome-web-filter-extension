const FILTER_STYLE_ID = "__chrome_web_filter_grayscale_style__";

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

async function setTabIcon(tabId, enabled) {
  await chrome.action.setIcon({
    tabId,
    path: enabled ? ICONS.on : ICONS.off,
  });
  await chrome.action.setTitle({
    tabId,
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

async function getTabFilterEnabled(tabId) {
  const [result] = await chrome.scripting.executeScript({
    target: { tabId },
    func: (styleId) => Boolean(document.getElementById(styleId)),
    args: [FILTER_STYLE_ID],
  });

  return Boolean(result?.result);
}

async function syncTabIcon(tabId) {
  if (!tabId) {
    return;
  }

  try {
    const enabled = await getTabFilterEnabled(tabId);
    await setTabIcon(tabId, enabled);
  } catch {
    await setTabIcon(tabId, false).catch(() => {});
  }
}

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id) {
    return;
  }

  try {
    const enabled = await toggleTabFilter(tab.id);
    await setTabIcon(tab.id, enabled);
  } catch {
    await setTabIcon(tab.id, false).catch(() => {});
  }
});

chrome.tabs.onActivated.addListener(async ({ tabId }) => {
  await syncTabIcon(tabId);
});

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo) => {
  if (changeInfo.status === "loading") {
    await setTabIcon(tabId, false).catch(() => {});
  }
});
