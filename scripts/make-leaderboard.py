"""Builds site/index.html (the private web leaderboard) from wi-eats/site/index.html, with Oregon's boards, sources and palette.
Ported from mi-eats/scripts/make-leaderboard.py (itself from tx-eats and co-eats).
Every replacement is asserted, so a change in the Wisconsin page fails loudly instead of leaving Wisconsin text behind.
Usage: .venv/bin/python scripts/make-leaderboard.py"""
import os, re, sys
ROOT = os.path.join(os.path.dirname(__file__), "..")
src = open(os.path.join(ROOT, "..", "wi-eats", "site", "index.html")).read()
s = src
def R(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f"expected {n} of {a[:90]!r}, found {c}")
    s = s.replace(a, b)

# ---------------- head, palette, type
R('<title>Wisconsin Restaurant Leaderboard</title>', '<meta charset="utf-8">\n<title>Oregon Restaurant Leaderboard</title>')
R('<meta name="description" content="Every restaurant in Wisconsin, ranked on ratings, popularity, fish fry, supper clubs, custard, value and estimated sales.">',
  '<meta name="description" content="Every restaurant in Oregon, ranked on ratings, popularity, honors, value and sales, checked against OLCC\'s statewide liquor licenses.">')
R('family=Saira+Extra+Condensed:wght@600;700;800;900&family=Source+Sans+3:ital,wght@0,400;0,500;0,600;0,700;1,400', 'family=Oswald:wght@500;600;700&family=Public+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400')
R('''  /* Packers: green #203731, gold #FFB612, white. Light-only by design; gold is a fill with green text on it, never text on white. */
  color-scheme:light;
  --bg:#FFFFFF; --surface:#FFFFFF; --surface-2:#F1F5F2; --surface-3:#E1EAE4;
  --ink:#14241D; --ink-2:#2E4238; --muted:#53665B; --rule:#DAE3DD; --rule-2:#B6C6BC;
  --green:#203731; --green-2:#2D5242; --gold:#FFB612; --gold-soft:#FFE7A8; --on-gold:#203731;
  --map-fill:#EEF3EF; --map-line:#C2D1C7; --dot-edge:rgba(20,36,29,.35);
  --seq1:#CFE2D5; --seq2:#9CC4A9; --seq3:#5F9A74; --seq4:#326B4B; --seq5:#203731;
  --scrim:rgba(20,36,29,.38);
  --shadow:0 1px 2px rgba(20,36,29,.06),0 8px 28px rgba(20,36,29,.10);
  --display:"Saira Extra Condensed","Arial Narrow","Roboto Condensed",sans-serif;
  --body:"Source Sans 3",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;''',
'''  /* Layout: sticky leaderboard tabs over a filter rail + ranked list; one Oregon element, a Mt. Hood ridgeline with firs under the
     header. Provisional palette until Nick picks (2026-10-24): the official state colors, navy #14305C (ORS 186.010) for headings and
     ink accents, Crater Lake blue #1F5A96 for links, and gold #F2B705 only as a fill under navy text (7.2:1; gold text on white fails).
     Light-only by design, like the other leaderboards: every color is set explicitly below. */
  color-scheme:light;
  --bg:#FFFFFF; --surface:#FFFFFF; --surface-2:#F3F5F9; --surface-3:#E2E8F1;
  --ink:#0E1B2E; --ink-2:#26364F; --muted:#556275; --rule:#DCE2EB; --rule-2:#B5C1D2;
  --green:#14305C; --green-2:#1F5A96; --gold:#F2B705; --gold-soft:#FCEFC2; --on-gold:#14305C; --red:#1F5A96;
  --map-fill:#F1F4F8; --map-line:#C4CEDB; --dot-edge:rgba(14,27,46,.35);
  --seq1:#D5E0EE; --seq2:#9DB5D6; --seq3:#5A82B8; --seq4:#1F5A96; --seq5:#14305C;
  --scrim:rgba(14,27,46,.38);
  --shadow:0 1px 2px rgba(14,27,46,.06),0 8px 28px rgba(14,27,46,.10);
  --display:"Oswald","Arial Narrow","Roboto Condensed",sans-serif;
  --body:"Public Sans",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;''')
R('body{margin:0;background:var(--bg);', 'html,body{background:var(--bg)}\nbody{margin:0;background:var(--bg);')
R('.hmid{padding:22px 16px 18px;border-bottom:4px solid var(--gold)}', '.hmid{padding:22px 16px 10px}\n.ridge{display:block;width:100%;height:44px;margin-top:-1px}\n.ridge .r1{fill:var(--green)} .ridge .r2{fill:#FFFFFF} .ridge .r3{fill:#2E5E4E}')
R('.tab.wi{border-color:#D9A21A;background:#FFF9EA}', '.tab.wi{border-color:#B98C00;background:#FFF8E1}')
R('.chips.wi .chip[aria-pressed="false"]{background:#FFF9EA;border-color:#D9A21A}', '.chips.wi .chip[aria-pressed="false"]{background:#FFF8E1;border-color:#B98C00}')
R('.badge.sc{background:var(--gold-soft);color:var(--on-gold)}', '.badge.sc{background:var(--gold-soft);color:#14305C}\n.badge.mi{background:var(--red);color:#fff}\n.res{display:inline-block;font:700 11.5px/1.5 var(--body);letter-spacing:.04em;text-transform:uppercase;padding:1px 7px;border-radius:5px;white-space:nowrap}\n.res-0{background:#DDEFE3;color:#0E5A2B} .res-1{background:#FFE9C2;color:#6B3A00} .res-2{background:#F9D5DB;color:#7A0019}\n.res-3{background:#DDEFE3;color:#0E5A2B} .res-4{background:#F9D5DB;color:#7A0019} .res-5{background:#DDEFE3;color:#0E5A2B} .res-6{background:#E3ECF8;color:#1C3F86} .res-7{background:#FFE9C2;color:#6B3A00} .res-8{background:#F9D5DB;color:#7A0019}')
R('.fhint{font-size:12.5px;color:#8A4B00;margin:0}', '.fhint{font-size:12.5px;color:#8A4B00;margin:0}')
R('#map{display:block;width:100%;max-width:min(760px,max(240px,calc((100dvh - var(--stickyH) - 120px) * 0.95)));margin:0 auto;aspect-ratio:0.95;touch-action:manipulation}',
  '#map{display:block;width:100%;max-width:min(860px,max(240px,calc((100dvh - var(--stickyH) - 120px) * 1.3)));margin:0 auto;aspect-ratio:1.3;touch-action:manipulation}')
