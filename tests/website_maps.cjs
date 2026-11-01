// Focused regressions for shared county search and full-width maps.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../website');
const server=require('node:http').createServer((req,res)=>{
  const file=path.join(root,decodeURIComponent(req.url.split('?')[0]==='/'?'index.html':req.url.split('?')[0]));
  try{res.setHeader('Content-Type',({'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.geojson':'application/json','.svg':'image/svg+xml','.png':'image/png'})[path.extname(file)]||'text/plain');res.end(fs.readFileSync(file));}catch{res.statusCode=404;res.end();}
});
(async()=>{
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const url=`http://127.0.0.1:${server.address().port}/index.html`;
  let browser;
  try{
    browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{})});
    const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.route('https://kennethlow.com/**',r=>r.fulfill({body:''}));
    for(const width of [1440,768,390]){
      await page.setViewportSize({width,height:900});
      for(const [chapter,id] of [['introduction','population-map'],['data-prep-eda','migration-map'],['clustering','cluster-map']]){
        await page.goto(url+'#'+chapter);
        await page.waitForSelector('#'+id+' .county');
        const map=page.locator('#'+id),input=map.locator('input[type=search]'),results=map.locator('.county-suggestions');
        assert.equal(await map.locator('.map-guide').count(),0);
        assert.equal(await input.getAttribute('placeholder'),'Search by county or state');
        for(const [state,count] of [['Texas',254],['California',58],['Colorado',64]]){
          await input.fill(state);
          assert.equal(await results.locator('button').count(),count,`${id}: ${state}`);
          assert((await results.locator('button').allTextContents()).every(name=>name.endsWith(', '+state)));
          assert(await results.evaluate(el=>el.scrollHeight>el.clientHeight),'All state results remain scrollable');
        }
        await input.press('ArrowDown');await page.keyboard.press('ArrowUp');await page.keyboard.press('Enter');
        assert.match(await input.inputValue(),/Yuma.*Colorado/);
        await input.fill('Denver');await input.press('Enter');assert.match(await input.inputValue(),/Denver/);
        assert.equal(await map.locator('.county.selected').count(),1);
        await input.fill('zzzzzz');assert.match(await results.innerText(),/No matching/);
        await input.press('Escape');assert.equal(await input.getAttribute('aria-expanded'),'false');
        await map.locator('.reset').click();assert.equal(await input.inputValue(),'');
        assert(await map.evaluate(el=>{const body=el.querySelector('.map-content').getBoundingClientRect(),map=el.querySelector('.map-wrap').getBoundingClientRect();return map.width>body.width-30;}));
        assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)));
        await map.screenshot({path:path.resolve(__dirname,`../data/interim/map-${id}-${width}.png`)});
      }
    }
    assert.deepEqual(errors,[]);console.log('All three analysis maps: complete state lists, county selection, keyboard search, reset, full-width layouts and responsive checks passed');
  }finally{await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
