// source-only held admission and synthetic HTTP measurement controls.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { transformSync } from '../../app/node_modules/esbuild/lib/main.js';
import { discoveryPreset, composeDiscoveryRows, filterDiscoveryRows, sortDiscoveryRows } from '../../app/src/web/analysis-discovery.ts';
import { readDiscovery, readPeerSettings } from '../../app/src/web/explorer.ts';
async function main(){
 const reports=[];
 for(const name of ['real-discovery-api-check.ts','real-live-check.ts']){
  const source=readFileSync(new URL(name,import.meta.url),'utf8'),errors:any[]=[],fakeProcess={argv:['node','held','http://synthetic.invalid','1'],exitCode:0};let reads=0,http=0;
  const context={URLSearchParams,Buffer,process:fakeProcess,console:{error:(error:any)=>errors.push(String(error)),log:()=>assert.fail('held command emitted success')},fetch:()=>{http++;throw Error('unexpected HTTP');},require:(id:string)=>{
   if(id==='node:assert/strict')return assert;
   if(id==='node:fs')return {readFileSync:()=>{reads++;throw Error('unexpected data read');}};
   if(id==='node:crypto')return {};
   if(id==='node:perf_hooks')return {performance:{now:()=>0}};
   if(id.endsWith('/analysis-discovery.ts'))return {discoveryPreset,composeDiscoveryRows,filterDiscoveryRows,sortDiscoveryRows};
   if(id.endsWith('/explorer.ts'))return {readDiscovery,readPeerSettings};
   if(id.endsWith('/analysis-values.ts')||id.endsWith('/analysis-history.tsx'))return {};
   throw Error('unexpected import '+id);
  }};
  new Function('require','process','console','fetch','URLSearchParams','Buffer',transformSync(source,{loader:'ts',format:'cjs',target:'es2022'}).code)(context.require,context.process,context.console,context.fetch,URLSearchParams,Buffer);
  await new Promise(resolve=>setImmediate(resolve));assert.equal(fakeProcess.exitCode,1);assert.equal(errors.length,1);assert.match(errors[0],/withheld/);assert.equal(reads,0);assert.equal(http,0);reports.push({name,held_exit:1,file_reads:reads,http_calls:http});
 }
 const live=readFileSync(new URL('real-live-check.ts',import.meta.url),'utf8'),start=live.indexOf('async function read('),end=live.indexOf('\nfunction close(',start),requests:any[]=[];let clock=0,status=200;
 const scopedRead=new Function('base','performance','requests','fetch','assert','Buffer',transformSync(live.slice(start,end),{loader:'ts',format:'cjs',target:'es2022'}).code+';return read')('http://synthetic.invalid',{now:()=>++clock},requests,async()=>({status,text:async()=>' {"label":"é"} '}),assert,Buffer);
 assert.deepEqual(await scopedRead('/positive'),{label:'é'});assert.equal(requests[0].response_bytes,Buffer.byteLength(' {"label":"é"} '));assert.equal(requests[0].status,200);assert.equal(requests[0].request_wall_milliseconds,1);
 status=503;await assert.rejects(()=>scopedRead('/refused'));assert.equal(requests[1].status,503);assert.equal(requests[1].request_wall_milliseconds,1);
 console.log(JSON.stringify({status:'passed',held:reports,synthetic_measurements:requests,actual_network_or_artifact_calls:0}));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
