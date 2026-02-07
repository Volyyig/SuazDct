// scripts/sync-version.js
// This script syncs the version from package.json to Cargo.toml and tauri.conf.json
import toml from '@iarna/toml';
import fs from 'fs';
import path from 'path';

const root = process.cwd();
const pkgPath = path.join(root, 'package.json');
const cargoPath = path.join(root, 'src-tauri', 'Cargo.toml');
const tauriConfPath = path.join(root, 'src-tauri', 'tauri.conf.json');

const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
const version = pkg.version;
if (!version) {
  console.error('package.json has no version');
  process.exit(1);
}

// update Cargo.toml
const cargoRaw = fs.readFileSync(cargoPath, 'utf8');
const cargo = toml.parse(cargoRaw);
cargo.package = cargo.package || {};
(cargo.package as any).version = version;
fs.writeFileSync(cargoPath, toml.stringify(cargo), 'utf8');

// update tauri.conf.json
const tauri = JSON.parse(fs.readFileSync(tauriConfPath, 'utf8'));
tauri.version = version;
fs.writeFileSync(tauriConfPath, JSON.stringify(tauri, null, 2), 'utf8');

console.log('Synced version =>', version);