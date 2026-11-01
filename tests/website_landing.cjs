// Verify real flow arithmetic, perspective interaction, all controls and layouts.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../website');
let seedLegacy=false;
const server=require('node:http').createServer((req,res)=>{
  if(req.url==='/cache-fixture.html'){
    res.setHeader('Content-Type','text/html');
    res.end('<link rel="stylesheet" href="landing.css"><script src="landing.js"></script><script type="module" src="county-search.js"></script>');return;
  }
  if(seedLegacy&&['/landing.css','/landing.js','/county-search.js'].includes(req.url)){
    res.setHeader('Cache-Control','public, max-age=3600');
    res.setHeader('Content-Type',req.url.endsWith('.css')?'text/css':'text/javascript');
    res.end(req.url.endsWith('.css')?'.atlas-title{text-align:left!important}':'window.cachedLegacyAtlas=true;');return;
  }
  const file=path.join(root,decodeURIComponent(req.url.split('?')[0]==='/'?'index.html':req.url.split('?')[0]));
  try{res.setHeader('Content-Type',({'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.geojson':'application/json','.svg':'image/svg+xml'})[path.extname(file)]||'text/plain');res.end(fs.readFileSync(file));}catch{res.statusCode=404;res.end();}
});
(async()=>{
  const {countyFlows}=await import('../website/flow-data.js');
  const fixture=[['A','B',30],['B','A',50],['A','C',12],['D','A',null],['A','E',7],['E','A',7],['A','A',99]];
  assert.equal(countyFlows(fixture,'A','inflow').flows[0].quantity,50);
  assert.equal(countyFlows(fixture,'A','outflow').flows.length,3);
  const net=countyFlows(fixture,'A','net');
  assert.deepEqual(net.flows.map(f=>[f.origin,f.destination,f.quantity]),[['B','A',20]]);
  assert.equal(net.unknown,2);assert.equal(net.balanced,1);
  assert.deepEqual(countyFlows(fixture,'B','net').flows.map(f=>[f.origin,f.destination,f.quantity]),[['B','A',20]]);
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  const url=`http://127.0.0.1:${server.address().port}/`;
  let browser;
  try{
    browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_EXECUTABLE?{executablePath:process.env.CHROMIUM_EXECUTABLE}:{})});
    // Revisit after an update with obsolete unversioned CSS and modules cached.
    // This separate context uses real HTTP caching (request routing disables it).
    const cachedPage=await browser.newPage();
    seedLegacy=true;await cachedPage.goto(url+'cache-fixture.html');seedLegacy=false;
    assert.equal(await cachedPage.evaluate(()=>window.cachedLegacyAtlas),true);
    await cachedPage.goto(url+'landing.html');
    await cachedPage.waitForFunction(()=>+document.querySelector('#flow-canvas').dataset.flowCount>0);
    assert.equal(await cachedPage.evaluate(()=>window.cachedLegacyAtlas),undefined);
    assert.equal(await cachedPage.locator('h1').evaluate(el=>getComputedStyle(el).textAlign),'center');
    await cachedPage.close();
    const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.route('https://kennethlow.com/**',r=>r.fulfill({body:''}));
    await page.addInitScript(()=>{const move=Path2D.prototype.moveTo;Path2D.prototype.moveTo=function(x,y){if(window.mapVertices?.length<12)window.mapVertices.push([x,y]);return move.call(this,x,y);};window.mapVertices=[];});
    await page.goto(url);await page.waitForURL('**/landing.html');
    await page.waitForFunction(()=>+document.querySelector('#flow-canvas').dataset.flowCount>0);
    assert.equal(await page.locator('#flow-year option').count(),15);
    const data=JSON.parse(fs.readFileSync(path.join(root,'data/flows/2023.json')));
    for(const mode of ['inflow','outflow','net']){
      await page.locator('#flow-mode').selectOption(mode);
      await page.waitForFunction(m=>document.querySelector('#flow-canvas').getAttribute('aria-label').startsWith('3D '+m+' map'),mode);
      const expected=countyFlows(data.flows,'08031',mode);
      await page.waitForFunction(count=>+document.querySelector('#flow-canvas').dataset.flowCount===count,expected.flows.length);
      const before=await page.locator('#flow-canvas').evaluate(c=>c.toDataURL());
      await page.waitForFunction(before=>document.querySelector('#flow-canvas').toDataURL()!==before,before);
    }
    await page.locator('#flow-county').fill('06037');await page.locator('#flow-county').press('Enter');
    await page.waitForFunction(()=>document.querySelector('#flow-canvas').getAttribute('aria-label').includes('Los Angeles'));
    await page.locator('#flow-year').selectOption('2009');
    await page.waitForFunction(()=>document.querySelector('#flow-canvas').getAttribute('aria-label').includes('2008–2009'));
    await page.locator('#flow-mode').selectOption('inflow');
    await page.waitForFunction(()=>document.querySelector('#flow-canvas').getAttribute('aria-label').startsWith('3D inflow'));
    const image=await page.locator('#flow-canvas').evaluate(c=>c.toDataURL());
    await page.locator('#flow-canvas').focus();await page.keyboard.press('ArrowRight');
    await page.waitForFunction(before=>document.querySelector('#flow-canvas').toDataURL()!==before,image);
    await page.locator('#flow-reset').click();
    await page.emulateMedia({reducedMotion:'reduce'});
    await page.locator('#flow-county').fill('Texas');
    assert.equal(await page.locator('#flow-counties button').count(),254);
    await page.locator('#flow-county').press('ArrowDown');await page.keyboard.press('Enter');
    assert.match(await page.locator('#flow-county').inputValue(),/Anderson County, Texas/);
    await page.locator('#flow-county').fill('08031');await page.locator('#flow-county').press('Enter');
    await page.waitForFunction(()=>document.querySelector('#flow-canvas').getAttribute('aria-label').includes('Denver'));
    await page.evaluate(()=>window.mapVertices=[]);await page.locator('#flow-reset').click();
    await page.waitForFunction(()=>window.mapVertices.length===12);
    const vertices=await page.evaluate(()=>window.mapVertices);
    const bounds=await page.locator('#flow-canvas').boundingBox();
    await page.mouse.move(bounds.x+bounds.width/2,bounds.y+bounds.height/2);
    await page.mouse.down();await page.evaluate(()=>window.mapVertices=[]);
    await page.mouse.move(bounds.x+bounds.width/2+60,bounds.y+bounds.height/2+30);await page.mouse.up();
    await page.waitForFunction(()=>window.mapVertices.length===12);
    const moved=await page.evaluate(()=>window.mapVertices);
    vertices.forEach(([x,y],i)=>{assert(Math.abs(moved[i][0]-x-60)<.01);assert(Math.abs(moved[i][1]-y-30)<.01);});
    const still=await page.locator('#flow-canvas').evaluate(c=>c.toDataURL());
    await page.waitForTimeout(150);assert.equal(await page.locator('#flow-canvas').evaluate(c=>c.toDataURL()),still);
    assert.equal(await page.locator('#flow-motion').innerText(),'Animate flows');
    await page.locator('#flow-motion').click();
    assert.equal(await page.locator('#flow-motion').getAttribute('aria-pressed'),'true');
    const resumed=await page.locator('#flow-canvas').evaluate(c=>c.toDataURL());
    await page.waitForFunction(before=>document.querySelector('#flow-canvas').toDataURL()!==before,resumed);
    await page.locator('#flow-motion').click();
    await page.waitForTimeout(100);
    const paused=await page.locator('#flow-canvas').evaluate(c=>c.toDataURL());
    await page.waitForTimeout(150);assert.equal(await page.locator('#flow-canvas').evaluate(c=>c.toDataURL()),paused);
    await page.locator('#flow-motion').click();
    await page.emulateMedia({reducedMotion:'no-preference'});
    await page.locator('#flow-play').click();
    await page.waitForFunction(()=>document.querySelector('#flow-year').value!=='2009');
    await page.locator('#flow-play').click();assert.equal(await page.locator('#flow-play').getAttribute('aria-pressed'),'false');
    await page.locator('#flow-county').fill('08031');await page.locator('#flow-county').press('Enter');
    await page.locator('#flow-year').selectOption('2023');
    await page.waitForFunction(()=>document.querySelector('#flow-canvas').getAttribute('aria-label').includes('2022–2023'));
    for(const width of [1440,768,390]){
      await page.setViewportSize({width,height:900});
      await page.waitForTimeout(200);
      assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),`${width}: landing overflows`);
      assert.equal(await page.locator('header,footer,.map-guide,.flow-records,#flow-scale').count(),0);
      assert.equal(await page.locator('h1').innerText(),'US County Migration Atlas');
      assert.equal(await page.locator('#flow-status').innerText(),'');
      assert.equal((await page.locator('main > :last-child').innerText()).replace(/\s+/g,' '),'View the analysis →');
      assert.equal(await page.locator('#flow-county').getAttribute('placeholder'),'Search by county or state');
      await page.screenshot({path:path.resolve(__dirname,`../data/interim/landing-${width}.png`),fullPage:true});
      await page.goto(url+'index.html#introduction/section-research-framework');await page.waitForSelector('#q10');
      await page.waitForTimeout(200);
      const box=await page.locator('.framework-visual').boundingBox();
      assert(box.y>=0&&box.y+box.height<=900,`${width}: entire framework fits viewport (${JSON.stringify(box)})`);
      await page.locator('#q10').click();assert.match(await page.locator('#framework-detail').innerText(),/magnitude/);
      await page.screenshot({path:path.resolve(__dirname,`../data/interim/framework-${width}.png`)});
      await page.goto(url+'landing.html');await page.waitForFunction(()=>+document.querySelector('#flow-canvas').dataset.flowCount>0);
    }
    await page.locator('.analysis-button').click();await page.waitForURL('**/index.html*');
    // Every fitted tree, including the largest: rectangles never intersect.
    await page.goto(url+'index.html#dectrees/section-results');await page.waitForSelector('#tree-target');
    for(const outcome of ['outflow','net'])for(const depth of ['2','4','6']){
      await page.locator('#tree-target').selectOption(outcome);await page.locator('#tree-depth').selectOption(depth);
      const overlaps=await page.locator('.tree-scroll g[role=button] rect').evaluateAll(nodes=>{
        const boxes=nodes.map(n=>n.getBoundingClientRect());let count=0;
        for(let i=0;i<boxes.length;i++)for(let j=i+1;j<boxes.length;j++){const a=boxes[i],b=boxes[j];if(a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top)count++;}return count;
      });assert.equal(overlaps,0,`${outcome} depth ${depth}: overlapping nodes`);
    }
    assert.deepEqual(errors,[]);console.log('Flow calculations, missing pairs, selectors, playback, state search, panning, flow animation and reduced motion, responsive layouts, framework and tree spacing passed');
  }finally{await browser?.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