R('@media (max-height:500px){#map{max-width:max(160px,calc((100dvh - var(--stickyH) - 70px) * 0.95))}}', '@media (max-height:500px){#map{max-width:max(160px,calc((100dvh - var(--stickyH) - 70px) * 1.3))}}')

# ---------------- header and filters
# a Mt. Hood ridgeline with firs (provisional header element, 2026-10-24): a navy band, Mt. Hood's snow-capped cone in the middle and a
# row of firs along the bottom edge (flat shapes, no map or team marks)
FIRS = "".join(f'<path class="r3" d="M{x} 44 L{x + 9} 27 L{x + 18} 44Z"/>' for x in range(4, 1200, 30) if not 520 < x < 662)
RIDGE = ('<svg class="ridge" viewBox="0 0 1200 44" preserveAspectRatio="none" aria-hidden="true">'
         '<rect class="r1" x="0" y="0" width="1200" height="10"/>'
         '<path class="r1" d="M500 44 L586 6 Q600 1 614 6 L700 44Z"/>'
         '<path class="r2" d="M586 6 Q600 1 614 6 L626 12 L614 10 L604 15 L596 11 L586 14 L574 12Z"/>' + FIRS + '</svg>')
R('''    <p class="kicker" id="kicker">Wisconsin · map listings as of Sep 2026</p>
    <h1 id="h1">Every Wisconsin restaurant, <span class="count">ranked</span></h1>
    <p class="lede" id="lede">Supper clubs, taverns, custard stands, Friday fish fries and the places in between, from Superior to Kenosha. Each one is ranked on ratings, popularity, value and estimated sales, with Wisconsin's own boards for fish fry, supper clubs, custard and cheese curds. Flip any leaderboard to see the bottom.</p>
  </div></div>''',
'''    <p class="kicker" id="kicker">Oregon · map listings as of Oct 2026</p>
    <h1 id="h1">Every Oregon restaurant, <span class="count">ranked</span></h1>
    <p class="lede" id="lede">Food carts, brewpubs, coast chowder houses, wine-country dining rooms and the places in between, from Astoria to Ontario. Each one is ranked on ratings, popularity, value and sales and checked against the state's liquor license list (OLCC). Oregon publishes no restaurant inspection results in bulk, so there's no inspection board. Flip any leaderboard to see the bottom.</p>
  </div></div>''' + RIDGE)
R('<select id="city"><option value="">All of Wisconsin</option></select>', '<select id="city"><option value="">All of Oregon</option></select>')
R('<span class="flabel" id="l-tags">Wisconsin classics</span>', '<span class="flabel" id="l-tags">Oregon guides</span>')
R('<label class="toggle"><input type="checkbox" id="confirmed"> Only confirmed places (on a Milwaukee or Dane County license list, or in two sources)</label>',
  '<label class="toggle"><input type="checkbox" id="confirmed"> Only confirmed places (holding an OLCC liquor license, or in two sources)</label>')
R('<p class="wnote">Each ingredient is a 0–100 percentile across Wisconsin.', '<p class="wnote">Each ingredient is a 0–100 percentile across Oregon.')
R('WI Score recipe: <span id="wname">', 'OR Score recipe: <span id="wname">')
R('placeholder="Search name, town, street, zip, “fish fry”…"', 'placeholder="Search name, town, street, zip, “chowder”…"')

# ---------------- constants
R('const TAGS = [["supper","Supper clubs",1],["fishfry","Fish fry",2],["custard","Frozen custard",8],["curds","Cheese curds",4]];',
  'let HAVE_TAGS = 0;\nconst TAGS_ALL = [["cart","Food carts",1],["brewpub","Brewpubs (OLCC)",2],["seafood","Coast seafood",4],["marion","Marionberry pie",8],["wine","Wine-country dining",16],["donut","Doughnut shops",32],["taqueria","Taquerías",64],["oldest","Oldest places",128]];\nlet TAGS = [];')
R('const JUR = ["", "City of Milwaukee", "Public Health Madison & Dane County"];', 'const JUR = ["", "OLCC liquor license"];')
R('research:"our verified list, placed with its Google listing"', 'research:"our hand-checked list, placed on its street address"')
R('try { S = sanitize(JSON.parse(localStorage.getItem("wi-eats") || "null")); }', 'try { S = sanitize(JSON.parse(localStorage.getItem("or-eats") || "null")); }')
R('localStorage.setItem("wi-eats", JSON.stringify(rest));', 'localStorage.setItem("or-eats", JSON.stringify(rest));')
R('let D = [], META = {}, SHAPES = null, WI_BOUNDS = null,', 'let D = [], META = {}, SHAPES = null, WI_BOUNDS = null, RESN = [], INSJ = [],')

