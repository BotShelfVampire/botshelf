/**
 * Traders Library creator service. No brokerage execution or payment execution.
 * Production must inject verified auth, durable transactional storage, a scanner,
 * rights review and the existing BSV commerce/entitlement adapters.
 * Test adapters are NOT production implementations.
 */
import { createHash, randomUUID } from 'node:crypto';
import { COMMERCIAL_TERMS, parseMonthlyPrice, productMatches, subscriptionIsActive } from './subscription-policy.mjs';
import { validatePublicationPolicy, hasInvitation } from './publishing-policy.mjs';
export class ServiceError extends Error {
  constructor(status, code) { super(code); this.status = status; this.code = code; }
}
const fail = (status, code) => { throw new ServiceError(status, code); };
export const PLATFORM_IDS = new Set(['tradingview','mt4','mt5','ctrader','ninjatrader','sierra-chart','multicharts','tradestation','quantower','quantconnect-lean','backtrader','freqtrade','amibroker','motivewave','other']);
const KINDS = new Set(['indicator','strategy','ea','trade-manager','template']);
const LICENSES = new Set(['MIT','Apache-2.0','GPL-3.0-only','GPL-3.0-or-later','MPL-2.0','BSD-2-Clause','BSD-3-Clause','custom']);
const EXTENSIONS = new Set(['pine','ps','mq4','mq5','mqh','cs','py','cpp','h','hpp','afl','els','txt','md','json','toml','set','js','ts','java','lua','r','jl']);
const plain = (v, name, min = 1, max = 1000) => {
  if (typeof v !== 'string' || v.trim().length < min || v.length > max || /\u0000/.test(v)) fail(422, `invalid_${name}`);
  return v.trim();
};
const digest = value => createHash('sha256').update(typeof value === 'string' ? value : JSON.stringify(value)).digest('hex');
export function priceMinor(value, mode) {
  if (mode === 'free') { if (!['','0','0.00','0.000000'].includes(String(value ?? ''))) fail(422,'free_price_must_be_zero'); return '0'; }
  try { return parseMonthlyPrice(value); } catch(e) { fail(422,e.message); }
}
export function requireActor(actor) {
  // Supplied exclusively by the trusted server auth adapter, never from JSON.
  if (!actor?.id) fail(401,'email_registration_required');
  if (actor.emailVerified !== true) fail(403,'email_verification_required');
  if (actor.disabled === true) fail(403,'account_disabled');
  return actor;
}
export function normalizeDraft(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) fail(422,'invalid_draft');
  const platform=plain(input.platform,'platform'); if (!PLATFORM_IDS.has(platform)) fail(422,'invalid_platform');
  const kind=plain(input.kind,'kind'); if (!KINDS.has(kind)) fail(422,'invalid_kind');
  const mode=input.mode; if (!['free','paid'].includes(mode)) fail(422,'invalid_mode');
  const license=input.license; if (!LICENSES.has(license)) fail(422,'invalid_license');
  const rights=input.rights; if (!['original','licensed-derivative','written-permission'].includes(rights)) fail(422,'invalid_rights');
  const publicationPolicy=validatePublicationPolicy(input,fail);
  const rawFiles=input.files; if (!Array.isArray(rawFiles) || rawFiles.length<1 || rawFiles.length>20) fail(422,'invalid_files');
  let total=0; const names=new Set();
  const files=rawFiles.map(file=>{
    const name=plain(file.name,'filename',1,140);
    if (!/^[\p{L}\p{N} _.()-]+$/u.test(name) || name==='.' || name==='..' || /[\\/:]/.test(name) || name.startsWith('.')) fail(422,'unsafe_filename');
    const lower=name.toLowerCase(); if (names.has(lower)) fail(422,'duplicate_filename'); names.add(lower);
    if (!EXTENSIONS.has(lower.split('.').pop()) && !/^license(?:\.txt)?$/i.test(name) && !/^notice(?:\.txt)?$/i.test(name)) fail(422,'unsupported_file_type');
    if (typeof file.content !== 'string' || !file.content.trim() || /\u0000/.test(file.content)) fail(422,'text_source_required');
    const size=Buffer.byteLength(file.content); total+=size; if (size>262144 || total>1048576) fail(413,'source_too_large');
    return {name,content:file.content,sha256:digest(file.content),bytes:size};
  });
  if (!files.some(f=>!['txt','md','json','toml','set'].includes(f.name.toLowerCase().split('.').pop()))) fail(422,'source_file_required');
  const term = mode==='free' ? 'free' : COMMERCIAL_TERMS.term;
  // Never claim downloaded source can be revoked when a subscription ends.
  const value = {
    title:plain(input.title,'title',3,120), authorName:plain(input.authorName,'author_name',2,80), platform,kind,mode,license,rights,term,
    platformName:platform==='other'?plain(input.platformName,'platform_name',2,80):'',
    platformVersion:plain(input.platformVersion,'platform_version',1,80),
    summary:plain(input.summary,'summary',10,500), purpose:plain(input.purpose,'purpose',20,4000),
    setup:plain(input.setup,'setup',20,6000), parameters:plain(input.parameters,'parameters',10,4000),
    limitations:plain(input.limitations,'limitations',10,4000), version:plain(input.version,'version',1,40),
    priceMinor:priceMinor(input.price,mode), currency:'USDT',
    ...COMMERCIAL_TERMS,...publicationPolicy,term,billingInterval:mode==='paid'?'month':null,accessDays:mode==='paid'?30:null,
    licenseText:plain(input.licenseText,'license_text',40,50000),
    thirdPartyNotices: typeof input.thirdPartyNotices==='string' ? input.thirdPartyNotices.slice(0,20000) : '',
    permissionEvidence:typeof input.permissionEvidence==='string'?input.permissionEvidence.slice(0,20000):'',
    files, agreedRights:input.agreedRights===true, agreedDistribution:input.agreedDistribution===true,
    testedByPlatform:false, compilation:'not_run', runtime:'not_run'
  };
  if (!value.agreedRights || !value.agreedDistribution) fail(422,'rights_declarations_required');
  // This is an intake check, not a legal decision or malware clearance.
  value.flags=[];
  const primary={tradingview:['pine','ps'],mt4:['mq4'],mt5:['mq5'],ctrader:['cs','py'],ninjatrader:['cs'],'sierra-chart':['cpp'],multicharts:['els','cs'],tradestation:['els'],quantower:['cs'],'quantconnect-lean':['py','cs'],backtrader:['py'],freqtrade:['py'],amibroker:['afl'],motivewave:['java']};
  if(platform==='other') value.flags.push('unknown_platform_review');
  else if(!files.some(f=>primary[platform]?.includes(f.name.toLowerCase().split('.').pop()))) value.flags.push('platform_source_mismatch');
  if (publicationPolicy.sourceOrigin==='remake' && mode==='paid') value.flags.push('paid_remake_commercial_rights_review');
  if (rights!=='original' && !value.permissionEvidence.trim()) value.flags.push('missing_rights_evidence');
  const source=files.map(f=>f.content).join('\n');
  if(publicationPolicy.accessMode!=='open' && (/GPL|MPL/.test(license+' '+publicationPolicy.upstreamLicense)||/GNU (?:GENERAL PUBLIC|General Public)|Mozilla Public License|SPDX-License-Identifier:.*(?:GPL|MPL)/.test(source)))value.flags.push('copyleft_protection_review');
  if (/-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?:api[_-]?secret|secret[_-]?key)\s*[:=]\s*["'][^"']{12}/i.test(source)) fail(422,'possible_secret');
  if (/\beval\s*\(|\bexec\s*\(|\bos\.system\s*\(|\bsubprocess\.|\bWebRequest\s*\(|\bDllImport\b|AccessRights\.FullAccess|\bProcess\.Start\s*\(/i.test(source)) value.flags.push('external_execution_or_io_review');
  if (/non[- ]commercial|CC[- ]BY[- ]NC|redistribution\s+(?:is\s+)?prohibited/i.test(source)) value.flags.push('source_restriction_review');
  value.contentHash=digest(value);
  return value;
}
export function publicListing(record,includePrivate=false) {
  const r=record.releases?.[record.publishedRevision]; if (!r || record.status!=='published' || (!includePrivate&&r.draft.visibility!=='public')) return null;
  const d=r.draft;
  return {id:record.id,title:d.title,authorName:d.authorName,platform:d.platform,platformName:d.platformName,
    platformVersion:d.platformVersion,kind:d.kind,mode:d.mode,priceMinor:d.priceMinor,currency:d.currency,term:d.term,
    summary:d.summary,purpose:d.purpose,setup:d.setup,parameters:d.parameters,limitations:d.limitations,
    version:d.version,license:d.license,usageTerms:d.licenseText,
    visibility:d.visibility,accessMode:d.accessMode,sourceOrigin:d.sourceOrigin,upstreamUrl:d.upstreamUrl,upstreamLicense:d.upstreamLicense,modificationSummary:d.modificationSummary,subscriptionValue:d.subscriptionValue,
    network:'TRC20',billingInterval:d.billingInterval,accessDays:d.accessDays,platformFeeBps:2000,sellerShareBps:8000,revision:r.revision,compilation:'not_run',runtime:'not_run',
    sourceAccess:d.accessMode==='open'?'verified-email-required':'author-only',rightsStatus:'checks-passed',updatedAt:r.publishedAt};
}
function own(actor,record) { requireActor(actor); if (!record || record.ownerId!==actor.id) fail(404,'not_found'); }
/**
 * store.transaction(fn) must be durable and serializable in production.
 * tx: get(id), set(record), list(), audit(event). Test adapter is separate.
 * review(snapshot) -> {fingerprint,security:'pass|pending|reject',rights:'pass|pending|reject',evidenceRef}
 * registerProduct is idempotent by listing/version/fingerprint and must reuse BSV.
 */
export function createCreatorService({store,review,commerce,protection,accounts,clock=()=>new Date().toISOString(),ids=randomUUID}={}) {
  if (!store?.transaction) throw new Error('durable_store_adapter_required');
  async function authorizeUse(actor,record,release) {
    requireActor(actor);
    if(actor.id===record.ownerId)return null;
    const restricted=release.draft.visibility==='private'||release.draft.accessMode==='invite-only';
    if(restricted&&!hasInvitation(record,actor.id,clock()))fail(403,'invitation_required');
    if(release.draft.mode==='paid') {
      if(!commerce?.getSubscription)fail(503,'subscription_adapter_not_connected');
      const expected={actorId:actor.id,listingId:record.id,productId:release.product.id,revision:release.revision,contentHash:release.draft.contentHash};
      const subscription=await commerce.getSubscription(expected);
      if(!subscriptionIsActive(subscription,expected,clock()))fail(402,'active_subscription_required');
      const invitation=record.invitations?.[actor.id];
      return restricted&&invitation?.expiresAt?new Date(Math.min(Date.parse(subscription.expiresAt),Date.parse(invitation.expiresAt))).toISOString():subscription.expiresAt;
    }
    if(record.status!=='published')fail(404,'not_found');
    return restricted?(record.invitations?.[actor.id]?.expiresAt??null):null;
  }
  return {
    async save(actor,input,id=null,expectedRevision=0) {
      requireActor(actor); const draft=normalizeDraft(input);
      return store.transaction(async tx=>{
        let rec=id?await tx.get(id):null; if (id) own(actor,rec);
        if (rec && rec.revision!==expectedRevision) fail(409,'revision_conflict');
        if (!rec && expectedRevision!==0) fail(409,'revision_conflict');
        rec={...(rec||{id:ids(),ownerId:actor.id,releases:{},invitations:{},status:'draft',createdAt:clock()}),
          draft,revision:(rec?.revision||0)+1,updatedAt:clock(),review:null};
        // Editing never overwrites a published release or its purchase rights.
        await tx.set(rec); await tx.audit({type:'draft_saved',id:rec.id,actor:actor.id,revision:rec.revision,at:clock()});
        return {id:rec.id,revision:rec.revision,status:rec.status,hasUnpublishedChanges:true};
      });
    },
    async mine(actor) {requireActor(actor);return store.transaction(async tx=>(await tx.list()).filter(r=>r.ownerId===actor.id).map(r=>({id:r.id,title:r.draft.title,revision:r.revision,status:r.status,publishedRevision:r.publishedRevision||null,mode:r.draft.mode,visibility:r.draft.visibility,accessMode:r.draft.accessMode,priceMinor:r.draft.priceMinor,billingInterval:r.draft.billingInterval,review:r.review?{security:r.review.security,rights:r.review.rights}:null})));},
    async getOwn(actor,id) {return store.transaction(async tx=>{const r=await tx.get(id);own(actor,r);return {id:r.id,revision:r.revision,status:r.status,draft:r.draft};});},
    async publish(actor,id,expectedRevision) {
      requireActor(actor);
      const snap=await store.transaction(async tx=>{const r=await tx.get(id);own(actor,r);if(r.revision!==expectedRevision)fail(409,'revision_conflict');return structuredClone(r);});
      if (!review) fail(503,'review_adapter_not_connected');
      const verdict=await review({listingId:id,ownerId:actor.id,revision:snap.revision,draft:snap.draft});
      if (!verdict || verdict.fingerprint!==snap.draft.contentHash || !verdict.evidenceRef || !['pass','pending','reject'].includes(verdict.security) || !['pass','pending','reject'].includes(verdict.rights)) fail(503,'invalid_review_attestation');
      if (snap.draft.flags.length && !verdict.resolvedFlags?.every(x=>typeof x==='string')) verdict.security='pending';
      if (snap.draft.flags.some(f=>!verdict.resolvedFlags?.includes(f))) verdict.security='pending';
      if(snap.draft.sourceOrigin==='remake'&&snap.draft.mode==='paid'&&
         (verdict.commercialUseAllowed!==true||verdict.substantiveChanges!==true))verdict.rights='pending';
      if(snap.draft.flags.includes('copyleft_protection_review')&&(verdict.closedSourceAllowed!==true||verdict.sourceDisclosureRequired!==false))verdict.rights='pending';
      const approved=verdict.security==='pass'&&verdict.rights==='pass';
      let protectionReceipt=null;
      if(approved && snap.draft.accessMode!=='open') {
        if(!protection?.checkPublication)fail(503,'source_protection_adapter_not_connected');
        protectionReceipt=await protection.checkPublication({listingId:id,revision:snap.revision,ownerId:actor.id,draft:snap.draft});
        if(protectionReceipt?.fingerprint!==snap.draft.contentHash||protectionReceipt.sourceNeverDelivered!==true||protectionReceipt.expiryEnforced!==true||protectionReceipt.revocationEnforced!==true||protectionReceipt.platformRules!=='pass'||!protectionReceipt.evidenceRef||!protectionReceipt.adapterId)fail(503,'source_protection_not_verified');
      }
      let product=null;
      if (approved && snap.draft.mode==='paid') {
        if (!commerce?.registerProduct) fail(503,'commerce_adapter_not_connected');
        const expectedProduct={idempotencyKey:`traders:${id}:${snap.revision}:${snap.draft.contentHash}`,listingId:id,ownerId:actor.id,revision:snap.revision,contentHash:snap.draft.contentHash,priceMinor:snap.draft.priceMinor,...COMMERCIAL_TERMS,type:snap.draft.accessMode==='open'?'DOWNLOADABLE_SOURCE':'PROTECTED_ACCESS'};
        product=await commerce.registerProduct(expectedProduct);
        if(!productMatches(product,expectedProduct))fail(503,'commerce_product_mismatch');
      }
      return store.transaction(async tx=>{
        const rec=await tx.get(id);own(actor,rec);if(rec.revision!==snap.revision)fail(409,'revision_conflict');
        rec.review=verdict;
        if (!approved) {
          if (rec.status!=='published') rec.status=verdict.security==='reject'||verdict.rights==='reject'?'changes_requested':'pending_review';
          await tx.set(rec);return {id,status:rec.status,revision:rec.revision,publishResult:'pending_review'};
        }
        rec.releases[String(rec.revision)]={revision:rec.revision,draft:structuredClone(rec.draft),product,protectionReceipt,publishedAt:clock()};
        rec.publishedRevision=String(rec.revision);rec.status='published';rec.updatedAt=clock();
        await tx.set(rec);await tx.audit({type:'published',id,actor:actor.id,revision:rec.revision,contentHash:rec.draft.contentHash,evidenceRef:verdict.evidenceRef,at:clock()});
        return {id,status:'published',revision:rec.revision,url:`/trading/community.html?id=${encodeURIComponent(id)}`};
      });
    },
    async unpublish(actor,id,expectedRevision) {return store.transaction(async tx=>{const r=await tx.get(id);own(actor,r);if(r.revision!==expectedRevision)fail(409,'revision_conflict');r.status='unpublished';r.revision++;r.updatedAt=clock();await tx.set(r);await tx.audit({type:'unpublished',id,actor:actor.id,at:clock()});return {id,status:r.status,revision:r.revision};});},
    async catalogue() {return store.transaction(async tx=>(await tx.list()).map(publicListing).filter(Boolean));},
    async source(actor,id,revision=null) {
      requireActor(actor);
      const record=await store.transaction(tx=>tx.get(id)); if(!record)fail(404,'not_found');
      const release=record.releases[String(revision||record.publishedRevision)]; if(!release)fail(404,'release_not_found');
      if(actor.id!==record.ownerId && release.draft.accessMode!=='open')fail(403,'source_is_protected');
      await authorizeUse(actor,record,release);
      return {id,revision:release.revision,version:release.draft.version,license:release.draft.license,licenseText:release.draft.licenseText,thirdPartyNotices:release.draft.thirdPartyNotices,authorName:release.draft.authorName,files:release.draft.files};
    },
    async details(actor,id) {
      const record=await store.transaction(tx=>tx.get(id));
      if(!record||record.status!=='published')fail(404,'not_found');
      const release=record.releases[record.publishedRevision];
      if(!release)fail(404,'not_found');
      if(release.draft.visibility==='private'){
        requireActor(actor);if(actor.id!==record.ownerId&&!hasInvitation(record,actor.id,clock()))fail(404,'not_found');
      }
      return publicListing(record,true);
    },
    async grantInvitation(actor,id,input,expectedRevision) {
      requireActor(actor);
      await store.transaction(async tx=>{const r=await tx.get(id);own(actor,r);if((r.accessRevision||0)!==expectedRevision)fail(409,'access_revision_conflict');});
      if(!accounts?.resolveVerifiedUser)fail(503,'account_lookup_adapter_not_connected');
      const recipient=await accounts.resolveVerifiedUser(plain(input.email,'recipient_email',3,320));
      if(typeof recipient?.id!=='string'||!recipient.id||['__proto__','constructor','prototype'].includes(recipient.id)||recipient.emailVerified!==true||recipient.disabled)fail(422,'verified_recipient_required');
      let expiresAt=null;
      if(input.expiresAt){const t=Date.parse(input.expiresAt);if(!Number.isFinite(t)||t<=Date.parse(clock()))fail(422,'invalid_invitation_expiry');expiresAt=new Date(t).toISOString();}
      return store.transaction(async tx=>{
        const r=await tx.get(id);own(actor,r);if((r.accessRevision||0)!==expectedRevision)fail(409,'access_revision_conflict');
        r.invitations??={};r.invitations[recipient.id]={userId:recipient.id,status:'active',grantedAt:clock(),expiresAt};r.accessRevision=(r.accessRevision||0)+1;
        await tx.set(r);await tx.audit({type:'invitation_granted',id,actor:actor.id,recipientId:recipient.id,at:clock()});
        return {id,revision:r.accessRevision||0,userId:recipient.id,status:'active',expiresAt};
      });
    },
    async invitations(actor,id){return store.transaction(async tx=>{const r=await tx.get(id);own(actor,r);return {revision:r.accessRevision||0,grants:Object.values(r.invitations||{})};});},
    async revokeInvitation(actor,id,userId,expectedRevision){
      return store.transaction(async tx=>{
        const r=await tx.get(id);own(actor,r);if((r.accessRevision||0)!==expectedRevision)fail(409,'access_revision_conflict');
        if(!r.invitations?.[userId])fail(404,'invitation_not_found');
        r.invitations[userId].status='revoked';r.invitations[userId].revokedAt=clock();r.accessRevision=(r.accessRevision||0)+1;
        // Native-platform revocation must be delivered by the production outbox consumer.
        // New BSV access is denied immediately; this does NOT claim native access was revoked.
        const job={type:'protected_access_revoke',id,recipientId:userId,at:clock()};
        if(!tx.outbox)fail(503,'durable_outbox_required');await tx.outbox(job);
        await tx.set(r);await tx.audit({...job,actor:actor.id});
        return {id,revision:r.accessRevision||0,status:'revoked',nativeRevocation:'queued'};
      });
    },
    async use(actor,id,revision=null){
      requireActor(actor);const record=await store.transaction(tx=>tx.get(id));
      if(!record)fail(404,'not_found');const release=record.releases[String(revision||record.publishedRevision)];
      if(!release)fail(404,'release_not_found');
      const expiresAt=await authorizeUse(actor,record,release);
      if(release.draft.accessMode==='open')return {id,revision:release.revision,state:'source_available',sourceUrl:`/api/traders/listings/${encodeURIComponent(id)}/source?revision=${release.revision}`,expiresAt};
      if(!protection?.authorizeUse)fail(503,'source_protection_adapter_not_connected');
      const result=await protection.authorizeUse({actorId:actor.id,listingId:id,revision:release.revision,contentHash:release.draft.contentHash,expiresAt,accessMode:release.draft.accessMode});
      if(!['ready','pending'].includes(result?.state)||!result.reference)fail(503,'invalid_protection_response');
      // No third-party object, source, cookie or internal token is forwarded to the client.
      return {id,revision:release.revision,state:result.state,reference:result.reference,expiresAt,sourceVisible:false};
    },
    async checkout(actor,id,expectedPublishedRevision) {
      requireActor(actor);
      const r=await store.transaction(tx=>tx.get(id)); const release=r?.releases?.[r.publishedRevision];
      if(r?.status!=='published'||!release||release.draft.mode!=='paid')fail(404,'paid_listing_not_available');
      if(release.revision!==expectedPublishedRevision)fail(409,'published_revision_changed');
      if(actor.id===r.ownerId)fail(422,'cannot_purchase_own_listing');
      if((release.draft.visibility==='private'||release.draft.accessMode==='invite-only')&&!hasInvitation(r,actor.id,clock()))fail(403,'invitation_required');
      if(!commerce?.beginCheckout)fail(503,'commerce_adapter_not_connected');
      // Returns the existing BSV checkout; does not charge or transfer funds.
      return commerce.beginCheckout({actorId:actor.id,productId:release.product.id,listingId:id,revision:release.revision,priceMinor:release.draft.priceMinor,...COMMERCIAL_TERMS});
    }
  };
}
export function createTradersHandler({service,resolveSession,allowRequest,allowedOrigin,curatedAccess}={}) {
  const json=(value,status=200)=>new Response(JSON.stringify(value),{status,headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'private, no-store','Vary':'Cookie','X-Content-Type-Options':'nosniff'}});
  return async req=>{
    try {
      const url=new URL(req.url);const suffix=url.pathname.replace(/^\/api\/traders\/?/,'');
      if(req.method==='OPTIONS')return json({error:'cross_origin_not_allowed'},403);
      if(!service||!resolveSession||!allowRequest||!allowedOrigin)fail(503,'production_adapters_not_connected');
      const actor=await resolveSession(req);
      if(!await allowRequest({req,actor,operation:suffix}))fail(429,'rate_limited');
      if(req.method==='GET'&&suffix==='session')return json({registered:!!actor?.id,emailVerified:actor?.emailVerified===true,displayName:actor?.displayName||'',registrationUrl:'/register.html',loginUrl:'/register.html'});
      if(req.method==='GET'&&suffix==='catalogue')return json(await service.catalogue());
      const detailMatch=suffix.match(/^listings\/([\w-]+)\/details$/);
      if(req.method==='GET'&&detailMatch)return json(await service.details(actor,detailMatch[1]));
      requireActor(actor);
      if(req.method==='GET'&&suffix==='mine')return json(await service.mine(actor));
      const match=suffix.match(/^listings\/([\w-]+)(?:\/(publish|unpublish|source|checkout|use|invitations|revoke-invitation))?$/);
      if(req.method==='GET'&&match){if(match[2]==='invitations')return json(await service.invitations(actor,match[1]));if(match[2]==='source')return json(await service.source(actor,match[1],url.searchParams.get('revision')));if(!match[2])return json(await service.getOwn(actor,match[1]));}
      if(req.method==='GET'&&suffix.startsWith('curated/')){
        if(!curatedAccess)fail(503,'curated_adapter_not_connected');
        const id=suffix.slice(8);if(!/^[a-z0-9-]{3,100}$/.test(id))fail(400,'invalid_source_id');
        const response=await curatedAccess({actor,id,request:req});
        const headers=new Headers(response.headers);headers.set('Cache-Control','private, no-store');headers.set('Vary','Cookie');headers.set('X-Content-Type-Options','nosniff');return new Response(response.body,{status:response.status,headers});
      }
      if(!['POST','PUT'].includes(req.method))fail(405,'method_not_allowed');
      if(req.headers.get('Origin')!==allowedOrigin)fail(403,'origin_check_failed');
      if(!/^application\/json(?:;|$)/i.test(req.headers.get('Content-Type')||''))fail(415,'json_required');
      const reader=req.body?.getReader();let raw='';let bytes=0;const decoder=new TextDecoder();
      if(reader)while(true){const {value,done}=await reader.read();if(done)break;bytes+=value.byteLength;if(bytes>1500000){await reader.cancel();fail(413,'request_too_large');}raw+=decoder.decode(value,{stream:true});}raw+=decoder.decode();
      let body;try{body=JSON.parse(raw);}catch{fail(400,'invalid_json');}
      if(suffix==='listings'&&req.method==='POST')return json(await service.save(actor,body.draft),201);
      if(!match)fail(404,'not_found');
      const id=match[1],action=match[2];
      if(req.method==='PUT'&&!action)return json(await service.save(actor,body.draft,id,body.expectedRevision));
      if(req.method==='POST'&&action==='publish')return json(await service.publish(actor,id,body.expectedRevision));
      if(req.method==='POST'&&action==='unpublish')return json(await service.unpublish(actor,id,body.expectedRevision));
      if(req.method==='POST'&&action==='invitations')return json(await service.grantInvitation(actor,id,body,body.expectedRevision));
      if(req.method==='POST'&&action==='revoke-invitation')return json(await service.revokeInvitation(actor,id,body.userId,body.expectedRevision));
      if(req.method==='POST'&&action==='use')return json(await service.use(actor,id,body.revision));
      if(req.method==='POST'&&action==='checkout')return json(await service.checkout(actor,id,body.expectedRevision));
      fail(404,'not_found');
    } catch(e) { return json({error:e instanceof ServiceError?e.code:'service_unavailable'},e instanceof ServiceError?e.status:503); }
  };
}
