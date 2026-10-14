/* Derksen Index — front end.
   Reads the lemma list from data/lemmata.csv (columns: lemma, gloss, page).
   Edit that file to correct spellings; no change to this script is needed. */
(function(){
'use strict';

var DATA_URL='data/lemmata.csv';
var ENTRIES=[]; // [lemma, gloss, page]

// RFC 4180 CSV: commas, quotes ("") and line breaks inside quoted fields; tolerates a BOM, CRLF and blank lines
function parseCSV(text){
  text=text.replace(/^\uFEFF/,'');
  var rows=[],row=[],field='',i=0,q=false,c;
  for(;i<text.length;i++){
    c=text[i];
    if(q){
      if(c==='"'){ if(text[i+1]==='"'){field+='"';i++;} else q=false; }
      else field+=c;
    }else if(c==='"')q=true;
    else if(c===','){row.push(field);field='';}
    else if(c==='\n'||c==='\r'){
      if(c==='\r'&&text[i+1]==='\n')i++;
      row.push(field);field='';
      if(row.length>1||row[0]!=='')rows.push(row);
      row=[];
    }else field+=c;
  }
  row.push(field);if(row.length>1||row[0]!=='')rows.push(row);
  return rows;
}

// map rows to entries by header name, so column order in the CSV does not matter
function toEntries(rows){
  var head=rows.shift().map(function(h){return h.trim().toLowerCase();});
  var L=head.indexOf('lemma'),G=head.indexOf('gloss'),P=head.indexOf('page');
  if(L<0||P<0)throw new Error('lemmata.csv needs the columns lemma, gloss, page (found: '+head.join(', ')+')');
  return rows.map(function(r){
    return [(r[L]||'').trim().normalize('NFC'),G<0?'':(r[G]||'').trim(),parseInt(r[P],10)];
  }).filter(function(e){return e[0]&&!isNaN(e[2]);});
}


function getUrl(p){return 'https://archive.org/details/etymological-dictionary-of-the-slavic-inherited-lexicon/page/'+p+'/mode/1up';}

function normalize(s){
  s=s.replace(/^[*]/,'');
  s=s.normalize('NFD').replace(/[̀-ͯ]/g,'');
  s=s.replace(/[ъь]/g,'');
  return s.toLowerCase();
}
function rev(s){return s.split('').reverse().join('');}
function rhymeKey(hw){return rev(normalize(hw));}

function trigrams(s){var t=new Set(),p='  '+s.toLowerCase()+'  ';for(var i=0;i<p.length-2;i++)t.add(p.slice(i,i+3));return t;}
function trigramSim(a,b){var ta=trigrams(a),tb=trigrams(b),n=0;ta.forEach(function(g){if(tb.has(g))n++;});return 2*n/(ta.size+tb.size||1);}

function scoreFuzzy(q,hw,gloss){
  var qn=normalize(q),hwl=hw.toLowerCase(),hwn=normalize(hw),glo=gloss.toLowerCase(),s=0;
  if(hwl.startsWith(q)||hwl.startsWith('*'+q))s+=5;
  if(hwn.startsWith(qn))s+=3;
  if(hwl.includes(q))s+=2;
  if(hwn.includes(qn))s+=1.5;
  if(glo.includes(q))s+=2.5;
  s+=trigramSim(qn,hwn)*3;s+=trigramSim(q,glo)*2;
  return s;
}
function searchFuzzy(query){
  query=query.trim();if(!query)return[];
  var ql=query.toLowerCase(),r=[];
  ENTRIES.forEach(function(e){var s=scoreFuzzy(ql,e[0],e[1]);if(s>0.4)r.push({hw:e[0],gloss:e[1],page:e[2],s:s});});
  r.sort(function(a,b){return b.s-a.s;});return r.slice(0,60);
}

var rhymeIndex=null;
function buildRhymeIndex(){
  if(rhymeIndex)return;
  rhymeIndex=ENTRIES.map(function(e){return{hw:e[0],gloss:e[1],page:e[2],rk:rhymeKey(e[0])};});
  rhymeIndex.sort(function(a,b){return a.rk<b.rk?-1:a.rk>b.rk?1:0;});
}
function searchRhyme(query){
  query=query.trim();if(!query)return[];
  buildRhymeIndex();
  var q=rev(normalize(query.replace(/^[*-]+/,'')));
  if(!q)return[];
  var r=[];
  rhymeIndex.forEach(function(e){
    var rk=e.rk,m=0;
    while(m<q.length&&m<rk.length&&q[m]===rk[m])m++;
    if(m>=1){var s=m*3+trigramSim(q,rk)*2;if(s>1)r.push({hw:e.hw,gloss:e.gloss,page:e.page,s:s,match:m});}
  });
  r.sort(function(a,b){return b.match-a.match||b.s-a.s;});return r.slice(0,60);
}

function escHtml(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
// match on the normalized form (no accents, no jers), then mark the matching span of the original text
function foldChar(ch){return ch.normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/[ъь]/g,'').toLowerCase();}
function highlight(text,query){
  var q=normalize(query.trim());if(!q)return escHtml(text);
  var chars=Array.from(text),flat='',map=[];
  chars.forEach(function(ch,i){var f=foldChar(ch);for(var j=0;j<f.length;j++){flat+=f[j];map.push(i);}});
  var on=new Array(chars.length).fill(false),from=0,at;
  while((at=flat.indexOf(q,from))>-1){
    var a=map[at],b=map[at+q.length-1];
    while(b+1<chars.length&&/^[̀-ͯ]+$/.test(chars[b+1]))b++; // keep a following combining accent with its letter
    for(var k=a;k<=b;k++)on[k]=true;from=at+q.length;
  }
  var html='',open=false;
  chars.forEach(function(ch,i){if(on[i]&&!open){html+='<mark>';open=true;}else if(!on[i]&&open){html+='</mark>';open=false;}html+=escHtml(ch);});
  return html+(open?'</mark>':'');
}
// rhyme matches count normalized letters; walk back over the raw headword so accents and jers stay inside the mark
function highlightSuffix(hw,matchLen){
  if(matchLen<=0)return escHtml(hw);
  var i=hw.length,n=0;
  while(i>0&&n<matchLen){
    var ch=hw[i-1];i--;
    if(normalize(ch).length)n++;
  }
  while(i>0&&!normalize(hw[i-1]).length&&hw[i-1]!==' '&&hw[i-1]!==';'&&hw[i-1]!=='*')i--;
  return escHtml(hw.slice(0,i))+'<mark>'+escHtml(hw.slice(i))+'</mark>';
}

var $=function(id){return document.getElementById(id);};
var out=$('search-output'),fullEl=$('full-index'),statusEl=$('status'),countEl=$('count'),hintEl=$('hint');
var queryEl=$('query'),clearBtn=$('clearBtn'),toggleBtn=$('toggleIndex'),tabFuzzy=$('tab-fuzzy'),tabRhyme=$('tab-rhyme');
var currentMode='fuzzy',indexVisible=false,debounce=null,sel=-1;
var HOVER=matchMedia('(hover: hover)').matches;
var TOTAL='';

function setStatus(html){statusEl.innerHTML=html||'';}
function showDisc(){
  out.innerHTML='';out.append($('disc').content.cloneNode(true));
  countEl.textContent=TOTAL+' lemmata';
  setStatus('');
}

function renderResults(results,query,mode){
  sel=-1;
  if(!query.trim()){showDisc();return;}
  if(!results.length){
    out.innerHTML='<div class="state"><p class="lead">No matches for “'+escHtml(query)+'”</p><p>Try fewer letters, drop the accents, or switch to '+(mode==='rhyme'?'fuzzy':'rhyme')+' search.</p></div>';
    countEl.textContent='0 results';setStatus('');return;
  }
  var n=results.length;
  countEl.textContent=(n===60?'Top 60':n)+(mode==='rhyme'?' rhyme':'')+' result'+(n!==1?'s':'');
  setStatus(HOVER?'↑ ↓ to move · Enter opens the page on archive.org':'Tap a lemma to open its page on archive.org');
  out.innerHTML='<ul class="results">'+results.map(function(r,i){
    var hwHtml=mode==='rhyme'?highlightSuffix(r.hw,r.match||0):highlight(r.hw,query);
    var glossHtml=mode==='rhyme'?escHtml(r.gloss):highlight(r.gloss,query);
    return '<li><a class="r" href="'+escHtml(getUrl(r.page))+'" target="_blank" rel="noopener" style="animation-delay:'+Math.min(i*0.018,0.5)+'s">'
      +'<span class="r-text"><span class="r-hw">'+hwHtml+'</span>'+(r.gloss?'<span class="r-gloss">'+glossHtml+'</span>':'')+'</span>'
      +'<span class="r-page" aria-label="page '+r.page+'"><small>p.</small><span>'+r.page+'</span></span></a></li>';
  }).join('')+'</ul>';
}

var indexBuilt=false;
function buildFullIndex(){
  if(indexBuilt)return;indexBuilt=true;
  var sections={};
  ENTRIES.forEach(function(e){
    var body=e[0].replace(/^[*]/,''),norm=body.normalize('NFD'),base=norm[0].toUpperCase();
    var key=/[A-Z]/.test(base)?base:body[0].toUpperCase();
    (sections[key]=sections[key]||[]).push(e);
  });
  var letters=Object.keys(sections).sort();
  var jump='<nav class="jump" aria-label="Jump to letter">'+letters.map(function(l){return '<a class="k sm" href="#ix-'+encodeURIComponent(l)+'">'+escHtml(l.toLowerCase())+'</a>';}).join('')+'</nav>';
  fullEl.innerHTML=jump+letters.map(function(l){
    var items=sections[l].map(function(e){
      return '<a class="ix" href="'+escHtml(getUrl(e[2]))+'" target="_blank" rel="noopener" title="'+escHtml(e[0]+(e[1]?' — '+e[1]:''))+'">'
        +'<span class="hw">'+escHtml(e[0])+'</span><span class="dots"></span><span class="pg">'+e[2]+'</span></a>';
    }).join('');
    return '<div class="sec" id="ix-'+escHtml(l)+'"><div class="sec-head"><b>*'+escHtml(l.toLowerCase())+'</b><span>'+sections[l].length+' lemmata</span></div><div class="grid">'+items+'</div></div>';
  }).join('');
  fullEl.querySelectorAll('.jump a').forEach(function(a){
    a.addEventListener('click',function(ev){ev.preventDefault();var t=document.getElementById(decodeURIComponent(a.getAttribute('href').slice(1)));if(t)t.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});});
  });
}

