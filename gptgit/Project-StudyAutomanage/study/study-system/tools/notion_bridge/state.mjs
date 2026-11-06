// Durable UTF-8 file protocol for analyzer.notion_mcp. Used through injected I/O.
// The host controls tool calls. This module never contacts Notion.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
const ALLOWED = new Set(['fetch', 'query_data_sources', 'notion_create_pages', 'notion_update_page']);
const WRITE = new Set(['notion_create_pages', 'notion_update_page']);
const idPattern = /^[a-f0-9]{32}$/;
const hash = value => crypto.createHash('sha256').update(JSON.stringify(value)).digest('hex');

async function read(file) { return JSON.parse((await fs.readFile(file, 'utf8')).replace(/^\uFEFF/, '')); }
async function atomic(file, value) {
  const temp = file + '.' + crypto.randomUUID() + '.tmp';
  await fs.mkdir(path.dirname(file), {recursive: true});
  await fs.writeFile(temp, JSON.stringify(value), 'utf8');
  await fs.rename(temp, file);
}
function compact(result) {
  if (!result || typeof result !== 'object' || Array.isArray(result)) throw new Error('BRIDGE_INVALID_RESULT');
  if (result.structuredContent != null) return {structuredContent: result.structuredContent, isError: !!result.isError};
  return {content: result.content || [], isError: !!result.isError};
}
function hasAsync(result) {
  let payload = result.structuredContent;
  if (!payload) {
    const item = result.content?.find(x => x.type === 'text');
    try { payload = JSON.parse(item?.text || '{}'); } catch { payload = {}; }
  }
  return !!payload?.async_task;
}

