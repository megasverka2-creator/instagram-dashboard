// ============================================================================
//  RestoPulse — AI xarajat hisoblovchi ("maosh")
//  Har AI so'rovdan keyin token'dan dollarni hisoblab, agentga bog'lab saqlaydi.
//  Sonnet 4.6: $3 / 1M input token, $15 / 1M output token.
//  Hammasi shu brauzerda (localStorage). Boshlang'ich balans tahminiy.
// ============================================================================
(function () {
  "use strict";
  const STORE = "rp_ai_xarajat";
  const IN_RATE = 3 / 1e6;    // $ / input token
  const OUT_RATE = 15 / 1e6;  // $ / output token

  function load() {
    try { return JSON.parse(localStorage.getItem(STORE) || "{}"); } catch (e) { return {}; }
  }
  function save(d) { try { localStorage.setItem(STORE, JSON.stringify(d)); } catch (e) {} }

  // Anthropic javobidagi usage'dan xarajatni hisoblab, agentga qo'shadi
  function record(agentId, usage) {
    if (!usage) return 0;
    const inT = usage.input_tokens || 0;
    const outT = usage.output_tokens || 0;
    const cost = inT * IN_RATE + outT * OUT_RATE;
    const d = load();
    const today = new Date().toISOString().slice(0, 10);
    d[agentId] = d[agentId] || { total: 0, today: 0, todayDate: today, calls: 0, inTok: 0, outTok: 0 };
    const a = d[agentId];
    if (a.todayDate !== today) { a.today = 0; a.todayDate = today; }
    a.total += cost; a.today += cost; a.calls += 1;
    a.inTok += inT; a.outTok += outT;
    save(d);
    return cost;
  }

  // Bitta agent ma'lumoti
  function get(agentId) {
    const d = load();
    const today = new Date().toISOString().slice(0, 10);
    const a = d[agentId];
    if (!a) return { total: 0, today: 0, calls: 0 };
    if (a.todayDate !== today) return { ...a, today: 0 };
    return a;
  }

  // Jami sarflangan (barcha agentlar)
  function totalSpent() {
    const d = load();
    return Object.values(d).reduce((s, a) => s + (a.total || 0), 0);
  }

  // $ formatlash
  function fmtUsd(v) {
    if (v < 0.01 && v > 0) return "$" + v.toFixed(4);
    return "$" + (v || 0).toFixed(2);
  }

  window.RP_Cost = { record, get, totalSpent, fmtUsd, IN_RATE, OUT_RATE };
})();
