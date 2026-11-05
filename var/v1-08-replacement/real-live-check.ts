// temporary actual-api target check; browser and pixel acceptance remain separate.
import assert from 'node:assert/strict';
import { performance } from 'node:perf_hooks';
import { analysisMetric, selectHistoryValue } from '../../app/src/web/analysis-values.ts';
import { analysisCsvHeaders, analysisCsvRow } from '../../app/src/web/analysis-history.tsx';
const expectedPublicationId='WITHHELD_ACCEPTED_REAL_PUBLICATION_ID';
const requests:any[]=[];
const [base,playerId,secondId]=process.argv.slice(2);
const ids=secondId?[playerId,secondId]:[playerId];
async function read(path:string){const started=performance.now(),response=await fetch(base+path),raw=await response.text();requests.push({path,status:response.status,response_bytes:Buffer.byteLength(raw),request_wall_milliseconds:performance.now()-started});assert.equal(response.status,200,path);return JSON.parse(raw);}
function close(actual:number,expected:number,label:string){assert.ok(Math.abs(actual-expected)<=1e-9*(1+Math.abs(expected)),label);}
function checkMaps(maps:any,expected:Map<string,any>,role:string,quantity:string,view:string){
 assert.deepEqual(maps.selection.players,ids);assert.deepEqual(maps.players.map((r:any)=>r.player_id),ids);
 assert.equal(maps.selection.family,`${role}_${quantity}`);assert.equal(maps.selection.strength,'5v5');assert.equal(maps.selection.view,view);
 const areas=new Map<number,number>(maps.definition.display_grid.cells.map((c:any)=>[c.cell_id,c.area_sqft]));
 for(const row of maps.players){
  const scalar=expected.get(row.player_id);
  if(scalar===null){assert.equal(row.result.availability,'absent');continue;}
  assert.equal(row.result.availability,'provided');const map=row.result.data;
  const field=`${role}_${quantity}_per60`+(view==='complete'?'_complete':'');const estimate=scalar[field];
  assert.equal(map.integrated_value,estimate.value,`integrated scalar ${row.player_id}`);
  assert.deepEqual(map.support,scalar.support);assert.equal(map.method_id,scalar.method_id);
  if(estimate.value===null){assert.equal(map.cells,null);assert.equal(map.display_cells,null);assert.equal(map.unavailable_reason,estimate.unavailable_reason);assert.deepEqual(map.reason_detail,estimate.reason_detail);continue;}
  assert.equal(map.cells.length,656);assert.equal(map.display_cells.length,668);
  close(map.cells.reduce((s:number,c:any)=>s+c.value,0),estimate.value,`native integral ${row.player_id}`);
  close(map.display_cells.reduce((s:number,c:any)=>s+c.mass,0),estimate.value,`display integral ${row.player_id}`);
  close(map.display_cells.reduce((s:number,c:any)=>{assert.ok(areas.has(c.cell_id));close(c.density_per100sqft*areas.get(c.cell_id)!/100,c.mass,`cell density ${row.player_id}`);return s+c.density_per100sqft*areas.get(c.cell_id)!/100},0),estimate.value,`density integral ${row.player_id}`);
 }
}
function checkJointScale(offense:any,defense:any,quantity:string,view:string){
 // the wire contract shares a scale across both player rows AND both 5v5 roles.
 const values=[offense,defense].flatMap(m=>m.players.flatMap((r:any)=>r.result.availability==='provided'?(r.result.data.display_cells??[]).map((c:any)=>Math.abs(c.density_per100sqft)):[]));
 const maximum=Math.max(0,...values);
 for(const maps of [offense,defense]){assert.equal(maps.scale.maximum,maximum,'joint displayed density maximum');assert.equal(maps.scale.minimum,view==='effect'?-maximum:0);assert.equal(maps.scale.unit,`${quantity}_per60_per100sqft`);}
}
async function main(){
 assert.ok(typeof expectedPublicationId==='string'&&expectedPublicationId.length>0&&!expectedPublicationId.includes('WITHHELD'),'accepted real publication pin withheld; no HTTP requests');
 const profiles=await Promise.all(ids.map(id=>read(`/api/players/${id}?season=20252026`)));
 for(const profile of profiles){assert.equal(profile.publication.publication_id,expectedPublicationId);assert.equal(profile.publication.purpose,'real');}
 const receipts:any[]=[];let mapRows=0,jointScales=0,guard='not applicable to one-player check';
 for(const primaryHistory of profiles[0].history){
  const season=primaryHistory.season.season;const expected=new Map<string,any>();
  for(let index=0;index<ids.length;index++){
   const profile=profiles[index],id=ids[index],history=profile.history.find((r:any)=>r.season.season===season);assert.ok(history);
   if('availability' in history.families){assert.equal(history.person,null);expected.set(id,null);continue;}
   const spatial=history.families.spatial;assert.equal(spatial.availability,'provided',`${season}/${id}: spatial family`);
   const selected=spatial.data.find((r:any)=>r.strength==='5v5');assert.equal(selected?.result.availability,'provided',`${season}/${id}: 5v5 projection`);
   const data=selected.result.data;expected.set(id,data);
   for(const role of ['offense','defense'])for(const quantity of ['attempts','xg']){
    const field=`${role}_${quantity}_per60`,metric=analysisMetric(`spatial.5v5.${field}`)!;
    const datum:any=selectHistoryValue(history,profile,metric,id);
    assert.deepEqual(datum.spatial_detail,{difference:data[field],complete:data[field+'_complete'],neutral:data[field+'_neutral'],relative_percent:data[`${role}_${quantity}_relative_percent`]});assert.deepEqual(datum.support,data.support);
    const csv=analysisCsvRow(profile.publication,history.season,{datum,standing:{kind:'unavailable',reason:'live accounting check',peerGroup:null,n:null,cutoffMinutes:null},member:null,incompatiblePeerCount:null});
    assert.deepEqual(JSON.parse(csv[analysisCsvHeaders.indexOf('spatial_detail')] as string),datum.spatial_detail);assert.equal(csv[analysisCsvHeaders.indexOf('spatial_strength')],'5v5');
    assert.ok(datum.methods.some((m:any)=>m.evidence.some((r:any)=>r.uri.endsWith('coefficient-support.jsonl')&&/^[a-f0-9]{64}$/.test(r.sha256))));
   }
   receipts.push({season,player_id:id,offense_xg:data.offense_xg_per60.value,defense_xg:data.defense_xg_per60.value,support:data.support,methods:data.method_id});
  }
  for(const quantity of ['attempts','xg'])for(const view of ['effect','complete']){
   const maps=await Promise.all(['offense','defense'].map(role=>read(`/api/maps?season=${season}&players=${ids.join(',')}&family=${role}_${quantity}&strength=5v5&view=${view}`)));
   for(let roleIndex=0;roleIndex<2;roleIndex++){
    const role=roleIndex===0?'offense':'defense';checkMaps(maps[roleIndex],expected,role,quantity,view);mapRows+=maps[roleIndex].players.length;
    if(secondId&&guard==='not applicable to one-player check'){
     const bad=structuredClone(maps[roleIndex]),second=bad.players.find((r:any)=>r.player_id===secondId);
     if(second?.result.availability==='provided'&&typeof second.result.data.integrated_value==='number'){
      second.result.data.integrated_value+=1;
      assert.throws(()=>checkMaps(bad,expected,role,quantity,view),/integrated scalar/);guard='mutated second-player integrated value rejected';
     }
    }
   }
   checkJointScale(maps[0],maps[1],quantity,view);jointScales++;
  }
 }
 assert.equal(receipts.filter(r=>r.player_id===playerId).length,3,'primary target must exercise all three display years');
 if(secondId)assert.equal(guard,'mutated second-player integrated value rejected');
 console.log(JSON.stringify({status:'passed',purpose:profiles[0].publication.purpose,publication_id:profiles[0].publication.publication_id,player_id:playerId,second_id:secondId??null,requests,checked_player_years:receipts.length,checked_map_rows:mapRows,joint_scales:jointScales,adversarial_guard:guard,scope:'actual API scalars/quartet/support for each present selected player; both returned map rows, cell/native/display/density integrals, common scale over both roles and players; no browser/download/pixel claim',receipts}));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