# ---------------- boards
a = s.index('const sigShow = '); b = s.index('const board = () =>')
BOARDS = r'''const ratedShow = r => [stars(r.rating), revs(r)+(r.reviews === 1 ? " review" : " reviews")+" ('21)"];
const resPill = r => `<span class="res res-${r.in_r === 0 ? 0 : 1}">${esc(INSJ[r.in_j])} · ${esc(RESN[r.in_r])}</span>`;
const MI_TXT = ["", "MICHELIN Recommended", "Bib Gourmand", "1 MICHELIN Star", "2 MICHELIN Stars", "3 MICHELIN Stars"];
const B = [
  {id:"overall", tab:"OR Score", top:"Top OR Score", bottom:"Lowest OR Score", metric:"OR Score", val:r=>r.score,
   sub:()=>"A blend of rating, popularity, value and estimated profit, weighted by the OR Score recipe in the filters. Places missing some data are pulled toward 40, a little below the middle. A James Beard honor sets a floor: 85 for an America's Classic or a win, 80 for a finalist, 72 for a semifinalist. (Oregon has no MICHELIN Guide.)",
   show:r=>[Math.round(r.score), "OR Score"]},
  {id:"rating", tab:"Rating", top:"Highest rated", bottom:"Lowest rated", metric:"rating", val:r=>r.bayes, need:(r,d)=>r.reviews >= (d==="top"?15:40),
   sub:"Google star rating as of the Sep 2021 snapshot, adjusted for review count so a 5.0 from three friends doesn't beat a 4.8 from 3,000 strangers.",
   show:ratedShow, dup:"rating"},
  {id:"popular", tab:"Popularity", top:"Most popular", bottom:"Least popular", metric:"reviews", val:r=>r.reviews, need:r=>r.reviews!=null,
   sub:"Total Google reviews as of Sep 2021: the best public stand-in for how many people walk through the door. Places opened since aren't in the snapshot, and the snapshot caps counts at 9,998 (shown as 9,998+).",
   show:r=>[revs(r), (r.reviews === 1 ? "review" : "reviews")+" ('21) · "+stars(r.rating)], dup:"rating"},
  {id:"gems", tab:"Hidden gems", top:"Hidden gems", bottom:"Popular but panned", metric:"rating", val:r=>r.gem, need:(r,d)=> d==="top" ? (r.reviews>=20 && r.reviews<=250 && r.chain_n<5) : r.reviews>=600,
   sub:"Top: independents with 20–250 reviews and great ratings. Bottom: places with 600+ reviews and the lowest ratings. Both from the Sep 2021 snapshot.",
   show:ratedShow, dup:"rating"},
  {id:"brewpub", wi:true, tagbit:2, tab:"Brewpubs", top:"Brewpubs, highest rated", bottom:"Brewpubs, lowest rated", metric:"rating", val:r=>r.bayes, need:(r,d)=>(r.tags & 2) && r.reviews >= (d==="top"?10:30),
   sub:"Places holding an OLCC Brewery Public House license (a brewery that sells its beer and food on site), one place per license, matched by the license's trade name. Ranked by Google rating (Sep 2021), adjusted for review count; brewpubs opened since aren't rated.",
   show:ratedShow, dup:"rating"},
  {id:"cart", wi:true, tagbit:1, tab:"Food carts", top:"Food carts, highest rated", bottom:"Food carts, lowest rated", metric:"rating", val:r=>r.bayes, need:(r,d)=>(r.tags & 1) && r.reviews >= (d==="top"?10:30),
   sub:"Food carts and the pods they park in, each confirmed at its pod with a 2025–26 source (carts move and close often). Hand-checked: each place confirmed open with a 2025–26 source. Ranked by Google rating (Sep 2021), adjusted for review count.",
   show:ratedShow, dup:"rating"},
  {id:"seafood", wi:true, tagbit:4, tab:"Coast seafood", top:"Coast seafood, highest rated", bottom:"Coast seafood, lowest rated", metric:"rating", val:r=>r.bayes, need:(r,d)=>(r.tags & 4) && r.reviews >= (d==="top"?10:30),
   sub:"Dungeness crab, clam chowder and oysters on the Oregon coast and its bays. Hand-checked: each place confirmed open with a 2025–26 source. Ranked by Google rating (Sep 2021), adjusted for review count.",
   show:ratedShow, dup:"rating"},
  {id:"marion", wi:true, tagbit:8, tab:"Marionberry pie", top:"Marionberry pie, highest rated", bottom:"Marionberry pie, lowest rated", metric:"rating", val:r=>r.bayes, need:(r,d)=>(r.tags & 8) && r.reviews >= (d==="top"?10:30),
   sub:"Marionberry pie, Oregon's official state pie (HCR 19, 2017). Hand-checked: each place confirmed open with a 2025–26 source. Ranked by Google rating (Sep 2021), adjusted for review count.",
   show:ratedShow, dup:"rating"},
  {id:"wine", wi:true, tagbit:16, tab:"Wine-country dining", top:"Wine-country dining, highest rated", bottom:"Wine-country dining, lowest rated", metric:"rating", val:r=>r.bayes, need:(r,d)=>(r.tags & 16) && r.reviews >= (d==="top"?10:30),
   sub:"Restaurants in the Willamette Valley wine country. Hand-checked: each place confirmed open with a 2025–26 source. Ranked by Google rating (Sep 2021), adjusted for review count.",
   show:ratedShow, dup:"rating"},
  {id:"donut", wi:true, tagbit:32, tab:"Doughnut shops", top:"Doughnut shops, highest rated", bottom:"Doughnut shops, lowest rated", metric:"rating", val:r=>r.bayes, need:(r,d)=>(r.tags & 32) && r.reviews >= (d==="top"?10:30),
   sub:"Doughnut shops. Hand-checked: each place confirmed open with a 2025–26 source. Ranked by Google rating (Sep 2021), adjusted for review count.",
   show:ratedShow, dup:"rating"},
  {id:"taqueria", wi:true, tagbit:64, tab:"Taquerías", top:"Taquerías, highest rated", bottom:"Taquerías, lowest rated", metric:"rating", val:r=>r.bayes, need:(r,d)=>(r.tags & 64) && r.reviews >= (d==="top"?10:30),
   sub:"Taquerías in Woodburn, Salem, Hillsboro, Hood River and beyond. Hand-checked: each place confirmed open with a 2025–26 source. Ranked by Google rating (Sep 2021), adjusted for review count.",
   show:ratedShow, dup:"rating"},
  {id:"iconic", tab:"Iconic", top:"Most iconic", bottom:"Least iconic", metric:"iconic points", val:r=>r.s_icon, need:r=>r.s_icon!=null,
   sub:"Only places with an honor or a long, verified history: James Beard awards and nominations 2025–26, America's Classics, and places we verified open at the same address since 1960 or earlier. Points for honors, years open and how many people know it.",
   show:r=>[Math.round(r.s_icon), "iconic pts" + (r.founded ? " · since " + r.founded : "")]},
  {id:"value", tab:"Value", top:"Best bang for buck", bottom:"Worst value", metric:"value score", val:r=>r.value_raw, need:r=>r.rating!=null,
   sub:"Rating (2021) relative to price level: a 4.7 at $ beats a 4.7 at $$$.",
   show:r=>[stars(r.rating)+" "+dollars(r.price)+(r.price_est?ESTTAG:""), "value "+Math.round(r.i_value)+" · rating '21"], dup:"rating"},
  {id:"price", tab:"Price", top:"Priciest", bottom:"Cheapest", metric:"price", val:r=>r.spend,
   sub:"Google price level (filled in from the chain or cuisine when missing, and marked est.) with typical spend per person. Within a price level, ties are ordered by OR Score.",
   show:r=>[dollars(r.price)+(r.price_est?ESTTAG:""), "~$"+r.spend+"/person "+ESTTAG]},
  {id:"property", tab:"Property value", top:"Most valuable property", bottom:"Least valuable property", metric:"property value", val:r=>r.prop, need:r=>r.prop!=null,
   sub:d=>"Metro Portland only (Multnomah, Washington and Clackamas counties): the county assessor's market value, land plus buildings, of the tax lot under the place, from Metro's Regional Land Information System" + (META.rlis?.fetched ? ` (read ${esc(META.rlis.fetched)})` : "") + ". For a mall, a tower or the airport that's the whole property, so every place inside shows the same figure. Places whose point falls on a street have no lot and are left out. Regional Land Information System data are a product of Metro.",
   show:r=>[money(r.prop), "property value" + (r.built ? " · built " + r.built : "")]},
  {id:"sales", tab:"Sales", top:"Highest sales", bottom:"Lowest sales", metric:"sales", val:r=>r.rev, need:(r,d)=>r.rev!=null && (d==="top" || r.rev_src!=="model-low"), est:true,
   sub:d=>`Estimated yearly sales. Locations of chains with a published average (${META.model?.n_chains ?? "80+"} brands) use that average scaled by how busy the location is; independents use a model.` + (d==="bottom" ? " This end leaves out places with no review data (their figures are rough placeholders). The model never goes below $100K a year, so the very bottom is a tie, ordered by OR Score." : ""),
   show:r=>[money(r.rev), "sales/yr · " + src(r)], dup:"sales"},
  {id:"profit", tab:"Profit", top:"Most profitable", bottom:"Least profitable", metric:"profit", val:r=>r.profit, need:(r,d)=>r.profit!=null && (d==="top" || r.rev_src!=="model-low"), est:true,
   sub:d=>"Estimated yearly pre-tax profit: estimated sales × a typical margin for the segment, nudged by how well-loved the place is." + (d==="bottom" ? " This end leaves out places with no review data (their figures are rough placeholders). The sales model never goes below $100K a year, so the very bottom is mostly places at that floor, ordered by margin and then OR Score." : ""),
   show:r=>[money(r.profit), "profit/yr "+ESTTAG]},
];'''
s = s[:a] + BOARDS + "\n" + s[b:]

