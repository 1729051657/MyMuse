"""The MyMuse sign-in page (``/web/``), in English and Simplified Chinese.

Two steps: an e-mail address, then the six-digit code the account service sends
(and, the first time, a friend's invite code if there is one — ``?invite=`` in the address
fills it in); or, for an account that set one, the password in one step. On success the
browser goes to the account's own Muse at ``<slug>.<SESSION_DOMAIN>``. The page
is served by the gateway itself so that it has no build step and no assets to keep in step.

One column on a phone; from 900px the words, the perks and the notices sit on the left and
the form on the right, both centred — the desktop app's sign-in page, not a phone column in
the middle of a wide window.
"""

from __future__ import annotations

PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MyMuse</title>
<meta name="description" content="Your personal cloud assistant. Sign in with an e-mail to work with files, browse the web and keep your tasks together.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='%235B4EE6'/%3E%3Ctext x='32' y='45' text-anchor='middle' font-family='system-ui' font-size='40' fill='white'%3EM%3C/text%3E%3C/svg%3E">
<script>try{var t=localStorage.getItem("nanomuse_theme")||"light";if(t==="system")t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";document.documentElement.dataset.theme=t}catch(e){}</script>
<style>
:root{--bg:#F3F3F5;--card:#fff;--ink:#1C1B22;--muted:#6E6B7A;--line:#E4E3EA;--accent:#5B4EE6;--accent-ink:#fff;--warn:#B23B3B}
html[data-theme=dark]{--bg:#121216;--card:#1B1B21;--ink:#F1F0F5;--muted:#9C99AA;--line:#2C2B34;--accent:#8A7DFF;--accent-ink:#0F0E16;color-scheme:dark}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 -apple-system,"PingFang SC","Noto Sans SC","Segoe UI",system-ui,sans-serif}
main{min-height:100dvh;display:flex;align-items:center;justify-content:center;padding:24px}
/* one column on a phone; from 900px the words on the left and the form on the right, like the desktop app */
.page{width:100%;max-width:440px;display:flex;flex-direction:column;gap:18px}
.words{padding:0 4px}
.card{order:1;background:var(--card);border:1px solid var(--line);border-radius:20px;padding:28px;box-shadow:0 10px 40px rgba(0,0,0,.06)}
.perks{order:2;display:grid;grid-template-columns:1fr 1fr;gap:8px;list-style:none;margin:0;padding:0}
.perks li{display:flex;gap:8px;align-items:flex-start;font-size:12.5px;line-height:1.4;color:var(--ink);opacity:.85;padding:9px 11px;border-radius:14px;background:color-mix(in srgb,var(--line) 45%,transparent)}
.perks svg{flex:none;width:16px;height:16px;color:var(--accent);margin-top:1px}
.more{order:3}
.brand{display:flex;align-items:center;gap:12px;margin-bottom:18px}
.brand-icon{display:grid;place-items:center;width:44px;height:44px;border-radius:12px;background:var(--accent);color:var(--accent-ink);font-size:26px;font-weight:700}
.brand b{font-size:20px;letter-spacing:-.01em}
.brand small{display:block;color:var(--muted);font-size:13px;margin-top:1px}
h1{font-size:22px;margin:0 0 6px;letter-spacing:-.01em}
p{margin:0 0 18px;color:var(--muted);font-size:14.5px}
.words p{margin-bottom:0}
label{display:block;font-size:13px;color:var(--muted);margin:0 0 6px}
input{width:100%;font:inherit;font-size:17px;padding:12px 14px;border:1px solid var(--line);border-radius:12px;background:transparent;color:var(--ink);outline:none}
input:focus{border-color:var(--accent);box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 20%,transparent)}
input.code{letter-spacing:.35em;text-align:center;font-variant-numeric:tabular-nums}
button{width:100%;margin-top:14px;font:inherit;font-weight:600;font-size:16px;padding:13px 16px;border:0;border-radius:12px;background:var(--accent);color:var(--accent-ink);cursor:pointer}
button[disabled]{opacity:.55;cursor:default}
button.ghost{background:transparent;color:var(--muted);font-weight:500;margin-top:6px;padding:8px}
.msg{min-height:22px;font-size:14px;margin-top:12px;color:var(--muted)}
.msg.err{color:var(--warn)}
.foot{margin-top:16px;font-size:12.5px;color:var(--muted);line-height:1.6}
.foot a{color:inherit}
.notice{margin:0 0 12px;padding:12px 14px;border:1px solid var(--line);border-radius:12px;font-size:13px;line-height:1.55;color:var(--ink)}
.notice b{display:block;margin-bottom:2px}
.notice b a{color:var(--accent);margin:0}
.notice a{color:var(--accent);text-decoration:none;margin-right:12px}
details.inv{margin-top:12px;font-size:13px;color:var(--muted)}
details.inv summary{cursor:pointer}
details.inv input{margin-top:8px;font-size:15px;text-transform:uppercase;letter-spacing:.12em}
.lang{position:fixed;top:14px;right:16px;font-size:13px;color:var(--muted);background:none;border:1px solid var(--line);border-radius:999px;padding:4px 12px;cursor:pointer;width:auto;margin:0;font-weight:500}
.tabs{display:flex;gap:4px;padding:4px;margin:0 0 16px;border-radius:14px;background:color-mix(in srgb,var(--line) 55%,transparent)}
.tabs .tab{flex:1;margin:0;padding:8px 10px;font-size:14px;font-weight:500;border-radius:10px;background:transparent;color:var(--muted)}
.tabs .tab.on{background:var(--card);color:var(--ink);box-shadow:0 1px 3px rgba(0,0,0,.08)}
.hint{font-size:12.5px;color:var(--muted);margin-top:8px;line-height:1.5}
#pass-box{margin-top:14px}
.notice.tip{border-color:color-mix(in srgb,var(--accent) 45%,var(--line));background:color-mix(in srgb,var(--accent) 7%,var(--card))}
.notice.tip a{display:inline-block;margin:6px 0 0;font-weight:600}
.hidden{display:none}
i.en,i.zh{font-style:normal}
[data-lang="zh"] i.en,[data-lang="en"] i.zh{display:none}
@media (min-width:900px){
  body{background:radial-gradient(ellipse at 18% 50%,color-mix(in srgb,var(--accent) 11%,transparent),transparent 58%) var(--bg)}
  main{padding:40px 56px}
  .page{max-width:1060px;display:grid;grid-template-columns:minmax(0,1.15fr) minmax(360px,420px);grid-template-areas:"words card" "perks card" "more card";column-gap:72px;row-gap:24px;align-items:center}
  .words{grid-area:words;align-self:end;padding:0}
  .perks{grid-area:perks;display:block}
  .perks li{font-size:14.5px;line-height:1.45;padding:0;margin:0 0 10px;background:none;opacity:.9}
  .perks svg{width:18px;height:18px;margin-top:3px}
  .more{grid-area:more;align-self:start;max-width:34em}
  .card{grid-area:card;padding:32px;align-self:center}
  .brand{margin-bottom:28px}
  h1.title{font-size:34px;margin-bottom:10px}
  .words p{font-size:16px;max-width:30em}
  .notice{font-size:13px}
}
</style>
</head>
<body data-lang="zh">
<button class="lang" id="lang" type="button">English</button>
<main>
<div class="page">
  <section class="words">
    <div class="brand"><span class="brand-icon" aria-hidden="true">M</span><div><b>MyMuse</b>
    <small><i class="zh">打开网页就能用，不用下载</i><i class="en">In the browser, nothing to install</i></small></div></div>
    <h1 class="title"><i class="zh">你的云端助手</i><i class="en">Your personal cloud assistant</i></h1>
    <p><i class="zh">整理资料、处理文件、浏览网页。用邮箱注册，让助手在自己的工作区里帮你完成任务。</i><i class="en">Organize information, work with files and browse the web. Sign up with an e-mail and give your assistant a workspace of its own.</i></p>
  </section>

  <ul class="perks">
    <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h8"/><path d="M10 19v-3.96 3.15"/><path d="M7 19h5"/><rect width="6" height="10" x="16" y="12" rx="2"/></svg><span><i class="zh">不用下载，打开浏览器就能用</i><i class="en">Nothing to install — it opens in the browser</i></span></li>
    <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/></svg><span><i class="zh">使用账号的模型额度，也可以配置自己的 key</i><i class="en">Use your account's model allowance or configure your own key</i></span></li>
    <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/></svg><span><i class="zh">文件和记忆保存在你的工作区，下次登录继续</i><i class="en">Keep files and memories in your workspace for your next visit</i></span></li>
    <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/></svg><span><i class="zh">删除、发送和付款等操作先征求你的同意</i><i class="en">Approve actions such as deleting, sending and paying before they run</i></span></li>
  </ul>

  <section class="card">
  <form id="step1">
    <div class="tabs" role="tablist">
      <button type="button" class="tab on" id="tab-code" role="tab" aria-selected="true"><i class="zh">验证码登录</i><i class="en">With a code</i></button>
      <button type="button" class="tab" id="tab-pass" role="tab" aria-selected="false"><i class="zh">密码登录</i><i class="en">With a password</i></button>
    </div>
    <label for="ident"><i class="zh">邮箱</i><i class="en">E-mail address</i></label>
    <input id="ident" name="identifier" type="email" autocomplete="username" required autofocus>
    <div id="pass-box" class="hidden">
      <label for="password"><i class="zh">密码</i><i class="en">Password</i></label>
      <input id="password" name="password" type="password" autocomplete="current-password">
      <div class="hint"><i class="zh">还没有密码？先用验证码登录，再在「账号」里设一个。</i><i class="en">No password yet? Sign in with a code first, then set one under Account.</i></div>
    </div>
    <div class="hint" id="code-hint"><i class="zh">首次验证会创建账号；已有账号验证后直接登录。</i><i class="en">Your first code creates an account. Use a code to return to an existing account.</i></div>
    <details class="inv" id="inv">
      <summary><i class="zh">有邀请码？</i><i class="en">Have an invite code?</i></summary>
      <input id="invite" name="invite" maxlength="8" autocomplete="off" spellcheck="false" placeholder="ABCD2345">
    </details>
    <button id="send" type="submit"><i class="zh">发送验证码</i><i class="en">Send the code</i></button>
    <button id="login" type="submit" class="hidden"><i class="zh">进入 MyMuse</i><i class="en">Open MyMuse</i></button>
    <div class="msg" id="msg1"></div>
  </form>

  <form id="step2" class="hidden">
    <h1><i class="zh">输入验证码</i><i class="en">Enter the code</i></h1>
    <p><i class="zh">六位数字已发到 </i><i class="en">Six digits were sent to </i><b id="to"></b></p>
    <label for="code"><i class="zh">验证码</i><i class="en">Code</i></label>
    <input id="code" class="code" name="code" inputmode="numeric" pattern="[0-9]{6}" maxlength="6" autocomplete="one-time-code" required>
    <button id="go" type="submit"><i class="zh">进入 MyMuse</i><i class="en">Open MyMuse</i></button>
    <button id="back" class="ghost" type="button"><i class="zh">换个账号</i><i class="en">Use another account</i></button>
    <div class="msg" id="msg2"></div>
  </form>
  </section>

  <section class="more">
  <div class="notice tip">
    <b><i class="zh">从一件具体的事开始</i><i class="en">Start with one specific task</i></b>
    <i class="zh">上传文件让助手整理，或提供网页链接让它收集资料。需要操作你的电脑或手机时，先在相应设备安装并连接客户端。</i>
    <i class="en">Upload a file to organize, or share a web link to research. To work on your computer or phone, first install and connect a client on that device.</i>
  </div>
  <div class="notice">
    <b><i class="zh">账号与数据</i><i class="en">Your account and data</i></b>
    <i class="zh">账号、文件、记忆和任务保存在本服务的服务器上。模型请求发送至服务配置的模型服务商。对话同步与数据共享偏好可在「数据控制」中管理。</i>
    <i class="en">This service stores your account, files, memories and tasks on its servers. Model requests go to the configured model provider. Manage conversation sync and data-sharing preferences under Data controls.</i>
    <br><a href="/privacy"><i class="zh">数据说明</i><i class="en">Data information</i></a>
    <a href="https://github.com/1729051657/MyMuse" rel="noopener"><i class="zh">源代码</i><i class="en">Source code</i></a>
  </div>
  <div class="foot">
    <i class="zh">MyMuse 基于 nanoMuse 开源项目构建，遵循 GPL-3.0-or-later 许可证，与 Meta 无关联。</i>
    <i class="en">MyMuse is built on nanoMuse under GPL-3.0-or-later and is not affiliated with Meta.</i>
  </div>
  </section>
</div>
</main>
<script>
(function(){
  var zh = /^zh/i.test(navigator.language || "");
  try { var saved = localStorage.getItem("nm-lang"); if (saved) zh = saved === "zh"; } catch (e) {}
  var body = document.body, langBtn = document.getElementById("lang");
  function setLang(z){ zh = z; body.dataset.lang = z ? "zh" : "en"; langBtn.textContent = z ? "English" : "中文";
    document.documentElement.lang = z ? "zh-CN" : "en"; try { localStorage.setItem("nm-lang", z ? "zh" : "en"); } catch (e) {} }
  setLang(zh);
  langBtn.onclick = function(){ setLang(!zh); };

  var s1 = document.getElementById("step1"), s2 = document.getElementById("step2");
  var ident = document.getElementById("ident"), code = document.getElementById("code");
  var password = document.getElementById("password"), passBox = document.getElementById("pass-box");
  var codeHint = document.getElementById("code-hint"), inv = document.getElementById("inv");
  var tabCode = document.getElementById("tab-code"), tabPass = document.getElementById("tab-pass");
  var invite = document.getElementById("invite");
  var msg1 = document.getElementById("msg1"), msg2 = document.getElementById("msg2");
  var send = document.getElementById("send"), login = document.getElementById("login"), go = document.getElementById("go");
  var mode = "code";
  function setMode(m){
    mode = m; var pw = m === "password";
    tabCode.classList.toggle("on", !pw); tabPass.classList.toggle("on", pw);
    tabCode.setAttribute("aria-selected", String(!pw)); tabPass.setAttribute("aria-selected", String(pw));
    passBox.classList.toggle("hidden", !pw); codeHint.classList.toggle("hidden", pw); inv.classList.toggle("hidden", pw);
    send.classList.toggle("hidden", pw); login.classList.toggle("hidden", !pw); show(msg1, "");
    if (pw && ident.value) password.focus();
  }
  tabCode.onclick = function(){ setMode("code"); };
  tabPass.onclick = function(){ setMode("password"); };
  function cleanInvite(v){ return (v || "").toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 8); }
  try {
    var fromUrl = cleanInvite(new URLSearchParams(location.search).get("invite"));
    if (fromUrl) { invite.value = fromUrl; inv.open = true; }
  } catch (e) {}
  var T = {
    sending: ["正在发送…", "Sending…"], sent: ["已发送", "Sent"],
    starting: ["正在准备你的 MyMuse，请稍候…", "Getting your MyMuse ready, please wait…"],
    ready: ["好了，正在进入…", "Ready, opening…"],
    network: ["网络不通，请稍后再试。", "Could not reach the server. Try again in a moment."]
  };
  function t(k){ return T[k][zh ? 0 : 1]; }
  // the relay's refusals in Chinese; English shows the relay's own sentence
  var E = {
    phone_region: "短信验证码目前只支持中国大陆手机号，海外用户请用邮箱登录。", bad_identifier: "请输入中国大陆手机号或邮箱。",
    code_wrong: "验证码不对。", code_expired: "验证码已过期，请重新发送。", code_too_often: "发送太频繁了，请几分钟后再试。",
    send_failed: "验证码没发出去，请稍后再试。", not_invited: "这个 relay 是私有的，这个账号不在名单上。",
    bad_credentials: "账号和密码不匹配。", no_password: "这个账号还没设密码，先用验证码登录，再在「账号」里设一个。", locked: "密码错得太多次了，请稍后再试，或改用验证码登录。",
    web_off: "这里没有开启网页版。", web_full: "当前注册名额已满，请联系服务运营者。",
    web_busy: "当前运行容量已满，请稍后重试或联系服务运营者。", start_failed: "没能启动你的 MyMuse，请稍后再试。",
    start_timeout: "你的 Muse 启动太久了，请稍后再试。", sign_in_again: "登录已失效，请重新登录。",
    relay_error: "账号服务没有返回凭据，请稍后再试。", relay_unreachable: "连不上账号服务，请稍后再试。"
  };
  function errText(r){ return (zh && E[r.body.error]) || r.body.message || ("HTTP " + r.status); }
  function show(el, text, err){ el.textContent = text || ""; el.className = "msg" + (err ? " err" : ""); }
  function post(url, data){
    return fetch(url, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data)})
      .then(function(r){ return r.text().then(function(txt){ var j = {}; try { j = txt ? JSON.parse(txt) : {}; } catch (e) {} return {ok: r.ok, status: r.status, body: j}; }); });
  }
  function enter(r, btn, msg){
    if (!r.ok) { btn.disabled = false; show(msg, errText(r), true); return; }
    show(msg, t("ready")); location.href = r.body.url;
  }
  s1.onsubmit = function(ev){
    ev.preventDefault();
    if (mode === "password") {
      if (!password.value) { password.focus(); return; }
      login.disabled = true; show(msg1, t("starting"));
      post("/api/web/login", {identifier: ident.value.trim(), password: password.value}).then(function(r){ enter(r, login, msg1); })
        .catch(function(){ login.disabled = false; show(msg1, t("network"), true); });
      return;
    }
    send.disabled = true; show(msg1, t("sending"));
    post("/api/web/code", {identifier: ident.value.trim()}).then(function(r){
      send.disabled = false;
      if (!r.ok) { show(msg1, errText(r), true); return; }
      document.getElementById("to").textContent = ident.value.trim();
      s1.classList.add("hidden"); s2.classList.remove("hidden"); show(msg2, t("sent")); code.value = ""; code.focus();
    }).catch(function(){ send.disabled = false; show(msg1, t("network"), true); });
  };
  s2.onsubmit = function(ev){
    ev.preventDefault(); go.disabled = true; show(msg2, t("starting"));
    post("/api/web/verify", {identifier: ident.value.trim(), code: code.value.trim(), invite: cleanInvite(invite.value)}).then(function(r){ enter(r, go, msg2); })
      .catch(function(){ go.disabled = false; show(msg2, t("network"), true); });
  };
  document.getElementById("back").onclick = function(){ s2.classList.add("hidden"); s1.classList.remove("hidden"); show(msg1, ""); ident.focus(); };
})();
</script>
</body>
</html>
"""