function run(){var q=queryEl.value;renderResults(currentMode==='rhyme'?searchRhyme(q):searchFuzzy(q),q,currentMode);}

function setIndex(on){
  indexVisible=on;
  toggleBtn.setAttribute('aria-pressed',on);
  if(on){buildFullIndex();fullEl.hidden=false;out.hidden=true;countEl.textContent=TOTAL+' lemmata';setStatus('Every lemma, alphabetically · click any entry to open its page');}
  else{fullEl.hidden=true;out.hidden=false;run();}
}

function setMode(mode,silent){
  currentMode=mode;
  tabFuzzy.setAttribute('aria-selected',mode==='fuzzy');
  tabRhyme.setAttribute('aria-selected',mode==='rhyme');
  if(mode==='rhyme'){hintEl.innerHTML='<b>Rhyme</b> finds lemmata with the same ending';setPh('-nъ');}
  else{hintEl.innerHTML='<b>Fuzzy</b> matches lemmata and English glosses';randomPlaceholder();}
  if(indexVisible)setIndex(false);else if(!silent)run();
}

// fuzzy placeholder: a random lemma or its gloss, cross-faded every 6 seconds
var phEl=$('ph'),phTimer=null;
function setPh(s){clearTimeout(phTimer);phEl.textContent=s;phEl.classList.remove('out');}
function pickPlaceholder(){
  for(var tries=0;tries<20;tries++){
    var e=ENTRIES[Math.floor(Math.random()*ENTRIES.length)];
    var s=(Math.random()<0.5||!e[1])?e[0].split(';')[0].trim():e[1].split(',')[0].trim();
    if(s&&s.length<=18&&s!==phEl.textContent)return s;
  }
  return phEl.textContent;
}
function randomPlaceholder(){setPh(pickPlaceholder());}
// fade out, swap, fade in
function cyclePlaceholder(){
  phEl.classList.add('out');
  clearTimeout(phTimer);
  phTimer=setTimeout(function(){if(currentMode==='fuzzy'){phEl.textContent=pickPlaceholder();}phEl.classList.remove('out');},800);
}

