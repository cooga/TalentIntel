"""
浏览器隐身配置
使用原生 Playwright + 自定义反检测脚本
"""
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import yaml


class StealthBrowser:
    """隐身浏览器管理器"""
    
    def __init__(self, config_path: str = "config/researcher.yaml"):
        self.config = self._load_config(config_path)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.p = None
        self.profile_dir = None
        
    def _load_config(self, path: str) -> Dict[str, Any]:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    async def launch(self, headless: bool = False) -> Page:
        """启动隐身浏览器"""
        browser_config = self.config.get('browser', {})
        
        self.p = await async_playwright().start()
        
        # 浏览器启动参数
        args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
        ]
        
        # 持久化上下文（保存登录状态）
        profile_dir = browser_config.get('profile_dir')
        if profile_dir:
            Path(profile_dir).mkdir(parents=True, exist_ok=True)
            self.profile_dir = str(Path(profile_dir).resolve())
            
            # 使用持久化上下文
            self.context = await self.p.chromium.launch_persistent_context(
                self.profile_dir,
                headless=headless,
                args=args,
                viewport={
                    'width': browser_config.get('viewport', {}).get('width', 1440),
                    'height': browser_config.get('viewport', {}).get('height', 900),
                },
                user_agent=browser_config.get('user_agent'),
                locale=browser_config.get('locale', 'en-US'),
                timezone_id=browser_config.get('timezone', 'America/New_York'),
                permissions=['notifications'],
            )
        else:
            # 临时上下文
            self.browser = await self.p.chromium.launch(
                headless=headless,
                args=args,
            )
            
            self.context = await self.browser.new_context(
                viewport={
                    'width': browser_config.get('viewport', {}).get('width', 1440),
                    'height': browser_config.get('viewport', {}).get('height', 900),
                },
                user_agent=browser_config.get('user_agent'),
                locale=browser_config.get('locale', 'en-US'),
                timezone_id=browser_config.get('timezone', 'America/New_York'),
                permissions=['notifications'],
            )
        
        # 注入隐身脚本
        await self.context.add_init_script("""
            // 覆盖 webdriver 检测
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // 覆盖 chrome 对象
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // 覆盖 permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // 添加语言
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // 添加插件
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    },
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: ""},
                        description: "",
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        length: 1,
                        name: "Chrome PDF Viewer"
                    }
                ]
            });
        """)
        
        # 获取或创建页面
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
        
        return self.page
    
    async def close(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.p:
            await self.p.stop()
    
    async def save_state(self):
        """保存会话状态（持久化上下文自动保存）"""
        # 使用 launch_persistent_context 时状态自动保存
        pass
