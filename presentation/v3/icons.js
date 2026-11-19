// Renders Lucide icons (react-icons/lu) to PNG with sharp, cached in presentation/v3/icons/.
const fs = require("fs");
const path = require("path");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const sharp = require("sharp");
const LU = require("react-icons/lu");
const DIR = path.join(__dirname, "icons");
fs.mkdirSync(DIR, { recursive: true });

async function icon(name, hex, px = 256, stroke) {
  const file = path.join(DIR, `${name}_${hex}_${px}.png`);
  if (fs.existsSync(file)) return file;
  const C = LU["Lu" + name];
  if (!C) throw new Error("no icon " + name);
  let svg = renderToStaticMarkup(React.createElement(C, { size: px, color: "#" + hex, strokeWidth: stroke || 1.9 }));
  if (!svg.includes("xmlns=")) svg = svg.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"');
  await sharp(Buffer.from(svg), { density: 300 }).resize(px, px).png().toFile(file);
  return file;
}
module.exports = { icon };
