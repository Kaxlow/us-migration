// Run with Playwright available on NODE_PATH; CHROMIUM_EXECUTABLE is optional.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../website');
async function checkMapColumns(page,id){
  assert.equal(await page.locator(id+' .map-guide').count(),0);
  const search=page.locator(id+' input[type=search]');
  assert.equal(await search.getAttribute('placeholder'),'Search by county or state');
  await search.fill('Texas');
  assert.equal(await page.locator(id+' .county-suggestions button').count(),254);
  await search.press('Escape');
  await search.fill('');
  assert(await page.locator(id).evaluate(el=>{const body=el.querySelector('.map-content').getBoundingClientRect(),map=el.querySelector('.map-wrap').getBoundingClientRect();return map.width>body.width-30;}),'Map occupies the full card width');

}
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
    const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.route('https://kennethlow.com/**',r=>r.fulfill({body:''}));
    for(const width of [1440,768,390]){
      await page.setViewportSize({width,height:900});await page.goto(url+'#introduction');
      await page.waitForSelector('#population-map .county');
      await checkMapColumns(page,'#population-map');
      assert.equal(await page.locator('.questions .question h3').first().textContent(),'Geographic patterns');
      assert(await page.locator('#population-map').evaluate(el=>{const controls=el.querySelector('.map-controls').getBoundingClientRect(),top=el.querySelector('.map-top').getBoundingClientRect();return Math.abs(controls.right-top.right)<15;}),'Population controls align right');
      await page.locator('#population-map').screenshot({path:path.resolve(__dirname,`../data/interim/revised-population-map-${width}.png`)});
    }
    for(const width of [1440,768,390]){
      await page.setViewportSize({width,height:900});
      for(const chapter of ['clustering','pca']){
        await page.goto(url+'#'+chapter);
        await page.waitForSelector(chapter==='clustering'?'#clustering-cross-view rect':'#pca-quintiles circle');
        assert.equal(await page.locator('.method-details,.supporting-detail').count(),0);
        assert.equal(await page.locator('.analysis-samples h3').count(),0);
        const empty=await page.locator('[data-analysis-chart] .interactive-body').evaluateAll(els=>els.filter(el=>!el.querySelector('svg,ol')).map(el=>el.parentElement.id));assert.deepEqual(empty,[]);
        const headers=await page.locator('.card-header').evaluateAll(els=>els.map(el=>{const title=el.querySelector('h3').getBoundingClientRect();return [...el.querySelectorAll('select')].every(s=>{const r=s.getBoundingClientRect();return Math.abs(r.top-title.top)<2&&r.height<=title.height+1;});}));
        assert(headers.every(Boolean),'Outcome controls share the title row and fit its height');
        assert.equal(await page.locator('.analysis-samples h3').count(),0);
        const mapRows=await page.locator('.map-controls').evaluateAll(els=>els.map(el=>{const rects=[...el.querySelectorAll('input,select,button')].filter(e=>!e.closest('.county-suggestions')).map(e=>e.getBoundingClientRect());return rects.every(r=>Math.abs(r.top-rects[0].top)<2);}));
        assert(mapRows.every(Boolean),'Map controls occupy one row');
        assert.equal(await page.locator('.analysis-figure img').evaluateAll(els=>els.filter(el=>!el.src.includes('sample')).length),0);
        const bounds=await page.evaluate(()=>{const content=document.querySelector('.chapter-content').getBoundingClientRect(),chrome=document.querySelector('.chapter-title').getBoundingClientRect().bottom;return {overflow:document.documentElement.scrollWidth>innerWidth,oversized:[...document.querySelectorAll('.interactive-body svg')].filter(el=>{const r=el.getBoundingClientRect();return r.width>content.width+1||r.height>innerHeight-chrome;}).map(el=>el.closest('figure')?.id)};});assert(!bounds.overflow);assert.deepEqual(bounds.oversized,[]);
        if(chapter==='clustering'){
          await checkMapColumns(page,'#cluster-map');
          assert.deepEqual(await page.locator('#cluster-selection .x-axis .tick text').allTextContents(),['2','3','4','5','6','7','8']);
          assert.equal(await page.locator('.cluster-county').count(),0);
          const input=page.locator('#cluster-map input');await input.fill('Horry');
          await page.locator('#cluster-map .county-suggestions button').first().waitFor();
          await input.press('ArrowDown');await page.keyboard.press('Enter');
          assert.match(await input.inputValue(),/Horry/);
          assert(!(await page.locator('#cluster-map .map-detail').isVisible()));
          assert.equal(await page.locator('#cluster-map .county title').count(),0);
          await page.locator('#cluster-map .county.selected').dispatchEvent('pointermove',{clientX:100,clientY:300});
          assert.match(await page.locator('#cluster-map .tooltip').textContent(),/Horry.*C1/s);
          await page.locator('#cluster-map .county.selected').dispatchEvent('click');
          assert(!(await page.locator('#cluster-map .map-detail').isVisible()));
          await page.locator('.cluster-view').selectOption('characteristics');
          assert.match(await page.locator('#cluster-map .cluster-legend').textContent(),/housing costs/);
          await page.locator('#clustering-migration-profiles rect').first().focus();
          assert.match(await page.locator('#clustering-migration-profiles .chart-tooltip').textContent(),/Inflow rate/);
          assert.equal(await page.locator('.question-answer').count(),0);
          for(const view of ['characteristics','migration'])for(const outcome of ['net','inflow','outflow']){
            const card=page.locator('#clustering-'+view+'-outcomes');await card.locator('.outcome-select').selectOption(outcome);
            await card.locator('rect').first().focus();assert(await card.locator('.chart-tooltip').isVisible());
          }
        }else{
          await page.locator('#pca-scores .outcome-select').selectOption('net');
          const point=page.locator('#pca-scores circle').first();
          await page.mouse.move(0,0);
          await point.focus();
          assert.match(await page.locator('#pca-score-tooltip').textContent(),/Autauga County, Alabama.*PC1:.*PC2:.*Net migration:/);
          assert(await page.locator('#pca-score-tooltip').isVisible());
          assert.equal(await page.locator('#pca-scores .chart-tooltip').count(),0);
          await point.hover({force:true});
          assert(await page.locator('#pca-score-tooltip').isVisible());
          await page.locator('#pca-scores h3').hover();
          assert(!(await page.locator('#pca-score-tooltip').isVisible()));
          const flow=await page.locator('.workflow li').evaluateAll(els=>els.map(el=>el.getBoundingClientRect().left));
          assert(flow.every((x,i)=>!i||x>flow[i-1]),'Workflow runs left to right');
          await page.locator('#pca-quintiles .component-select').selectOption('PC3');
          await page.locator('#pca-quintiles circle').first().focus();
          assert.match(await page.locator('#pca-quintiles .chart-tooltip').textContent(),/PC3/);
          assert.equal(await page.locator('.question-answer').count(),0);
          assert(!/undefined/.test(await page.locator('#section-conclusions').locator('xpath=ancestor::section').textContent()));
          assert.equal(await page.locator('.pca-interpretations article').count(),5);
          assert.equal(await page.locator('#section-conclusions').locator('xpath=ancestor::section').locator('p').count(),4);
          assert.equal(await page.locator('#pca-associations rect').count(),15);
          assert.equal(await page.locator('.pca-supplement tbody tr').count(),13);
          assert.equal(await page.locator('.pca-supplement').getAttribute('open'),null);
          for(const outcome of ['net','inflow','outflow']){
            await page.locator('#pca-scores .outcome-select').selectOption(outcome);
            assert.equal(await page.locator('#pca-scores .scale-ticks span').count(),3);
            assert(!/95th|color limit/.test(await page.locator('#pca-scores .legend-card').textContent()));
            await page.locator('#pca-scores circle').first().focus();
            assert.match(await page.locator('#pca-score-tooltip').textContent(),new RegExp(outcome==='net'?'Net migration':outcome==='inflow'?'Inflow':'Outflow'));
            await page.locator('#pca-quintiles .outcome-select').selectOption(outcome);
            assert.equal(await page.locator('#pca-quintiles circle').count(),5);
          }
        }
        await page.locator('.section-nav a').filter({hasText:'Conclusion'}).click();
        await page.evaluate(()=>window.scrollBy(0,130));await page.waitForTimeout(150);
        const before=await page.evaluate(()=>window.scrollY);
        await page.locator('.section-nav a').filter({hasText:'Code',exact:true}).click();
        await page.waitForTimeout(100);await page.goBack();await page.waitForTimeout(150);
        assert(Math.abs(before-await page.evaluate(()=>window.scrollY))<3,'Same chapter section Back');
        assert.equal(await page.locator('.section-nav [aria-current]').textContent(),'Conclusion');
        await page.locator('#navigation a[href="#introduction"]').click();await page.waitForTimeout(150);
        await page.goBack();await page.waitForTimeout(750);
        const after=await page.evaluate(()=>window.scrollY);
        assert(Math.abs(before-after)<3,`${width} ${chapter}: Back ${before} â†’ ${after}`);
        await page.screenshot({path:path.resolve(__dirname,`../data/interim/updated-${chapter}-${width}.png`)});
        const chart=page.locator(chapter==='clustering'?'#cluster-geography':'#pca-loadings');
        await page.waitForTimeout(150);
        const cardFit=await chart.evaluate(el=>({height:el.getBoundingClientRect().height,available:innerHeight-document.querySelector('.chapter-title').getBoundingClientRect().height-document.querySelector('.site-masthead').getBoundingClientRect().height}));
        assert(cardFit.height<=cardFit.available,`Full card exceeds viewport: ${JSON.stringify(cardFit)}`);
        await chart.screenshot({path:path.resolve(__dirname,`../data/interim/updated-${chapter}-chart-${width}.png`)});
        console.log(`${width}px ${chapter}: charts, controls, sizing and Back passed`);
      }
    }
    for(const width of [1440,768,390]){
      await page.setViewportSize({width,height:900});await page.goto(url+'#data-prep-eda');
      await page.waitForSelector('#chart-9 .main-svg');
      const sizes=await page.evaluate(()=>[getComputedStyle(document.querySelector('.cleaning-stage h3')).fontSize,getComputedStyle(document.querySelector('.chart-card h3')).fontSize]);assert.equal(sizes[0],sizes[1]);
      for(const outcome of ['net','inflow','outflow']){
        await page.locator('#migration-map .outcome-select').selectOption(outcome);
        const gradient=await page.locator('#migration-map .gradient').evaluate(el=>el.style.background);
        assert(gradient.includes(outcome==='outflow'?'61, 112, 103':'150, 80, 48'));
        if(outcome==='net')assert.equal(await page.locator('#migration-map .legend-labels span').nth(1).textContent(),'0');
        const before=await page.locator('#migration-map .legend-labels').textContent();
        await page.locator('#migration-map .year').selectOption('2009');
        assert.equal(await page.locator('#migration-map .legend-labels').textContent(),before);
        await page.locator('#migration-map .year').selectOption('2023');
        for(const i of [2,4,5,6,7,8]){
          const card=page.locator('#chart-'+i).locator('xpath=ancestor::article');await card.locator('.outcome-select').selectOption(outcome);
          const field=outcome+'_individuals_per_1000';
          assert.match(await page.locator('#chart-'+i).getAttribute('aria-label'),new RegExp(outcome==='net'?'Net migration':outcome==='inflow'?'Inflow':'Outflow'));
          assert(await page.locator('#chart-'+i).evaluate(el=>el.data.length>0));
        }
      }
      const search=page.locator('#migration-map input');await search.fill('Alaska');await page.locator('#migration-map .county-suggestions button').first().click();
      for(const outcome of ['net','inflow','outflow']){
        const card=page.locator('#chart-4').locator('xpath=ancestor::article');
        await card.locator('.outcome-select').selectOption(outcome);
        for(const unit of ['count','rate']){
          await card.locator('.migration-unit').selectOption(unit);
          const actual=await page.locator('#chart-4').evaluate(el=>el.data[0].x);
          const data=JSON.parse(fs.readFileSync(path.join(root,'data/exploration/analysis.json')));
          const field=outcome+'_individuals'+(unit==='rate'?'_per_1000':'');
          assert.deepEqual(actual,(unit==='rate'?data.rateRankings:data.countRankings).filter(r=>r.outcome===outcome).map(r=>r[field]));
        }
      }
      await checkMapColumns(page,'#migration-map');
      assert(await page.locator('.migration-unit').evaluate(el=>{const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');ctx.font=getComputedStyle(el).font;return el.clientWidth>Math.max(...[...el.options].map(o=>ctx.measureText(o.text).width))+25;}),'Both unit options fit');
      await page.locator('#migration-map input').focus();
      assert.equal(await page.locator('#migration-map input').evaluate(el=>getComputedStyle(el).outlineStyle),'none');
      await page.locator('#migration-map').locator('..').screenshot({path:path.resolve(__dirname,`../data/interim/revised-map-${width}.png`)});
      assert.match(await search.inputValue(),/Alaska/);
      assert(!(await page.locator('#migration-map .map-detail').isVisible()));
      assert.equal(await page.locator('#migration-map .county title').count(),0);
      await page.locator('#migration-map .county.selected').dispatchEvent('pointermove',{clientX:100,clientY:300});
      assert.match(await page.locator('#migration-map .tooltip').textContent(),/state.*Inflow:.*Outflow:.*Net:/s);
      assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)));
      await page.locator('#chart-2').screenshot({path:path.resolve(__dirname,`../data/interim/outcome-eda-${width}.png`)});
      console.log(`${width}px EDA: outcomes, fixed map scales, state details and typography passed`);
    }
    for(const chapter of ['introduction','data-prep-eda','clustering','pca']){
      await page.goto(url+'#'+chapter);
      await page.waitForSelector('.section-title');
      const ids=await page.locator('.section-title').evaluateAll(els=>els.map(el=>el.id));
      for(const id of ids){
        await page.locator('#'+id).evaluate(el=>el.scrollIntoView({block:'start'}));
        await page.waitForTimeout(120);
        const atEnd=await page.evaluate(()=>scrollY>0&&scrollY+innerHeight>=document.documentElement.scrollHeight-2);
        assert.equal(await page.locator('.section-nav [aria-current]').getAttribute('href'),'#'+chapter+'/'+(atEnd?ids.at(-1):id));
      }
      console.log(`${chapter}: scrolling updates section navigation`);
    }
    assert.deepEqual(errors,[]);console.log('No browser errors');
  }finally{await browser?.close();server.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
