// Verify classification chapters against the actual notebook exports.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../website');
const server=require('node:http').createServer((req,res)=>{
 const file=path.join(root,decodeURIComponent(req.url.split('?')[0]==='/'?'index.html':req.url.split('?')[0]));
 try{res.setHeader('Content-Type',({'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.geojson':'application/json','.svg':'image/svg+xml','.png':'image/png','.csv':'text/csv','.txt':'text/plain'})[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));}catch{res.statusCode=404;res.end();}
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const url=`http://127.0.0.1:${server.address().port}/`;
 const data={...JSON.parse(fs.readFileSync(path.join(root,'data/classification/naive-bayes.json'))).tasks,...JSON.parse(fs.readFileSync(path.join(root,'data/classification/decision-trees.json'))).tasks};
 let browser;
 try{
  browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{})});
  const page=await browser.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('https://kennethlow.com/**',r=>r.fulfill({body:''}));
  for(const width of [1440,768,390]){
   await page.setViewportSize({width,height:900});
   for(const chapter of ['naivebayes','dectrees']){
    await page.goto(url+'#'+chapter+'/section-results');
    await page.waitForSelector('.confusion-plot .main-svg');
    await page.evaluate(()=>document.fonts.ready);
    assert.deepEqual(await page.locator('.section-title').allTextContents(),['Overview','Results','Conclusions','Data Prep','Code']);
    const tasks=chapter==='naivebayes'?['inflow']:['outflow','net'];
    for(const outcome of tasks){
     const plot=page.locator('#'+outcome+'-confusion');
     const selector=page.getByLabel(outcome+' confusion matrix display');
     await selector.selectOption('counts');
     assert.deepEqual(await plot.evaluate(el=>el.data[0].z),data[outcome].model.confusion);
     await selector.selectOption('normalized');
     assert.deepEqual(await plot.evaluate(el=>el.data[0].z),data[outcome].model.confusion_normalized);
     await selector.focus();await page.keyboard.press('Home');await page.keyboard.press('Enter');
     assert.equal(await selector.inputValue(),'counts');
    }
    // All sample/download/image targets are local files and resolve successfully.
    const urls=await page.locator('a[href^="data/"],a[href^="assets/"],img').evaluateAll(els=>[...new Set(els.map(el=>el.getAttribute('href')||el.getAttribute('src')))]);
    for(const file of urls){assert(fs.existsSync(path.join(root,file)),file);assert.equal((await page.request.get(url+file)).status(),200,file);}
    const download=page.locator('a[download][href$="-predictions.csv"]').first();
    const [received]=await Promise.all([page.waitForEvent('download'),download.click()]);
    assert(received.suggestedFilename().endsWith('-predictions.csv'));
    if(chapter==='dectrees'){
     for(const target of ['outflow','net'])for(const depth of ['2','4','6']){
      await page.locator('#tree-target').selectOption(target);await page.locator('#tree-depth').selectOption(depth);
      const tree=data[target].trees.find(t=>t.depth===Number(depth));
      assert.equal(await page.locator('.tree-scroll g[role=button]').count(),tree.node_count);
      const last=page.locator('.tree-scroll g[role=button]').last();
      await last.focus();await page.keyboard.press('Enter');
      assert.match(await page.locator('.tree-node-detail').innerText(),/training counties/);
      const link=await page.locator('.tree-downloads a').first().getAttribute('href');
      assert.equal(link,`assets/classification/${target}-tree-${depth}.svg`);
      assert.equal((await page.request.get(url+link)).status(),200);
     }
     await page.locator('#tree-target').selectOption('net');await page.locator('#tree-depth').selectOption('4');
     await page.locator('.supervised-tree').scrollIntoViewIfNeeded();
     await page.screenshot({path:path.resolve(__dirname,`../data/interim/classification-tree-${width}.png`)});
    }
    await page.locator(`.section-nav a[href="#${chapter}/section-results"]`).click();
    await page.waitForTimeout(180);
    assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),`${width} ${chapter} page overflow`);
    await page.screenshot({path:path.resolve(__dirname,`../data/interim/classification-${chapter}-${width}.png`)});
    assert(await page.locator('.supervised-plot').evaluateAll(els=>els.every(el=>{const svg=el.querySelector('.main-svg');return svg&&svg.getBoundingClientRect().width<=el.clientWidth+1;})), 'Chart SVG fits its container');
    if(width===390){await page.locator('.supervised-chart-card').first().scrollIntoViewIfNeeded();await page.screenshot({path:path.resolve(__dirname,`../data/interim/classification-matrix-${chapter}-${width}.png`)});}
    const scroll=await page.evaluate(()=>scrollY);
    await page.locator('#navigation a[href="#introduction"]').click();
    await page.waitForSelector('.questions');
    await page.goBack();await page.waitForSelector('.confusion-plot .main-svg');await page.waitForTimeout(200);
    assert(Math.abs(await page.evaluate(()=>scrollY)-scroll)<4,'Back restores reading position');
    await page.locator(`.section-nav a[href="#${chapter}/section-conclusions"]`).click();
    assert((await page.locator('#section-conclusions').innerText()).includes('Conclusions'));
    await page.waitForTimeout(150);
    assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)), 'Conclusions fit viewport');
    if(chapter==='dectrees'&&width===1440){await page.locator('#section-conclusions').scrollIntoViewIfNeeded();await page.screenshot({path:path.resolve(__dirname,'../data/interim/classification-conclusions-1440.png')});}
    console.log(`${width}px ${chapter}: metrics, selectors, keyboard, downloads, history and layout passed`);
   }
  }
  assert.deepEqual(errors,[]);console.log('No classification browser errors');
 }finally{await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