# ---------------- honors lift the MI Score: a James Beard place that opened after the 2021 snapshot has no rating data, so the blend
# alone would pull it to 40 (Nick on Texas, 2026-10-20: "the score would be higher"). Oregon has no MICHELIN Guide, so mi is always 0.
R("""    r.score = have ? (sum/have)*(have/weightTotal) + 40*(1 - have/weightTotal) : 40;
  }""", """    r.score = have ? (sum/have)*(have/weightTotal) + 40*(1 - have/weightTotal) : 40;
    // an honor sets a floor: 1+ MICHELIN Star 92, Bib Gourmand or America's Classic or a James Beard win 85, a finalist 80,
    // MICHELIN Recommended 78, a semifinalist 72
    const h = r.hon || 0, mi = r.mi || 0;
    const floor = Math.max(mi >= 3 ? 92 : mi === 2 ? 85 : mi === 1 ? 78 : 0, (h & 3) ? 85 : (h & 4) ? 80 : (h & 8) ? 72 : 0);
    if (floor > r.score) r.score = floor;
  }""")
# ---------------- rows, badges, stats
R('''  if (r.hon & 1) h += `<span class="badge jbf">America's Classic</span>`;''',
  '''  if (r.mi) h += `<span class="badge mi">${MI_TXT[r.mi]}</span>`;
  if (r.hon & 1) h += `<span class="badge jbf">America's Classic</span>`;''')
R('''  if ((r.hon & 16) && !(r.hon & 7)) h += `<span class="badge icon">Icon</span>`;
  if ((r.tags & 1) && !/supper ?club/i.test(r.name)) h += `<span class="badge sc">Supper club</span>`;''',
  '''  if ((r.hon & 16) && r.founded) h += `<span class="badge icon">Since ${esc(r.founded)}</span>`;
  if (r.tags & 1) h += `<span class="badge sc">Food cart</span>`;
  if (r.tags & 2) h += `<span class="badge sc">Brewpub</span>`;
  if (r.tags & 4) h += `<span class="badge sc">Coast seafood</span>`;
  if (r.tags & 8) h += `<span class="badge sc">Marionberry pie</span>`;
  if (r.tags & 16) h += `<span class="badge sc">Wine country</span>`;
  if (r.tags & 32) h += `<span class="badge sc">Doughnuts</span>`;
  if (r.tags & 64) h += `<span class="badge sc">Taquería</span>`;''')
R('''  if (r.ff_n >= 3 && b.id !== "fishfry") bits.push(`<span>${r.ff_n} <i>fish fry mentions</i></span>`);
  if (r.grade) bits.push(`<span class="${dup("grade")}" title="Our grade from Dane County inspection results, not an official grade"><span class="grade sm g-${r.grade}">${r.grade}</span> <i>our inspection grade</i></span>`);''',
  '''  if (r.liq) bits.push(`<span><i>${esc(META.liqt[r.liq])}</i></span>`);''')
R('''  if (S.board !== "overall" && r.score != null) bits.push(`<span>${Math.round(r.score)} <i>WI Score</i></span>`);''',
  '''  if (S.board !== "overall" && r.score != null) bits.push(`<span>${Math.round(r.score)} <i>OR Score</i></span>`);''')
R('''const TAG_PH = [["friday fish fry","fishfry"],["fish fries","fishfry"],["fish fry","fishfry"],["fishfry","fishfry"],["supper clubs","supper"],["supper club","supper"],
  ["supperclub","supper"],["frozen custard","custard"],["custard","custard"],["cheese curds","curds"],["cheese curd","curds"],["curds","curds"]].map(([p, t]) => [norm(p), t]);''',
  '''const TAG_PH_ALL = [["food carts","cart"],["food cart","cart"],["brewpubs","brewpub"],["brewpub","brewpub"],["marionberry pie","marion"],
  ["marionberry","marion"],["doughnuts","donut"],["donuts","donut"],["taquerias","taqueria"],["taqueria","taqueria"],["wine country","wine"]]
  .map(([p, t]) => [norm(p), t]);
let TAG_PH = [];''')
R('''  // "fish fry", "supper club", "custard", "cheese curds" mean the Wisconsin tags, not words in a name''', '''  // "food cart", "brewpub", "marionberry" mean the Oregon guides, not words in a name''')
R('''  // "fond du lac fish fry" means the town; "green bay rd" or "madison st" is a street, not the town''', '''  // "woodburn taqueria" means the town; "oregon st" or "hood river hwy" is a street, not the town''')
R('''  // a town named in the search ("fond du lac fish fry") narrows to it; a place NAMED that way still counts''', '''  // a town named in the search ("woodburn taqueria") narrows to it; a place NAMED that way still counts''')
R('''    return `No places match “${esc(S.q.trim())}” in Wisconsin.''', '''    return `No places match “${esc(S.q.trim())}” in Oregon.''')
R('''  const setPh = () => { $("#q").placeholder = innerWidth < 400 ? "Search name, town, street…" : "Search name, town, street, zip, “fish fry”…"; };''', '''  const setPh = () => { $("#q").placeholder = innerWidth < 400 ? "Search name, town, street…" : "Search name, town, street, zip, “chowder”…"; };''')
R('''  if (S.board === "overall" && !weightTotal) return `The WI Score recipe is empty.''', '''  if (S.board === "overall" && !weightTotal) return `The OR Score recipe is empty.''')
R('''  if (pool.length && board().id === "clean") return `${plural(pool.length, "place matches", "places match")} ${what}, but inspection results are only published for Dane County (Madison and its suburbs). ${f.length ? undo + " to see them." : ""}`;''',
  '''  if (pool.length && board().id === "clean") return `${plural(pool.length, "place matches", "places match")} ${what}, but Oregon publishes no inspection results in bulk. ${f.length ? undo + " to see them." : ""}`;''')
