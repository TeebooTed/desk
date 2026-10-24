// QR codes for Desk's "Connect another computer" (pod mode). Bundled to ../../assets/qrcode.js by build.mjs; loaded only when needed.
import qrcode from "qrcode-generator";
window.DeskQR = (text) => { const q = qrcode(0, "M"); q.addData(text); q.make(); return q.createSvgTag({ cellSize: 4, margin: 2, scalable: true }); };
