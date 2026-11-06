// Host-neutral dispatcher. Load this function once and inject local I/O and
// the connected Notion tool caller; no credentials or network client here.
(async function dispatch({io, invoke, batchSize = 6, maxExchanges = 1, allowWrites = false, onProgress = () => {}, checkPreflight}) {
  if (!Number.isInteger(batchSize) || batchSize < 1 || batchSize > 20 ||
      !Number.isInteger(maxExchanges) || maxExchanges < 1 || maxExchanges > 100) {
    throw new Error('BRIDGE_INVALID_LIMIT');
  }
  const summaries = [];
  let actualNotionCalls = 0;
  await io('lock', {});
  try {
    for (let exchange = 0; exchange < maxExchanges; exchange++) {
      let work = await io('prepare', {allowWrites});
      if (work.status === 'already_completed') break;
      while (work.status === 'ready') {
        if (work.preflight) {
          if (!checkPreflight) throw new Error('BRIDGE_PREFLIGHT_REQUIRED');
          await checkPreflight(work.preflight);
        }
        const selected = work.pending.slice(0, batchSize);
        const claimed = await io('claim', {requestId: work.requestId, indexes: selected.map(x => x.index)});
        actualNotionCalls += claimed.length;
        // Persist each result as it arrives, before starting the next batch.
        // An interrupted/throwing call remains claimed and is never auto-replayed.
        const settled = await Promise.allSettled(claimed.map(async item => {
          let result;
          try { result = await invoke(item.tool, item.args); }
          catch { throw new Error('BRIDGE_CALL_UNCERTAIN'); }
          await io('record', {requestId: work.requestId, index: item.index, result});
        }));
        const failed = settled.find(x => x.status === 'rejected');
        if (failed) throw new Error('BRIDGE_UNRESOLVED_CALL');
        work = await io('prepare', {allowWrites});
        await onProgress({requestId: work.requestId, completed: work.completed, total: work.total});
      }
      if (work.status !== 'complete') throw new Error('BRIDGE_UNRESOLVED_CALL');
      const summary = await io('finish', {requestId: work.requestId});
      summaries.push(summary);
      // The Python worker may not have published its next request yet.
      // No hidden polling or long-running background loop; call again if needed.
    }
    return {exchanges: summaries, actualNotionCalls};
  } finally {
    await io('unlock', {});
  }
})