R('''"All of Wisconsin"}</option>`''', '''"All of Oregon"}</option>`''')
R('''$("#cityhint").textContent = `No Wisconsin town matches''', '''$("#cityhint").textContent = `No Oregon town matches''')
R('''    else if (cityFromBox && S.city) { S.city = ""; cityFromBox = false; rerender(); }   // "Wausauk" is no longer Wausau''', '''    else if (cityFromBox && S.city) { S.city = ""; cityFromBox = false; rerender(); }   // "Bendd" is no longer Bend''')
R('''    const hit = CITY_N.get(v) || (CITIES.find(([c]) => (" " + norm(c)).includes(" " + v)) || [])[0];   // CITIES is biggest first: "bay" -> Green Bay''',
  '''    const hit = CITY_N.get(v) || (CITIES.find(([c]) => (" " + norm(c)).includes(" " + v)) || [])[0];   // CITIES is biggest first: "falls" -> Klamath Falls''')
R('''const cols = [["name","City or town"],["n","Places","r"],["score","Avg WI Score","r"]''', '''const cols = [["name","City or town"],["n","Places","r"],["score","Avg OR Score","r"]''')

# ---------------- map
R('shapesPending = fetchJSON("wi_shapes.json").then(j => {', 'shapesPending = fetchJSON("or_shapes.json").then(j => {')
R("WI_BOUNDS = a[0] < a[1] ? a : [-92.9, -86.8, 42.49, 47.08];", "WI_BOUNDS = a[0] < a[1] ? a : [-124.57, -116.46, 41.99, 46.29];")
R('map listings as of Sep 2026 · ratings as of Sep 2021`;', 'map listings as of Oct 2026 · ratings as of Sep 2021`;')
R("const w = c.clientWidth || 600, h = Math.round(w / 0.95);", "const w = c.clientWidth || 600, h = Math.round(w / 1.3);")
R("  ctx.save(); land(); ctx.clip(\"evenodd\");   // county lines stop at the shore", "  ctx.save(); land(); ctx.clip(\"evenodd\");   // county lines stop at the shore")
R('''  $("#live").textContent = pool.length === 1 ? `Only one place matches your filters: ${r.name}.` : `Random pick: ${r.name}, ${r.city || "Wisconsin"}.`;''',
  '''  $("#live").textContent = pool.length === 1 ? `Only one place matches your filters: ${r.name}.` : `Random pick: ${r.name}, ${r.city || "Oregon"}.`;''')

# ---------------- drawer
a = s.index('function calibNote(r) {'); b = s.index('function sigCard(n, rt, what)')
s = s[:a] + r'''function calibNote(r) {
  const c = (META.calibration || {}).areas || {}, g = k => [c["Oregon (statewide)"]?.groups?.[k]].filter(Boolean);
  const range = k => { const v = g(k).map(x => x.official); if (!v.length) return null; const lo = Math.min(...v), hi = Math.max(...v); return lo === hi ? pctTxt(lo) : `${pctTxt(lo)}–${pctTxt(hi)}`; };
  const feed = r.src === "AllThePlaces" || r.src === "DAC", checked = r.hc ? " It's also on our hand-checked list." : "";
  if (r.src === "research") return "This place isn't in the map listings as a place to eat. It's on our hand-checked list and placed on its street address.";
  if (r.tier === 2) return (r.src === "official" ? `This place comes straight from the ${esc(JUR[r.jur])} list. The map listings we use didn't have it, so it's placed on its licensed street address.` : `Matched to an active ${esc(JUR[r.jur])}, so it's confirmed as a licensed business.`) + checked;
  const via = feed ? (r.tier === 1 ? "brand feed + Google 2021" : "brand feed only") : r.src === "meta" ? (r.tier === 1 ? "Meta + open in Google 2021" : "Meta only") : null;
  const rate = via ? range(via) : null, kind = feed ? "chain store-list listings" : "listings";
  if (!via) return "Kept because it's on our hand-checked list, even though its only map listing comes from a source that's usually unreliable.";
  if (r.tier === 1) return `Found in two independent sources: a map listing and Google's 2021 data, but not matched to a liquor license. Oregon publishes no food-license list, so the check is OLCC's liquor licenses: ${kind} like this matched one ${rate || "often"} of the time, and many real restaurants (cafés, taquerías, carts) serve no alcohol.` + checked;
  return `Found in one map source only, and not matched to a liquor license. Oregon publishes no food-license list; checked against OLCC's liquor licenses, single-source ${kind} like this matched one ${rate || "less often"} of the time, so this one may be closed or misfiled.` + checked;
}
''' + s[b:]
R('''  const gq = encodeURIComponent(`${r.name} ${r.addr || ""} ${r.city || ""} WI`);''', '''  const gq = encodeURIComponent(`${r.name} ${r.addr || ""} ${r.city || ""} OR`);''')
R('''  const heroLbl = r.score == null ? (weightTotal ? "No WI Score: not enough data" : "WI Score recipe is empty")
    : ri >= 0 ? `WI Score · #${fmtN(ri+1)} of ${fmtN(L.length)} with your filters (ignoring search)` : "WI Score · outside your current filters";''',
  '''  const heroLbl = r.score == null ? (weightTotal ? "No OR Score: not enough data" : "OR Score recipe is empty")
    : ri >= 0 ? `OR Score · #${fmtN(ri+1)} of ${fmtN(L.length)} with your filters (ignoring search)` : "OR Score · outside your current filters";''')
