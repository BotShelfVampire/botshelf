// Integration example only. Do not deploy until these adapters exist and pass
// the existing site's email, CSRF/session, entitlement and persistence tests.
import {createCreatorService,createTradersHandler} from './creator-core.mjs';
// Supply adapters from the AUTHORITATIVE existing BSV source. Do not replace
// existing auth with localStorage, a JSON emailVerified field or a test cookie.
export function buildTradersEndpoint(adapters) {
 const service=createCreatorService({store:adapters.store,review:adapters.review,commerce:adapters.commerce,protection:adapters.protection,accounts:adapters.accounts});
 return createTradersHandler({service,resolveSession:adapters.resolveSession,allowRequest:adapters.allowRequest,allowedOrigin:adapters.allowedOrigin,curatedAccess:adapters.curatedAccess});
}
