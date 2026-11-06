const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
let State;
const stateReady = import('../tools/notion_bridge/state.mjs').then(module => {State = module.State;});
const moduleDirectory = path.resolve(__dirname, '../tools/notion_bridge');
const source = fs.readFile(path.join(moduleDirectory, 'dispatch.js'), 'utf8');

async function fixture(t, requests, single = false) {
  await stateReady;
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'notion-bridge-'));
  t.after(() => fs.rm(directory, {recursive: true, force: true}));
  const requestId = crypto.randomUUID().replaceAll('-', '');
  const request = single ? {request_id: requestId, rpc: requests[0].tool, args: requests[0].args} :
    {request_id: requestId, requests};
  await fs.writeFile(path.join(directory, 'request.json'), JSON.stringify(request), 'utf8');
  const state = new State(directory);
  const io = (action, args) => state.call(action, args);
  const run = eval(await source);
  const response = async () => JSON.parse(await fs.readFile(path.join(directory, requestId+'.json'), 'utf8'));
  return {directory, requestId, state, io, run, response};
}
const fetchRequest = id => ({tool: 'fetch', args: {id}});

test('prepared preflight is required and stale package stops before claim or tool call', async t => {
  const f = await fixture(t, [fetchRequest('first')]);
  const file = path.join(f.directory, 'request.json');
  const request = JSON.parse(await fs.readFile(file, 'utf8'));
  request.preflight = {package: 'package.json'};
  await fs.writeFile(file, JSON.stringify(request));
  let calls = 0;
  const invoke = async () => {calls++; return {structuredContent: {ok: true}};};
  await assert.rejects(f.run({io:f.io, invoke}), /BRIDGE_PREFLIGHT_REQUIRED/);
  await assert.rejects(f.run({io:f.io, invoke, checkPreflight:async () => {throw new Error('STALE');}}), /STALE/);
  assert.equal(calls, 0);
  const manifest = JSON.parse(await fs.readFile(path.join(f.directory,'dispatch',f.requestId,'manifest.json'),'utf8'));
  assert.deepEqual(manifest.states, ['pending']);
  const result = await f.run({io:f.io, invoke, checkPreflight:async value => {assert.equal(value.package,'package.json');}});
  assert.equal(result.actualNotionCalls, 1);
});

test('out-of-order replies preserve request order and unicode, no replay on repeat', async t => {
  const f = await fixture(t, [fetchRequest('first'), fetchRequest('second')]);
  let calls = 0;
  const invoke = async (_, args) => {
    calls++;
    if (args.id === 'first') await new Promise(resolve => setTimeout(resolve, 10));
    return {structuredContent: {text: args.id+' 한글 “인용” C:\\자료\\😀'}, content: [{type: 'text', text: 'duplicate'}]};
  };
  const result = await f.run({io: f.io, invoke});
  assert.equal(result.actualNotionCalls, 2);
  const response = await f.response();
  assert.match(response.results[0].structuredContent.text, /^first/);
  assert.match(response.results[1].structuredContent.text, /^second/);
  assert.equal(response.results[0].content, undefined);
  assert.equal((await f.run({io: f.io, invoke})).actualNotionCalls, 0);
  assert.equal(calls, 2);
});

test('saved results survive interruption and uncertain write is not replayed', async t => {
  const f = await fixture(t, [fetchRequest('saved'),
    {tool: 'notion_update_page', args: {page_id: 'existing', command: 'replace_content', new_str: '학습'}}]);
  let calls = 0;
  await assert.rejects(f.run({io: f.io, allowWrites: true, batchSize: 1, invoke: async name => {
    calls++;
    if (name === 'notion_update_page') throw Error('lost after sending');
    return {structuredContent: {text: 'saved'}};
  }}), /BRIDGE_UNRESOLVED_CALL/);
  const saved = JSON.parse(await fs.readFile(path.join(f.directory,'dispatch',f.requestId,'0.json'),'utf8'));
  assert.equal(saved.structuredContent.text, 'saved');
  const resumed = new State(f.directory);
  await assert.rejects(f.run({io: (a,b) => resumed.call(a,b), allowWrites: true, invoke: async () => {calls++;}}), /BRIDGE_UNRESOLVED_CALL/);
  assert.equal(calls, 2);
  // Explicitly resolved response, after checking actual remote state, can finish.
  await resumed.lock();
  await resumed.record({requestId:f.requestId,index:1,result:{structuredContent:{page_id:'existing'}}});
  await resumed.unlock();
  const complete = await f.run({io: f.io, allowWrites:true, invoke:async()=>{throw Error('must not replay');}});
  assert.equal(complete.actualNotionCalls, 0);
  assert.equal((await f.response()).results.length, 2);
});