R('''  const cats = `<div class="dsec"><h3>Category scores (percentile vs. all Wisconsin places)</h3>''', '''  const cats = `<div class="dsec"><h3>Category scores (percentile vs. all Oregon places)</h3>''')
a = s.index('  const sig = [sigCard('); b = s.index('  const moneyNote = {')
s = s[:a] + s[b:]
R('''This location isn't in the 2021 review snapshot, so this uses 85% of the chain's published U.S. average sales per location." : "Based on the chain's published U.S. average sales per location, scaled up or down by how busy this location was (2021 reviews) compared with the chain's other Wisconsin locations.",''',
  '''This location isn't in the 2021 review snapshot, so this uses 85% of the chain's published U.S. average sales per location." : "Based on the chain's published U.S. average sales per location, scaled up or down by how busy this location was (2021 reviews) compared with the chain's other Oregon locations.",''')
R('''scaled by 2021 review volume relative to similar Wisconsin places''', '''scaled by 2021 review volume relative to similar Oregon places''')
a = s.index('  const honorsList = ['); b = s.index('  $("#drawer").innerHTML = `${dhead(')
s = s[:a] + r'''  const honorsList = [...(x.jbf ? x.jbf.split(/;\s(?![^()]*\))/).map(v => "James Beard: " + v) : [])];
  const tagsTxt = TAGS.filter(([, , bit]) => r.tags & bit).map(([, l]) => l);
  const facts = (x.note || x.dishes || x.founded_note || x.seasonal) ? `<div class="dsec"><h3>Hand-checked facts</h3>${x.note ? `<p style="margin:0 0 8px;color:var(--ink-2);font-size:14px">${esc(x.note)}</p>` : ""}
      ${kv([x.dishes ? ["On the menu", esc(x.dishes.split("; ").join(", "))] : null, x.founded ? ["Open here since", esc(x.founded)] : null, x.seasonal ? ["Season", esc(x.seasonal)] : null])}
      ${x.founded_note ? `<p class="note">${esc(x.founded_note)}</p>` : ""}${x.web ? `<p class="note">Source: <a href="${esc(x.web)}" target="_blank" rel="noopener">${esc(x.web.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, ""))}</a>.</p>` : ""}</div>` : "";
  const lic = (x.lic || []).map(l => [esc(l.src), esc(l.type || "") + (l.id ? " · no. " + esc(l.id) : "") + (l.exp ? " · expires " + esc(l.exp) : "")]);
  const insp = `<div class="dsec"><h3>Health inspections</h3><p class="note">Oregon's county health departments inspect and score every restaurant (a sanitation score out of 100, with a posted "Complied" or "Failed to Comply" notice at the door), but the results are only on a search-only portal (inspections.myhealthdepartment.com/oregon) that doesn't allow automated access, so none are shown here.</p></div>`;
  const alcSec = "";
''' + s[b:]
R('''  $("#drawer").innerHTML = `${dhead(esc(r.city || "Wisconsin"), random)}''', '''  $("#drawer").innerHTML = `${dhead(esc(r.city || "Oregon"), random)}''')
R('''    <div class="addr">${r.addr ? esc(r.addr) + ", " : ""}${esc(r.city || "Wisconsin")}''', '''    <div class="addr">${r.addr ? esc(r.addr) + ", " : ""}${esc(r.city || "Oregon")}''')
R('''    ${sig ? `<div class="dsec"><h3>Wisconsin classics · from Google reviews through Sep 2021</h3><div class="wisig">${sig}</div><p class="note">Average star rating of just the reviews that mention it. Reviews rate the whole visit, so read these as a lean, not a verdict.</p></div>` : ""}
    ${(honorsList.length || x.icon || x.founded) ? `<div class="dsec"><h3>Honors &amp; history</h3>${x.icon?`<p style="margin:0 0 8px;color:var(--ink-2);font-size:14px">${esc(x.icon)}</p>`:""}${honorsList.length?`<ul class="lines">${honorsList.map(v=>`<li>${esc(v)}</li>`).join("")}</ul>`:""}${x.founded ? `<p class="note">Open since ${esc(x.founded)} (verified).</p>` : ""}</div>`
      : (r.hon && !DETAIL ? `<div class="dsec"><h3>Honors &amp; history</h3><p class="note">${detailFailed ? "Couldn't load the honors. Check your connection and reopen this place." : "Loading…"}</p></div>` : "")}
    ${insp}''',
  '''    ${honorsList.length ? `<div class="dsec"><h3>Honors</h3><ul class="lines">${honorsList.map(v=>`<li>${esc(v)}</li>`).join("")}</ul><p class="note">MICHELIN and the MICHELIN Guide are trademarks of Michelin. James Beard Foundation awards are the Foundation's. Honors are facts, not ratings.</p></div>`
      : ((r.hon & 15) && !DETAIL ? `<div class="dsec"><h3>Honors</h3><p class="note">${detailFailed ? "Couldn't load the honors. Check your connection and reopen this place." : "Loading…"}</p></div>` : "")}
    ${facts}
    ${alcSec}
    ${insp}''')
R('''      x.lic ? ["License number", esc(x.lic.replace(/^(MKE|PHMDC)-/, ""))] : null,
      tagsTxt.length ? ["Wisconsin tags", esc(tagsTxt.join(", "))] : null,
      ["Listed as a bar or tavern", r.bar ? "Yes" : "No"], ["Locations in Wisconsin", r.chain_n >= 2 ? fmtN(r.chain_n) : "This one only"],''',
  '''      ...lic, r.liq ? ["Serves alcohol", "Yes · " + esc(META.liqt[r.liq])] : ["Serves alcohol", "— (no active on-premises OLCC license matched)"],
      tagsTxt.length ? ["Oregon guides", esc(tagsTxt.join(", "))] : null,
      r.county ? ["County", esc(r.county)] : null,
      r.prop != null ? ["Property value", money(r.prop) + (r.built ? " · built " + esc(r.built) : "") + " · Metro RLIS (county assessor)"] : null,
      ["Listed as a bar or tavern", r.bar ? "Yes" : "No"], ["Locations in Oregon", r.chain_n >= 2 ? fmtN(r.chain_n) : "This one only"],''')
R('''  detailPending = fetchJSON("wi_detail.json").then(j => {''', '''  detailPending = fetchJSON("or_detail.json").then(j => {''')

