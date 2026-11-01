// Pure calculations shared by the map, accessible table and data-contract tests.
export function countyFlows(rows, county, mode) {
  const pairs=new Map();
  for(const [origin,destination,quantity] of rows){
    if(origin===destination || (origin!==county && destination!==county))continue;
    const other=origin===county?destination:origin;
    if(!pairs.has(other))pairs.set(other,{id:other,inflow:null,outflow:null});
    pairs.get(other)[origin===county?'outflow':'inflow']=quantity;
  }
  let unknown=0,balanced=0;
  const flows=[];
  for(const pair of pairs.values()){
    const quantity=mode==='net'?(pair.inflow===null || pair.outflow===null?null:pair.inflow-pair.outflow):pair[mode];
    if(quantity===null){unknown++;continue;}
    if(quantity===0){balanced++;continue;}
    const inward=mode==='inflow'||(mode==='net'&&quantity>0);
    flows.push({...pair,quantity:Math.abs(quantity),signedQuantity:quantity,
      origin:inward?pair.id:county,destination:inward?county:pair.id,inward});
  }
  return {flows:flows.sort((a,b)=>b.quantity-a.quantity||a.id.localeCompare(b.id)),unknown,balanced};
}
