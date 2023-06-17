const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();

    // 开启请求拦截
    await page.setRequestInterception(true);

    // 如果请求是目标URL，则允许请求继续，否则中止请求
    page.on('request', (req) => {
        if (req.url().endsWith('/api/poppy/v1/opt?scene=opt')) {
            req.continue();
        } else {
            req.abort();
        }
    });

    await page.goto('https://www.temu.com/womens-clothing-o3-28.html');

    // 滚动到底部并点击元素
    await page.evaluate(() => {
        window.scrollBy(0, window.innerHeight);
        document.querySelector('._2U9ov4XG').click();
    });

    // 等待并捕获特定的网络请求
    const response = await page.waitForResponse(response => response.url().endsWith('/api/poppy/v1/opt?scene=opt') && response.status() === 200);

    // 获取返回的JSON数据
    const json = await response.json();
    console.log(json);

    await browser.close();
})();
