import {readFile} from 'node:fs/promises';
import {resolve,sep} from 'node:path';
import {requireActor,ServiceError} from './creator-core.mjs';
/** Only bind this to a private directory/store. Never publish private/. */
export async function createCuratedAccess(privateDirectory) {
 const root=resolve(privateDirectory);
 const load=async path=>{const full=resolve(root,path);if(!full.startsWith(root+sep))throw new ServiceError(400,'invalid_asset_path');return readFile(full);};
 const rows=JSON.parse((await load('catalog-full.json')).toString('utf8'));const index=new Map(rows.map(d=>[d.id,d]));
 return async({actor,id,request})=>{
  requireActor(actor);const row=index.get(id);if(!row)throw new ServiceError(404,'source_not_found');
  const headers={'Cache-Control':'private, no-store','Vary':'Cookie','X-Content-Type-Options':'nosniff'};
  if(new URL(request.url).searchParams.get('format')!=='json'){
   return new Response(await load(row.download),{headers:{...headers,'Content-Type':'application/zip','Content-Disposition':`attachment; filename="${id}.zip"`}});
  }
  const files=[];for(const f of row.files){const data=await load(f.local_source);const enc=/utf-?16/i.test(f.encoding||'')?'utf16le':'utf8';files.push({name:f.path.split('/').at(-1),content:data.toString(enc)});}
  const licenseText=(await load(row.license_file)).toString('utf8');
  return new Response(JSON.stringify({id,files,license:row.license,licenseText,authorName:row.provider||row.author,thirdPartyNotices:row.thirdPartyNotices||''}),{headers:{...headers,'Content-Type':'application/json; charset=utf-8'}});
 };
}
