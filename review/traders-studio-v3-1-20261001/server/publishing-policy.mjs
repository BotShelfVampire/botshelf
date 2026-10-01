/** Visibility, source access and billing are independent fields. No legal auto-approval. */
export const VISIBILITY = new Set(['public','private']);
export const ACCESS_MODES = new Set(['open','protected','invite-only']);
export const SOURCE_ORIGINS = new Set(['original','remake','redistribution']);
export function validatePublicationPolicy(input, error) {
  const require=(condition,code)=>{if(!condition)error(422,code);};
  require(VISIBILITY.has(input.visibility),'choose_publication_visibility');
  require(ACCESS_MODES.has(input.accessMode),'choose_source_access');
  require(SOURCE_ORIGINS.has(input.sourceOrigin),'choose_source_origin');
  if(input.currency && input.currency!=='USDT') error(422,'usdt_only');
  if(input.network && input.network!=='TRC20') error(422,'trc20_only');
  if(input.mode==='paid' && input.term && input.term!=='rolling-30-days')error(422,'monthly_subscription_required');
  if(input.mode==='paid' && input.billingInterval && input.billingInterval!=='month')error(422,'monthly_subscription_required');
  if('platformFeeBps' in input && input.platformFeeBps!==2000)error(422,'fixed_revenue_split');
  if('sellerShareBps' in input && input.sellerShareBps!==8000)error(422,'fixed_revenue_split');
  if(input.sourceOrigin==='redistribution' && input.mode==='paid')error(422,'unchanged_free_sources_must_remain_free');
  if(input.sourceOrigin!=='original' && input.rights==='original')error(422,'upstream_rights_required');
  if(input.sourceOrigin!=='original') {
    require(typeof input.upstreamUrl==='string' && input.upstreamUrl.length<=2000,'upstream_url_required');
    try {const u=new URL(input.upstreamUrl);require(u.protocol==='https:'&&!u.username&&!u.password,'invalid_upstream_url');}catch{error(422,'invalid_upstream_url');}
    require(typeof input.upstreamLicense==='string'&&input.upstreamLicense.trim().length>0&&input.upstreamLicense.length<=120,'upstream_license_required');
  }
  if(input.sourceOrigin==='remake') require(typeof input.modificationSummary==='string'&&input.modificationSummary.trim().length>=20&&input.modificationSummary.length<=6000,'substantive_changes_description_required');
  // The chosen visibility does not change any licence. Whether source disclosure is
  // required depends on the grant and delivery model; that decision belongs to review.
  if(input.mode==='paid') require(typeof input.subscriptionValue==='string'&&input.subscriptionValue.trim().length>=20&&input.subscriptionValue.length<=2000,'monthly_value_description_required');
  return {
    visibility:input.visibility,accessMode:input.accessMode,sourceOrigin:input.sourceOrigin,
    upstreamUrl:input.sourceOrigin==='original'?'':input.upstreamUrl.trim(),
    upstreamLicense:input.sourceOrigin==='original'?'':input.upstreamLicense.trim(),
    modificationSummary:input.sourceOrigin==='remake'?input.modificationSummary.trim():'',
    subscriptionValue:input.mode==='paid'?input.subscriptionValue.trim():''
  };
}
export function hasInvitation(record,userId,now) {
  if(!record.invitations||!Object.hasOwn(record.invitations,userId))return false;
  const grant=record.invitations[userId];
  return grant?.status==='active' && (grant.expiresAt===null || Date.parse(grant.expiresAt)>Date.parse(now));
}
