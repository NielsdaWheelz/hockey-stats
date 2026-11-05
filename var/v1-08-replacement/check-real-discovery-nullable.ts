// tiny public-consumer controls; only source files and in-memory synthetic rows.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { transformSync } from '../../app/node_modules/esbuild/lib/main.js';
import { discoveryPreset, composeDiscoveryRows, sortDiscoveryRows } from '../../app/src/web/analysis-discovery.ts';
const source=readFileSync(process.argv[2]!, 'utf8'),start=source.indexOf('function checkRaw(');assert.ok(start>=0);
const declaration=source.slice(start,source.indexOf('\n}',start)+2);
const fields=['offense_attempts_per60','offense_xg_per60','offense_attempts_relative_percent','offense_xg_relative_percent','defense_attempts_per60','defense_xg_per60','defense_attempts_relative_percent','defense_xg_relative_percent'];
const body=transformSync(declaration,{loader:'ts',format:'cjs',target:'es2022'}).code;
const checkRaw=new Function('assert','fields','ids',body+';return checkRaw')(assert,fields,(rows:any[])=>rows.map(r=>r.person.player_id).sort());
const support={included_seconds:24000,events:1,eligible_weight:null,known_excluded_seconds:0,unquantified_gap:false,reason_counts:[],inferred_inputs:[],current_season_information:true,prior_only:false,prior_seasons:[]};
const method={method_id:'synthetic-spatial',recipe_id:'synthetic',reference_id:'synthetic-reference',support_policy_id:'synthetic-support',reference:'synthetic',population:'synthetic only',limitations:[],assessment:{status:'experimental',findings:[]},evidence:[{uri:'/synthetic/coefficient-support.jsonl',sha256:'a'.repeat(64)}]};
const pending={availability:'not_computed',explanation:'synthetic unavailable',data:null},saved=new Map<string,any>();
const estimate=(value:number|null)=>({value,unavailable_reason:value===null?'missing_source':null,reason_detail:value===null?{explanation:'synthetic missing projection',evidence:[{kind:'method',id:method.method_id}]}:null,uncertainty:{kind:'not_estimated'}});
const players=[-2,0,2,null].map((value,index)=>{const player_id=String(index+1),data:any={support,method_id:method.method_id,state_weights:[{strength:'5v5',weight:1}]};for(const role of ['offense','defense'])for(const q of ['attempts','xg'])for(const suffix of ['per60','per60_complete','per60_neutral','relative_percent'])data[`${role}_${q}_${suffix}`]=estimate(value);saved.set(player_id,data);return {person:{player_id,display_name:'synthetic '+player_id,reported_position:'D',kind:'skater',teams:[]},result:{availability:'provided',explanation:null,data:{observed:pending,spatial:{five_on_five:{availability:'provided',explanation:null,data}},reported_usage:pending}}};});
const api:any={publication:{purpose:'real',publication_id:'synthetic-not-real'},kind:'skater',family:'overview',strength:null,season:{season:'20252026'},sources:{},methods:{[method.method_id]:method},players};
const rows=composeDiscoveryRows(api,api,discoveryPreset('spatial','5v5').columns,{peers:'position',peerMin:300,specialtyMin:50});
checkRaw(rows,saved,new Map([[method.method_id,method]]));
const orderingStart=source.indexOf('  const originalOrder='),ordering=source.slice(orderingStart,source.indexOf('\n',orderingStart));assert.ok(orderingStart>=0);
new Function('assert','rows','fields','sortDiscoveryRows','ids','saved',transformSync(ordering,{loader:'ts',format:'cjs',target:'es2022'}).code)(assert,rows,fields,sortDiscoveryRows,(items:any[])=>items.map(r=>r.person.player_id).sort(),saved);
for(const dir of ['asc','desc'] as const)for(const field of fields){const sorted=sortDiscoveryRows(rows,('spatial.5v5.'+field) as any,dir);assert.deepEqual(sorted.map(r=>r.cells['spatial.5v5.'+field].value),dir==='asc'?[-2,0,2,null]:[2,0,-2,null]);}
const refused=[];
for(const kind of ['reason','explanation','uncertainty','support','method','invented_zero']){const bad=JSON.parse(JSON.stringify(rows)),cell:any=bad[3]!.cells['spatial.5v5.offense_attempts_per60'];if(kind==='reason')cell.row.datum.original.unavailable_reason='failed_fit';else if(kind==='explanation')cell.row.datum.original.reason_detail.explanation='changed';else if(kind==='uncertainty')cell.row.datum.original.uncertainty.kind='changed';else if(kind==='support')cell.row.datum.support.included_seconds=1;else if(kind==='method')cell.row.datum.methods[0].recipe_id='changed';else cell.value=0;assert.throws(()=>checkRaw(bad,saved,new Map([[method.method_id,method]])));refused.push(kind);}
const old=readFileSync(new URL('../v1-08-product/discovery-api-check.ts',import.meta.url),'utf8'),oldStart=old.indexOf('  const originalOrder='),oldOrdering=old.slice(oldStart,old.indexOf('\n',oldStart));
assert.throws(()=>new Function('assert','rows','fields','sortDiscoveryRows','ids','saved',transformSync(oldOrdering,{loader:'ts',format:'cjs',target:'es2022'}).code)(assert,rows,fields,sortDiscoveryRows,(items:any[])=>items.map(r=>r.person.player_id).sort(),saved));
console.log(JSON.stringify({status:'passed',public_consumer_synthetic_rows:4,old_numeric_null_order_refused:true,selectors:8,nullable_sort_directions:2,refused,network_calls:0,actual_artifact_reads:0}));
