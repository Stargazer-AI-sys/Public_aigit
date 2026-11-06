// Codex functions.exec adapter. Load this saved function, then call with the
// enabled tools object and absolute moduleDirectory/directory paths.
// The only per-run inputs are paths, limits and explicit write authorization.
// This is not a standalone authenticated Notion client.
(async function runDispatch(tools, {moduleDirectory, directory, allowWrites = false, batchSize = 6, maxExchanges = 1, onProgress}) {
  const nodeTool = tools.mcp__node_repl__js;
  if (!nodeTool) throw new Error('BRIDGE_NODE_TOOL_UNAVAILABLE');
  const mapping = {fetch: 'mcp__codex_apps__notion_fetch',
    query_data_sources: 'mcp__codex_apps__notion_query_data_sources',
    notion_create_pages: 'mcp__codex_apps__notion_notion_create_pages',
    notion_update_page: 'mcp__codex_apps__notion_notion_update_page'};
  function parse(result) {
    if (result.isError) throw new Error('BRIDGE_LOCAL_IO_ERROR');
    for (const item of result.content || []) {
      if (item.type === 'text') { try { return JSON.parse(item.text); } catch {} }
    }
    throw new Error('BRIDGE_LOCAL_IO_ERROR');
  }
  async function node(code) {
    const value = parse(await nodeTool({code, title: '저장된 Notion 전달 코드 실행'}));
    if (value.bridgeError) throw new Error(value.bridgeError);
    return value;
  }
  const setup = await node(`var bridgeFs = await import('node:fs/promises');
var bridgePath = await import('node:path'); var bridgeUrl = await import('node:url');
var bridgeModuleDir = bridgePath.resolve(${JSON.stringify(moduleDirectory)});
var bridgeStateModule = await import(bridgeUrl.pathToFileURL(bridgePath.join(bridgeModuleDir,'state.mjs')).href);
var bridgeStates = typeof bridgeStates === 'undefined' ? new Map() : bridgeStates;
var bridgeInstance = new bridgeStateModule.State(${JSON.stringify(directory)});
bridgeStates.set(bridgeInstance.token, bridgeInstance);
nodeRepl.write(JSON.stringify({handle:bridgeInstance.token,source:await bridgeFs.readFile(bridgePath.join(bridgeModuleDir,'dispatch.js'),'utf8')}));`);
  const dispatch = eval(setup.source);
  // node_repl is a single persistent runtime; serialize its I/O, while Notion
  // calls can run independently up to batchSize.
  let queue = Promise.resolve();
  function serial(work) {
    const next = queue.then(work); queue = next.catch(() => {}); return next;
  }
  function call(action, args) {
    return node(`try {nodeRepl.write(JSON.stringify(await bridgeStates.get(${JSON.stringify(setup.handle)}).call(${JSON.stringify(action)},${JSON.stringify(args)})));}
catch(error){nodeRepl.write(JSON.stringify({bridgeError:/^BRIDGE_[A-Z_]+$/.test(error.message)?error.message:'BRIDGE_LOCAL_IO_ERROR'}));}`);
  }
  const io = (action, args) => serial(async () => {
    const encoded = JSON.stringify(args);
    if (action !== 'record' || encoded.length <= 12000) return call(action, args);
    const uploadId = args.requestId; // transfers serialized, one active upload
    await call('uploadStart', {uploadId});
    let sequence = 0;
    for (let i = 0; i < encoded.length;) {
      let end = Math.min(i + 12000, encoded.length);
      if (end < encoded.length && /[\uD800-\uDBFF]/.test(encoded[end - 1])) end--;
      await call('uploadChunk', {uploadId, sequence: sequence++, data: encoded.slice(i, end)});
      i = end;
    }
    return call('uploadFinish', {uploadId});
  });
  const invoke = async (name, args) => {
    const tool = tools[mapping[name]];
    if (!tool) throw new Error('BRIDGE_NOTION_TOOL_UNAVAILABLE');
    const result = await tool(args);
    // Keep one representation, not both text and structured duplicates.
    return result.structuredContent != null ?
      {structuredContent: result.structuredContent, isError: !!result.isError} :
      {content: result.content || [], isError: !!result.isError};
  };
  const checkPreflight = async metadata => {
    if (!tools.exec_command) throw new Error('BRIDGE_PREFLIGHT_RUNNER_UNAVAILABLE');
    const quote = value => "'"+String(value).replaceAll("'", "''")+"'";
    const code = 'import sys; from analyzer.notion_prepared import load,validate; validate(load(sys.argv[1]))';
    const value = await tools.exec_command({
      cmd: '$env:PYTHONPATH='+quote(metadata.python_path || '')+'; & '+quote(metadata.python)+
           ' -X utf8 -c '+quote(code)+' '+quote(metadata.package),
      workdir:metadata.root, max_output_tokens:500});
    if (value.exit_code !== 0) throw new Error('BRIDGE_PREPARED_PACKAGE_STALE');
  };
  try { return await dispatch({io, invoke, allowWrites, batchSize, maxExchanges, onProgress, checkPreflight}); }
  finally {
    await node(`bridgeStates.delete(${JSON.stringify(setup.handle)});nodeRepl.write(JSON.stringify({closed:true}));`);
  }
})
