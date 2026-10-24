// Solid sign-in for Desk's optional pod mode. Bundled to ../../assets/solid-auth.js by build.mjs.
// Desk only loads this file when "Storage: Solid pod" is chosen in settings.
import { login, logout, handleIncomingRedirect, getDefaultSession, fetch } from "@inrupt/solid-client-authn-browser";
window.DeskSolidAuth = { login, logout, handleIncomingRedirect, getDefaultSession, fetch };