# ---------------- method cards
a = s.index('function methodCards() {'); b = s.index('// ---------------- boot ----------------')
s = s[:a] + r'''function methodCards() {
  const m = META, c = (m.calibration || {}).areas || {}, S0 = c["Oregon (statewide)"] || {};
  const dv = ["Foursquare only", "BrightQuery only", "Microsoft only"].map(k => S0.groups?.[k]).filter(Boolean).map(g => g.official);
  const dropRange = dv.length ? `${Math.round(Math.min(...dv) * 100)}–${Math.round(Math.max(...dv) * 100)}%` : "a small share";
  const mh = S0.groups?.["Meta + open in Google 2021"], mo = S0.groups?.["Meta only"];
  const cols = [
    ["m", "Official records", [
      ["Liquor licenses (statewide)", `The Oregon Liquor and Cannabis Commission's "Liquor Business Licenses & Endorsements" (data.oregon.gov, updated daily; read ${esc(m.licenses_updated || "")}): ${fmtN(m.olcc_active_onprem || 0)} active on-premises licenses, ${fmtN(m.olcc_active_full || 0)} of them Full On-Premises Commercial (bars and restaurants that serve spirits, which Oregon requires to offer food). A listing matched to an active license is confirmed; a licensed bar or restaurant the map listings lack is added (beer-and-wine and tasting-room licenses only when the trade name says it's a place to eat or drink). Expired licenses and ones with an inactive date are ignored. The licensee's name is never shown.`],
      ["Health inspections: none", "Oregon's 33 local health departments inspect and score restaurants on one shared HealthSpace portal (inspections.myhealthdepartment.com/oregon), but it's search-only and its robots.txt disallows all crawlers, and we found no bulk copy (Multnomah's old API is gone, OHA's statistics stop at 2021). So there's no inspection board and no grade of ours."],
      ["Brewpubs", "OLCC's Brewery Public House license marks a brewpub: one license tags one place, chosen by the license's trade name."],
      ["Property values (metro Portland)", `Oregon Metro's Regional Land Information System "Taxlots (Public)" (rlisdiscovery.oregonmetro.gov): the three counties' assessor market values, land plus buildings, for the tax lot under each place (${fmtN(m.rlis?.n || 0)} places). ${esc(m.rlis?.attribution || "")}`]]],
    ["s", "Map listings & 2021 snapshot", [
      ["Places statewide", `Overture Maps' open map listings (${esc(m.overture_release || "Oct 2026")} release, which merges Meta, Foursquare, chain store lists and other sources), food carts included. We keep listings from Meta and from chains' own store lists, and drop Foursquare, BrightQuery and Microsoft listings unless a license or our research confirms them: statewide only ${dropRange} of those matched an OLCC license, against ${mh ? Math.round(mh.official * 100) : "–"}% of Meta listings Google also had open in 2021. Anything Google already showed as closed in 2021 is dropped. Vancouver, Washington, is left out by the state line.`],
      ["Ratings, reviews & price level", "Google Maps ratings from the UCSD Google Local research dataset, frozen in September 2021. Each Google listing is matched to one place at most, on a shared distinctive name word nearby. Places that opened later aren't in it, and the rating boards leave them out rather than guess."],
      ["Honors & guides", "Oregon has no MICHELIN Guide. James Beard honors and the hand-checked Oregon guides (food carts and pods, coast seafood, marionberry pie, wine-country dining, doughnut shops, taquerías, the oldest places), each with a 2025–26 source, are added in the next pass."]]],
    ["e", "Estimated", [
      ["Sales & profit", `Chains use their published U.S. average sales per store (QSR 50, Technomic, company filings and franchise disclosures; ${m.model?.n_chains ?? "60+"} brands found here), scaled by how busy the location is. Independents start from a typical figure for their price level ($600K for $ up to $3.5M for $$$$) and scale with 2021 review volume relative to similar Oregon places, with an exponent of ${m.model?.b ?? 0.76} fit on published Chicago sales. Places without reviews get a rough placeholder. Profit = sales × a typical segment margin.`],
      ["Price, cuisine & food cost", "Missing price levels are filled in from the chain's or cuisine's usual Oregon level and marked est. Cuisine comes from the listing's category, the business name and Google categories, so a few will be off."]]],
  ];
  $("#srcgrid").innerHTML = cols.map(([t, h, cards]) => `<div class="srccol"><span class="tag ${t}">${h}</span>${cards.map(([h,p]) => `<div class="src"><h3>${h}</h3><p>${p}</p></div>`).join("")}</div>`).join("");
  const G = [["Meta + open in Google 2021","Meta listing, open in Google's 2021 data","kept · two sources"],["Meta only","Meta listing only","kept · listing only"],
    ["brand feed + Google 2021","Chain store list + Google 2021","kept · two sources"],["brand feed only","Chain store list only","kept · listing only"],
    ["Foursquare/BrightQuery/Microsoft + Google 2021","Foursquare / BrightQuery / Microsoft + Google 2021","dropped unless licensed"],["Foursquare only","Foursquare only","dropped unless licensed"],
    ["BrightQuery only","BrightQuery only","dropped unless licensed"],["Microsoft only","Microsoft only","dropped unless licensed"],["Google 2021 says closed","Google showed it closed in 2021","dropped"]];
  const cell = (j, k) => { const g = c[j]?.groups?.[k]; return g ? `${Math.round(g.official * 100)}% <span style="color:var(--muted)">of ${fmtN(g.n)}</span>` : "—"; };
  const pc = (m.calibration || {}).per_county || {};
  const ctyRows = Object.entries(pc).sort((a, b) => b[1].listings - a[1].listings);
  const PORT = c["Multnomah County (Portland)"] || {};
  $("#calib").innerHTML = S0.groups ? `<div class="src" style="display:grid;gap:10px"><h3>How the map listings were checked</h3>
    <p>Oregon has no statewide food-license list, so every map listing was checked against OLCC's active on-premises liquor licenses, county by county: same business name nearby, or the same street address with a distinctive name word in common. Many real restaurants serve no alcohol, so these rates are floors; what matters is how the kinds of listing compare. Coverage runs the other way too: the open map listings held ${Math.round((S0.coverage||0)*100)}% of the ${fmtN(S0.official_food || 0)} Full On-Premises bars and restaurants statewide and ${Math.round((PORT.coverage||0)*100)}% of Multnomah County's; the rest were added from the license list.</p>
    <div class="calib"><table><thead><tr><th scope="col">Kind of listing</th><th scope="col" class="r">Oregon</th><th scope="col" class="r">Multnomah</th><th scope="col">Here</th></tr></thead><tbody>
    ${G.map(([k, l, what]) => `<tr><td>${esc(l)}</td><td class="r num">${cell("Oregon (statewide)", k)}</td><td class="r num">${cell("Multnomah County (Portland)", k)}</td><td>${what}</td></tr>`).join("")}</tbody></table></div>
    <p class="note">Matched = holds an active OLCC on-premises license (Full, Limited, Brewery Public House or a maker's tasting room). A real place licensed under a different name counts as a miss. Hand-checked places are kept whatever their source.</p></div>
    <div class="src" style="display:grid;gap:10px"><h3>Coverage by county</h3>
    <p>Every county is on OLCC's statewide list; no county publishes inspection results in bulk (all 36 use the same search-only portal). “Full licenses found” is the share of each county's Full On-Premises bars and restaurants the open map listings already held (the rest were added).</p>
    <div class="calib" style="max-height:420px;overflow:auto"><table><thead><tr><th scope="col">County</th><th scope="col" class="r">Map listings</th><th scope="col" class="r">On-premises licenses</th><th scope="col" class="r">Full licenses</th><th scope="col" class="r">Full licenses found</th></tr></thead><tbody>
    ${ctyRows.map(([n, v]) => `<tr><td>${esc(n)}</td><td class="r num">${fmtN(v.listings)}</td><td class="r num">${fmtN(v.olcc_onprem || 0)}</td><td class="r num">${fmtN(v.olcc_full || 0)}</td><td class="r num">${v.full_found == null ? "—" : Math.round(v.full_found * 100) + "%"}</td></tr>`).join("")}</tbody></table></div></div>` : "";
}

''' + s[b:]