function onInput(){
  var q=queryEl.value;clearBtn.hidden=!q.length;phEl.hidden=!!q.length;
  if(indexVisible&&q.length)setIndex(false);
  clearTimeout(debounce);debounce=setTimeout(run,80);
}

function moveSel(d){
  var items=out.querySelectorAll('.r');if(!items.length)return;
  if(sel>=0&&items[sel])items[sel].classList.remove('sel');
  sel=Math.max(0,Math.min(items.length-1,sel+d));
  items[sel].classList.add('sel');items[sel].scrollIntoView({block:'nearest'});
}

tabFuzzy.addEventListener('click',function(){setMode('fuzzy');queryEl.focus();});
tabRhyme.addEventListener('click',function(){setMode('rhyme');queryEl.focus();});
toggleBtn.addEventListener('click',function(){
  if(!indexVisible){queryEl.value='';clearBtn.hidden=true;phEl.hidden=false;}
  setIndex(!indexVisible);
});
queryEl.addEventListener('input',onInput);
clearBtn.addEventListener('click',function(){queryEl.value='';clearBtn.hidden=true;phEl.hidden=false;run();queryEl.focus();});
queryEl.addEventListener('keydown',function(e){
  if(e.key==='Escape'){clearBtn.click();}
  else if(e.key==='ArrowDown'){e.preventDefault();moveSel(1);}
  else if(e.key==='ArrowUp'){e.preventDefault();moveSel(-1);}
  else if(e.key==='Enter'){
    clearTimeout(debounce);
    var items=out.querySelectorAll('.r');
    if(!items.length){run();items=out.querySelectorAll('.r');}
    var t=items[sel>=0?sel:0];if(t)window.open(t.href,'_blank','noopener');
  }
});
// "/" jumps back to the search field from anywhere
addEventListener('keydown',function(e){if(e.key==='/'&&document.activeElement!==queryEl){e.preventDefault();queryEl.focus();queryEl.select();}});

function start(){
  TOTAL=ENTRIES.length.toLocaleString('en');
  if(queryEl.value)onInput();else showDisc();
  randomPlaceholder();
  setInterval(function(){if(currentMode==='fuzzy'&&!queryEl.value&&!document.hidden)cyclePlaceholder();},6000);
}

out.innerHTML='<div class="state"><p>Loading lemmata…</p></div>';
queryEl.focus();
fetch(DATA_URL,{cache:'no-cache'})
  .then(function(r){if(!r.ok)throw new Error('HTTP '+r.status+' for '+DATA_URL);return r.text();})
  .then(function(t){ENTRIES=toEntries(parseCSV(t));start();})
  .catch(function(err){
    var local=location.protocol==='file:';
    out.innerHTML='<div class="state"><p class="lead">The lemma list could not be loaded.</p><p>'
      +(local?'Browsers block reading data files from a page opened directly from disk. Serve the folder over HTTP instead (e.g. run <code>python3 -m http.server</code> inside it and open <code>http://localhost:8000</code>).'
             :escHtml(String(err.message||err)))+'</p></div>';
    countEl.textContent='';
  });
})();
