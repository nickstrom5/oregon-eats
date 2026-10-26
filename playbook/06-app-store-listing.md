# App Store listing (ASO)

Written by `scripts/make-listing.py` from `site-numbers.json` (2026-10-24); re-run it after every data refresh, never hand-edit.
The machine copy is `app-store/listing.json` (read by `../scripts/asc_listing.py` once Nick creates the App Store Connect record and
adds `"com.oregoneats.ios": "or-eats"` to its FOLDERS). The URLs assume oregon.eatsranked.com is live; until Nick's CNAME
resolves, use https://nickstrom5.github.io/oregon-eats/.

## Name (30 max)
`Oregon Eats: Restaurants` (24)

## Subtitle (30 max)
`Food Carts, Brewpubs & Chowder` (30)

Together they index: oregon, eats, restaurants, food, carts, brewpubs, chowder. Home Screen name: Oregon Eats.

## Keywords (100 max)
`portland,bend,eugene,salem,doughnuts,newport,astoria,hood river,ashland,medford,corvallis,pdx,crab` (98)

- No word repeats the name or subtitle; no trademarks (no Voodoo, Pip's, Mo's, McMenamins, Deschutes), no "best", "top" or "#1".
- Towns are the biggest win; Beaverton, Hillsboro, Lincoln City, Cannon Beach and McMinnville didn't fit. Rotate them in after a month
  of App Store Connect search-term data. Apple's public search can't be used for this research (itunes.apple.com's robots.txt blocks Claude).

## Promotional text (170 max, editable any time without review)
`35 food carts and pods, 19 doughnut shops and 15 coast seafood houses, each checked by hand. Plus 266 brewpubs and 12,000+ Oregon restaurants near you.` (151)

## Description (2794 of 4,000)
```
Oregon's restaurants, from a Portland food cart pod to a bowl of chowder on the coast.

Oregon Eats is a free guide to eating in Oregon: 35 food carts and pods in Portland, Bend and Eugene, 15 coast seafood houses, 19 doughnut shops, plus wine country dining rooms and taquerías we checked by hand, and 266 brewpubs with a state Brewery Public House license. Behind them, 12,697 restaurants, cafés, bars and bakeries in 317 towns, from Portland, Salem and Eugene to Bend, Medford and the coast. 6,238 of them hold an active Oregon liquor license. No account, no ads.

OREGON GUIDES
• Food Carts & Pods: carts and the pods that gather them, in Portland, Bend, Eugene and Springfield.
• Brewpubs: places that hold an active Brewery Public House license from the Oregon Liquor and Cannabis Commission.
• Coast Seafood: Dungeness crab, clam chowder and oysters from Astoria to Port Orford.
• Doughnut Shops: from Portland's famous names to small-town bakeries.
• Wine Country and Taquerías: Willamette Valley dining rooms and taquerías.
• Award winners: 15 James Beard semifinalists, finalists and America's Classics.

FIND IT FAST
• Sort by distance, or browse the map by guide.
• Search by name, town, street or dish: "chowder newport", "doughnuts salem".
• Filter by town or cuisine, or hide chains.
• Save places, and find hand-checked places from iPhone search (Spotlight).

LIVE DETAILS FROM APPLE MAPS
Tap "Ratings, hours & photos" on any place to open Apple Maps' own place card, with current hours, photos, ratings and directions.

HOW THE LISTS ARE BUILT
Every guide place was checked by hand in October 2026: a dated 2025 or 2026 source names it (local news, an official tourism listing or the place's own site), or an older one does and the place holds an active Oregon liquor license in 2026. The rest come from Overture Maps open data, checked against the Oregon Liquor and Cannabis Commission's license list. Website links are checked too. Oregon publishes no restaurant inspection results in bulk, so the app shows none. Nothing is ranked by star ratings, and the app computes no grades.

PRIVATE BY DESIGN
No account, no tracking, no ads. Your location, if you share it, only sorts lists on your device. Saved places stay on your device.

Places open and close, and carts move, so check before you go. Spot a mistake? Email nick@eatsranked.com.

An independent app, not affiliated with any restaurant, chain or government agency (including the State of Oregon, the Oregon Liquor and Cannabis Commission and the Oregon Health Authority), or with the James Beard Foundation. James Beard Foundation and James Beard Award are trademarks of the James Beard Foundation. Place data from Overture Maps Foundation (CDLA Permissive 2.0) and others; sources and licenses are on the About tab.
```

## What's New (1.0)
`First release: food carts, brewpubs, coast seafood, doughnut shops and 12,000+ Oregon restaurants.`

## Screenshots
Framed by `scripts/appstore-screenshots.py`: `app-store/iphone/` (8, 1320x2868, the 6.9" slot) and `app-store/ipad/` (6, 2064x2752, the
13" slot). Upload one file at a time in file order and check the order after a reload. Oregon shows no inspection results, so no image
can show a failed one; no negative board appears.

## Category and age rating
Primary Food & Drink, secondary Travel. Age rating: alcohol references "Infrequent" (bars, brewpubs, taverns) → 13+; everything else
None/No. Pricing $0.00, available in the United States. Content rights: yes, third-party content, with the rights (open data, public
records, Apple's place card). Untick "Sign-in required".

## App Review
Reply and recording script: `13-app-review-reply.md`. Put the reply in App Review Information → Notes from the start.