# ---------------- build
R('''  // Wisconsin signals: Bayes-shrink each place's average toward the statewide average for that dish (5 reviews' worth)
  for (const [key, n, r, out] of [["ff","ff_n","ff_r","ff"],["cc","cc_n","cc_r","cc"],["cs","cs_n","cs_r","cs"]]) {
    let sw = 0, sn = 0; for (const [i, nn, rr] of sp[key] || []) if (rr != null) { sw += nn * rr / 100; sn += nn; }
    const mu = sn ? sw / sn : 4.2;
    for (const [i, nn, rr] of sp[key] || []) { const o = rows[i]; if (!o) continue; o[n] = nn; o[r] = rr == null ? null : rr / 100; o[out] = rr == null ? null : (nn * rr / 100 + 5 * mu) / (nn + 5); }
  }
  for (const [i, nn] of sp.sc || []) if (rows[i]) rows[i].sc_n = nn;
  for (const [i, s, f] of sp.hon || []) if (rows[i]) { rows[i].s_icon = s / 10; rows[i].hon = f; }
  for (const [i, cl, g, ni, nr] of sp.insp || []) if (rows[i]) Object.assign(rows[i], {clean: cl, grade: g, n_insp: ni, n_reinsp: nr});''',
  '''  for (const [i, s, f, mi, gs] of sp.hon || []) if (rows[i]) { rows[i].s_icon = s / 10; rows[i].hon = f; rows[i].mi = mi; rows[i].gs = gs; }
  HAVE_TAGS = 0; for (let i = 0; i < C.tags.length; i++) HAVE_TAGS |= C.tags[i] || 0;
  TAGS = TAGS_ALL.filter(([, , b]) => HAVE_TAGS & b); TAG_PH = TAG_PH_ALL.filter(([, t]) => TAGS.some(([k]) => k === t));
  for (let i = B.length - 1; i >= 0; i--) if (B[i].tagbit && !(HAVE_TAGS & B[i].tagbit)) B.splice(i, 1);   // a guide shows once its research lands
  for (const [i, res, p, d, n, rr, cl, j] of sp.insp || []) if (rows[i]) Object.assign(rows[i], {in_r: res, in_p: p, in_d: d, in_n: n, in_rr: rr, in_cl: cl, in_j: j});''')
R('''    o.src = (m.srcs || [])[C.src[i]] || null;''', '''    o.src = (m.srcs || [])[C.src[i]] || null; o.liq = C.liq[i] || 0; o.hc = C.hc[i] || 0; o.county = C.county[i] == null ? null : m.counties[C.county[i]];
    o.alc_k = null; o.alc_n = 0; o.prop = C.prop_k[i] == null ? null : C.prop_k[i] * 1000; o.built = C.built[i] || null;''')
R('''    o._s = " " + normRaw([o.name, o.city, o.zip, o.cuisine, o.brand].join(" ")) + " " + norm(o.addr) + " ";''', '''    o._s = " " + normRaw([o.name, o.city, o.zip, o.cuisine, o.brand, o.county].join(" ")) + " " + norm(o.addr) + " ";''')
R('''  CITY_N = new Map();   // "st germain", "saint germain" and "St. Germain" are one town''', '''  CITY_N = new Map();   // "st helens", "saint helens" and "St. Helens" are one town''')
R('''             "fish", "fry", "custard", "curds", "cheese", "supper", "club", "brats", "tavern", "tap", "brewery", "kringle"]));''',
  '''             "cart", "carts", "pod", "brewpub", "chowder", "crab", "oysters", "marionberry", "pie", "doughnut", "donut", "taqueria", "tacos", "wine", "winery", "tavern", "tap", "brewery"]));''')
R('''  $("#h1").innerHTML = `<span class="count num">${fmtN(n)}</span> Wisconsin restaurants, ranked`;''', '''  $("#h1").innerHTML = `<span class="count num">${fmtN(n)}</span> Oregon restaurants, ranked`;''')
R('''  fetchJSON("wisconsin.json").then(j => {''', '''  fetchJSON("oregon.json").then(j => {''')
R('''  $("#tagchips").innerHTML = TAGS.map(([k, l]) => `<button class="chip" type="button" data-v="${k}" aria-pressed="false">${l}</button>`).join("");''',
  '''  $("#tagchips").innerHTML = TAGS.map(([k, l]) => `<button class="chip" type="button" data-v="${k}" aria-pressed="false">${l}</button>`).join("");
  $("#l-tags").hidden = $("#tagchips").hidden = !TAGS.length;   // no hand-checked guide yet: no empty filter''')
for word in ("Wisconsin", "Milwaukee", "Dane County", "custard", "WI Score", "wi_", "Colorado", "Denver", "Boulder", "green chile", "CO Score",
             "Michigan", "MI Score", "mi_", "Detroit", "MDARD", "MLCC", "coney", "pasty", "Great Lakes",
             "Texas", "TABC", "Austin", "El Paso", "Arlington", "TX Score", "tx_", "brisket", "Comptroller"):
    hits = [m.start() for m in re.finditer(re.escape(word), s)]
    if hits:
        print(f"note: {len(hits)} '{word}' left, e.g. {s[max(0, hits[0]-60):hits[0]+40]!r}")
open(os.path.join(ROOT, "site", "index.html"), "w").write(s)
print("wrote site/index.html", len(s) // 1024, "KB")
