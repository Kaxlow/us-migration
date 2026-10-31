// Verify incremental loading, stable references, chapter recovery and the research story.
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
  const url=`http://127.0.0.1:${server.address().port}/`;
  let browser;
  try{
    browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{})});
    const page=await browser.newPage(),errors=[],requests=[];
    page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
    await page.route('https://kennethlow.com/**',r=>r.fulfill({body:''}));
    await page.goto(url+'#introduction');await page.waitForSelector('#q10');
    assert(!requests.some(r=>/data\/(exploration|clustering|pca|classification)\//.test(r)),'Overview requests only its own datasets and compact findings');
    assert.deepEqual(await page.locator('.nav-group-label').allTextContents(),['Overview','Findings','Analyses','Data & methods']);
    assert.equal(await page.locator('.question-status').count(),10);
    assert(!/\[object Object\]|undefined/.test(await page.locator('main').innerText()));
    for(const width of [1440,768,390]){
      await page.setViewportSize({width,height:950});
      for(const slug of ['introduction','conclusion']){
        await page.goto(url+'#'+slug);await page.waitForSelector('.section-title');
        await page.evaluate(()=>document.fonts.ready);
        assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),`${slug} ${width} overflow`);
        await page.screenshot({path:path.resolve(__dirname,`../data/interim/story-${slug}-${width}.png`)});
      }
    }
    // A failed chapter remains retryable and does not affect the overview.
    let fail=true;
    await page.route('**/data/pca/pca.json',r=>fail?r.fulfill({status:503,body:'temporarily unavailable'}):r.continue());
    await page.goto(url+'#pca');await page.waitForSelector('#retry-chapter');
    await page.locator('a[href="#introduction"]').last().click();await page.waitForSelector('#q10');
    await page.locator('#navigation a[href="#pca"]').click();await page.waitForSelector('#retry-chapter');
    fail=false;await page.locator('#retry-chapter').click();await page.waitForSelector('#pca-quintiles circle');
    const pcaRequests=requests.filter(r=>r.endsWith('/data/pca/pca.json')).length;
    await page.locator('#navigation a[href="#introduction"]').click();await page.waitForSelector('#q10');
    await page.locator('#navigation a[href="#pca"]').click();await page.waitForSelector('#pca-quintiles circle');
    assert.equal(requests.filter(r=>r.endsWith('/data/pca/pca.json')).length,pcaRequests,'Successful data is cached');
    // Existing routes/aliases, explicit IDs, assets and repository notebook targets.
    for(const slug of ['introduction','conclusion','data-prep-eda','clustering','pca','naivebayes','dectrees','regression','adaboost','gradientboosting','xgboost']){
      await page.goto(url+'#'+slug);await page.waitForSelector('.section-title');
      await page.waitForFunction(()=>!document.querySelector('main').hasAttribute('aria-busy'));
      const ids=await page.locator('.section-title').evaluateAll(els=>els.map(e=>e.id));
      assert.equal(new Set(ids).size,ids.length);assert(ids.every(Boolean));
      const local=await page.locator('a[href^="data/"],a[href^="assets/"],img').evaluateAll(els=>[...new Set(els.map(e=>e.getAttribute('href')||e.getAttribute('src')))]);
      for(const target of local)assert(fs.existsSync(path.join(root,target)),`${slug}: ${target}`);
      const notebooks=await page.locator('a[href*="/notebooks/"]').evaluateAll(els=>els.map(e=>e.href));
      for(const href of notebooks){
        const [file,anchor]=decodeURIComponent(href.split('/notebooks/')[1]).split('#');
        const notebook=path.join(root,'../notebooks',file);assert(fs.existsSync(notebook),href);
        if(anchor){const cells=JSON.parse(fs.readFileSync(notebook)).cells;
          assert(cells.some(c=>c.cell_type==='markdown'&&c.source.join('').includes(`id="${anchor}"`)),href);
        }
      }
      for(const id of ids){
        await page.locator(`.section-nav a[href="#${slug}/${id}"]`).click();
        assert.equal(new URL(page.url()).hash,`#${slug}/${id}`);
      }
    }
    await page.goto(url+'#conclusion/section-results');await page.waitForSelector('#section-findings');
    assert.equal(new URL(page.url()).hash,'#conclusion/section-findings');
    await page.goto(url+'#regression/section-code');await page.waitForSelector('#section-overview');
    assert.equal(new URL(page.url()).hash,'#regression/section-overview');
    assert.deepEqual(errors,[]);
    console.log('Story, responsive layouts, lazy loading, caching, failure/retry, references and aliases passed');
  }finally{await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
