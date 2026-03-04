const fs = require('fs-extra');
const path = require('path');
const { execSync } = require('child_process');


const crmAppPath = path.resolve(__dirname, '../../crm/frontend');
const frappeUIPath = path.resolve(__dirname, '../../crm/frappe-ui');
const overrideSrcPath = path.resolve(__dirname, './src');
const overrideFilesPath = path.resolve(__dirname, './src_override');
const overridefrappeUIPath = path.resolve(__dirname, '../frappe-ui');

console.log('Starting  :  Copying original src.');
fs.copySync(path.join(crmAppPath, 'src'), overrideSrcPath);
console.log('Completed :  Copying original src.');

console.log('Starting  :  Copying frappe ui.');
fs.copySync(frappeUIPath, overridefrappeUIPath);
console.log('Completed :  Copying frappe ui.');

console.log('Starting  :  Overriding src.');
fs.copySync(overrideFilesPath, overrideSrcPath);
console.log('Completed :  Overriding src.');

execSync('yarn install', { stdio: 'inherit' });