test('write authorization and allowlist are enforced before dispatch', async t => {
  const f = await fixture(t, [{tool:'notion_create_pages',args:{pages:[]}}]);
  let calls = 0;
  await assert.rejects(f.run({io:f.io,invoke:async()=>{calls++;}}), /BRIDGE_WRITE_NOT_ENABLED/);
  assert.equal(calls, 0);
  const g = await fixture(t, [{tool:'delete_everything',args:{}}]);
  await assert.rejects(g.run({io:g.io,invoke:async()=>{calls++;}}), /BRIDGE_INVALID_REQUEST/);
  assert.equal(calls, 0);
});

test('one dispatcher owns a bridge directory; invalid IDs cannot escape it', async t => {
  const f = await fixture(t,[fetchRequest('safe')]);
  await f.state.lock();
  const other = new State(f.directory);
  await assert.rejects(other.lock(),/BRIDGE_DISPATCHER_LOCKED/);
  assert.throws(()=>f.state.journal('../outside'),/BRIDGE_INVALID_ID/);
  await f.state.unlock();
});

test('request changes after preparation are detected before calling tools', async t => {
  const f = await fixture(t,[fetchRequest('first')]);
  await f.state.lock();
  await f.state.prepare();
  await fs.writeFile(path.join(f.directory,'request.json'),JSON.stringify({request_id:f.requestId,requests:[fetchRequest('changed')]}));
  await assert.rejects(f.state.claim({requestId:f.requestId,indexes:[0]}),/BRIDGE_REQUEST_CHANGED/);
  await f.state.unlock();
});

test('legacy single-request protocol and tool errors retain their envelope', async t => {
  const f = await fixture(t,[fetchRequest('single')],true);
  await f.run({io:f.io,invoke:async()=>({isError:true,content:[{type:'text',text:'tool error'}]})});
  const response = await f.response();
  assert.equal(response.result.isError,true);
  assert.equal(response.results,undefined);
});

test('null structured response preserves the text JSON used by Notion queries', async t => {
  const f = await fixture(t,[fetchRequest('text-only')]);
  await f.run({io:f.io,invoke:async()=>({structuredContent:null,content:[{type:'text',text:'{"results":[],"has_more":false}'}]})});
  assert.equal(JSON.parse((await f.response()).results[0].content[0].text).has_more,false);
});

test('queued async task is saved for resolution, not returned as completed', async t => {
  const f = await fixture(t,[{tool:'notion_update_page',args:{page_id:'existing',command:'replace_content',new_str:'x'}}]);
  await assert.rejects(f.run({io:f.io,allowWrites:true,invoke:async()=>({structuredContent:{async_task:{id:'task'}}})}),/BRIDGE_UNRESOLVED_CALL/);
  const saved = JSON.parse(await fs.readFile(path.join(f.directory,'dispatch',f.requestId,'0.async.json'),'utf8'));
  assert.equal(saved.structuredContent.async_task.id,'task');
  await assert.rejects(fs.access(path.join(f.directory,f.requestId+'.json')));
});

test('saved Codex adapter splits large responses and serializes node I/O', async t => {
  const f = await fixture(t,[fetchRequest('large'),fetchRequest('small')]);
  const requestFile = path.join(f.directory,'request.json');
  const request = JSON.parse(await fs.readFile(requestFile,'utf8'));
  request.preflight = {python:'C:/Python/python.exe',package:"C:/자료/it's a package.json",root:'C:/자료',python_path:'C:/deps'};
  await fs.writeFile(requestFile,JSON.stringify(request));
  const runner = eval(await fs.readFile(path.join(moduleDirectory,'run_dispatch.js'),'utf8'));
  const text = '한글 C:\\Users\\ICT “인용” 😀\n'.repeat(1800);
  let active = 0, maxActive = 0, chunks = 0, preflights = 0;
  const tools = {
    exec_command: async args => {
      assert.equal(args.workdir,'C:/자료');
      assert.ok(args.cmd.includes("it''s a package.json"));
      preflights++;
      return {exit_code:0};
    },
    mcp__node_repl__js: async ({code}) => {
      if (code.startsWith('var bridgeFs')) return {content:[{type:'text',text:JSON.stringify({handle:'mock',source:await source})}]};
      active++; maxActive = Math.max(maxActive,active);
      if (code.includes('uploadChunk')) chunks++;
      let output;
      try {
        await Function('bridgeStates','nodeRepl', 'return (async()=>{'+code+'})()')(new Map([['mock',f.state]]),{write:s=>{output=s;}});
      } finally {active--;}
      return {content:[{type:'text',text:output}]};
    },
    mcp__codex_apps__notion_fetch: async ({id})=>({structuredContent:{id,text:id==='large'?text:'작음'}})
  };
  const result = await runner(tools,{moduleDirectory,directory:f.directory});
  assert.equal(result.actualNotionCalls,2);
  assert.equal((await f.response()).results[0].structuredContent.text,text);
  assert.ok(chunks>1);
  assert.equal(maxActive,1);
  assert.equal(preflights,1);
});