class State {
  constructor(directory) {
    this.root = path.resolve(directory);
    this.journals = path.join(this.root, 'dispatch');
    this.lockFile = path.join(this.root, 'dispatcher.lock');
    this.token = crypto.randomUUID();
    this.owned = false;
    this.uploads = new Map();
  }
  async lock() {
    await fs.mkdir(this.root, {recursive: true});
    try { await fs.writeFile(this.lockFile, this.token, {encoding: 'utf8', flag: 'wx'}); }
    catch (error) { if (error.code === 'EEXIST') throw new Error('BRIDGE_DISPATCHER_LOCKED'); throw error; }
    this.owned = true;
    return {locked: true};
  }
  async unlock() {
    if (this.owned && await fs.readFile(this.lockFile, 'utf8') === this.token) await fs.unlink(this.lockFile);
    this.owned = false;
    return {locked: false};
  }
  async assertLock() {
    if (!this.owned || await fs.readFile(this.lockFile, 'utf8') !== this.token) throw new Error('BRIDGE_DISPATCHER_LOCKED');
  }
  journal(requestId) {
    if (!idPattern.test(requestId)) throw new Error('BRIDGE_INVALID_ID');
    return path.join(this.journals, requestId);
  }
  async request() {
    const raw = await read(path.join(this.root, 'request.json'));
    this.journal(raw.request_id);
    const requests = raw.requests || (raw.rpc ? [{tool: raw.rpc, args: raw.args}] : null);
    if (!Array.isArray(requests) || !requests.length || requests.some(x =>
        !ALLOWED.has(x.tool) || !x.args || typeof x.args !== 'object' || Array.isArray(x.args) ||
        x.args.allow_deleting_content)) throw new Error('BRIDGE_INVALID_REQUEST');
    return {requestId: raw.request_id, requests, single: !raw.requests, fingerprint: hash(raw),
      ...(raw.preflight ? {preflight: raw.preflight} : {})};
  }
  async manifest(requestId) { return read(path.join(this.journal(requestId), 'manifest.json')); }
  async prepare({allowWrites = false} = {}) {
    await this.assertLock();
    const req = await this.request();
    const response = path.join(this.root, req.requestId + '.json');
    try {
      await fs.access(response);
      return {status: 'already_completed', requestId: req.requestId};
    } catch (error) { if (error.code !== 'ENOENT') throw error; }
    if (!allowWrites && req.requests.some(x => WRITE.has(x.tool))) throw new Error('BRIDGE_WRITE_NOT_ENABLED');
    let manifest;
    try { manifest = await this.manifest(req.requestId); }
    catch (error) {
      if (error.code !== 'ENOENT') throw error;
      manifest = {...req, states: req.requests.map(() => 'pending')};
      await atomic(path.join(this.journal(req.requestId), 'manifest.json'), manifest);
    }
    if (manifest.fingerprint !== req.fingerprint) throw new Error('BRIDGE_REQUEST_CHANGED');
    const states = [];
    for (let index = 0; index < manifest.states.length; index++) {
      try { await fs.access(path.join(this.journal(req.requestId), index + '.json')); states.push('received'); }
      catch (error) { if (error.code !== 'ENOENT') throw error; states.push(manifest.states[index]); }
    }
    const unresolved = states.flatMap((s, i) => s === 'claimed' ? [i] : []);
    if (unresolved.length) throw new Error('BRIDGE_UNRESOLVED_CALL');
    const pending = req.requests.flatMap((x, index) => states[index] === 'pending' ? [{index, ...x}] : []);
    return {status: pending.length ? 'ready' : 'complete', requestId: req.requestId,
      pending, total: states.length, completed: states.filter(x => x === 'received').length,
      ...(req.preflight ? {preflight: req.preflight} : {})};
  }
  async claim({requestId, indexes}) {
    await this.assertLock();
    const manifest = await this.manifest(requestId);
    const req = await this.request();
    if (req.requestId !== requestId || req.fingerprint !== manifest.fingerprint) throw new Error('BRIDGE_REQUEST_CHANGED');
    if (!Array.isArray(indexes) || !indexes.length || new Set(indexes).size !== indexes.length ||
        indexes.some(i => !Number.isInteger(i) || manifest.states[i] !== 'pending')) throw new Error('BRIDGE_INVALID_CLAIM');
    for (const index of indexes) manifest.states[index] = 'claimed';
    await atomic(path.join(this.journal(requestId), 'manifest.json'), manifest);
    return indexes.map(index => ({index, ...manifest.requests[index]}));
  }
  async record({requestId, index, result}) {
    await this.assertLock();
    const manifest = await this.manifest(requestId);
    if (!Number.isInteger(index) || manifest.states[index] !== 'claimed') throw new Error('BRIDGE_INVALID_CLAIM');
    const value = compact(result);
    if (hasAsync(value)) {
      await atomic(path.join(this.journal(requestId), index + '.async.json'), value);
      throw new Error('BRIDGE_ASYNC_REQUIRES_RESOLUTION');
    }
    const file = path.join(this.journal(requestId), index + '.json');
    try {
      const previous = await read(file);
      if (hash(previous) !== hash(value)) throw new Error('BRIDGE_RESULT_CHANGED');
      return {saved: true, index};
    } catch (error) { if (error.code !== 'ENOENT') throw error; }
    await atomic(file, value);
    return {saved: true, index};
  }
  async finish({requestId}) {
    await this.assertLock();
    const manifest = await this.manifest(requestId);
    const results = [];
    for (let i = 0; i < manifest.requests.length; i++) results.push(await read(path.join(this.journal(requestId), i + '.json')));
    const response = manifest.single ? {request_id: requestId, result: results[0]} : {request_id: requestId, results};
    await atomic(path.join(this.root, requestId + '.json'), response);
    return {requestId, total: results.length, errors: results.filter(x => x.isError).length,
      responseBytes: Buffer.byteLength(JSON.stringify(response)), status: 'completed'};
  }
  // Host adapters may split large results across tool messages. Chunks are JSON
  // string segments, joined before parsing so surrogate pairs remain intact.
  async uploadStart({uploadId}) {
    if (!idPattern.test(uploadId)) throw new Error('BRIDGE_INVALID_ID');
    this.uploads.set(uploadId, []); return {ready: true};
  }
  async uploadChunk({uploadId, sequence, data}) {
    const parts = this.uploads.get(uploadId);
    if (!parts || sequence !== parts.length || typeof data !== 'string') throw new Error('BRIDGE_INVALID_CHUNK');
    parts.push(data); return {saved: true};
  }
  async uploadFinish({uploadId}) {
    const parts = this.uploads.get(uploadId);
    if (!parts) throw new Error('BRIDGE_INVALID_CHUNK');
    const args = JSON.parse(parts.join('')); this.uploads.delete(uploadId);
    return this.record(args);
  }
  async call(action, args) {
    if (!new Set(['lock', 'unlock', 'prepare', 'claim', 'record', 'finish', 'uploadStart', 'uploadChunk', 'uploadFinish']).has(action))
      throw new Error('BRIDGE_INVALID_ACTION');
    return this[action](args);
  }
}
export {State, compact};
